import functools
import itertools
import math
import re
import threading
from datetime import date, datetime, timedelta

from srp.errors import (AccountLocked, AccountSuspended, DuplicateAccount, DuplicateReport, DuplicateReview,
                        InvalidCollegeEmail, InvalidCredentials, InvalidInput, InvalidReview, NotAuthorised, NotFound,
                        NotVerified)
from srp.models import (CATEGORY_FIELDS, NOTIFICATION_CATEGORIES, AuditEntry, Category, City, College, Notification,
                        Recommendation, Review, ReviewStatus, User)
from srp.security import hash_password, verify_password

MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15
DEFAULT_RADIUS_KM = 5
MIN_PASSWORD_LENGTH = 8
MAX_COMMENT_LENGTH = 1000
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SPAM_PATTERN = re.compile(r"(https?://|www\.)|(.)\2{9,}", re.IGNORECASE)
BLOCKED_WORDS = {"fuck", "shit", "bitch", "bastard", "asshole", "scam123"}


def normalise_email(email):
    return email.strip().lower()


def distance_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def locked(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapper


class UserTable(dict):
    def __init__(self):
        super().__init__()
        self.by_email = {}

    def __setitem__(self, key, user):
        super().__setitem__(key, user)
        self.by_email[user.email] = user


def _number(value, low, high, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
        raise InvalidInput(name)
    return float(value)


def _text(value, name, required=True, limit=200):
    if not isinstance(value, str):
        raise InvalidInput(name)
    value = value.strip()
    if (required and not value) or len(value) > limit:
        raise InvalidInput(name)
    return value


def _as_date(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise InvalidInput("event_date")


class Platform:
    def __init__(self, clock=datetime.now, store=None):
        self.clock = clock
        self.store = store
        self._lock = threading.RLock()
        self.cities = {}
        self.colleges = {}
        self.users = UserTable()
        self.recommendations = {}
        self.reviews = {}
        self._user_reviews = {}
        self.notification_log = []
        self.audit_log = []
        self._ids = itertools.count(1)
        if store is not None:
            self._restore(store.load())

    def _restore(self, data):
        tables = (("cities", self.cities, "city_id"), ("colleges", self.colleges, "college_id"),
                  ("users", self.users, "user_id"), ("recommendations", self.recommendations, "rec_id"),
                  ("reviews", self.reviews, "review_id"))
        highest = 0
        for key, table, id_field in tables:
            for item in data[key]:
                identifier = getattr(item, id_field)
                table[identifier] = item
                highest = max(highest, int(re.sub(r"\D", "", identifier) or 0))
        for review in self.reviews.values():
            self._user_reviews.setdefault(review.user_id, []).append(review)
        self.notification_log = data["notifications"]
        self.audit_log = data["audit"]
        self._ids = itertools.count(highest + 1)

    def _next(self, prefix):
        return f"{prefix}{next(self._ids):04d}"

    def _save(self, kind, item):
        if self.store is not None:
            getattr(self.store, "save_" + kind)(item)

    def _audit(self, actor_id, action, target="", detail=""):
        entry = AuditEntry(0, self.clock(), actor_id, action, target, detail)
        if self.store is not None:
            entry.entry_id = self.store.add_audit(entry)
        else:
            entry.entry_id = len(self.audit_log) + 1
        self.audit_log.append(entry)

    def _notify(self, user_id, category, message):
        user = self.users.get(user_id)
        if user is None or category in user.disabled_notifications:
            return None
        note = Notification(0, user_id, category, message, self.clock())
        if self.store is not None:
            note.notification_id = self.store.add_notification(note)
        else:
            note.notification_id = len(self.notification_log) + 1
        self.notification_log.append(note)
        return note

    def _user(self, user_id):
        user = self.users.get(user_id)
        if user is None:
            raise NotFound("user")
        return user

    def _admin(self, admin_id):
        user = self._user(admin_id)
        if user.role != "admin":
            raise NotAuthorised(admin_id)
        return user

    @locked
    def add_city(self, name, state):
        city = City(self._next("CT"), _text(name, "name"), _text(state, "state"))
        self.cities[city.city_id] = city
        self._save("city", city)
        return city

    @locked
    def add_college(self, name, domain, city_id, address=""):
        if city_id not in self.cities:
            raise NotFound("city")
        domain = _text(domain, "domain").lower().lstrip("@")
        if any(c.domain == domain for c in self.colleges.values()):
            raise InvalidInput("domain")
        college = College(self._next("CL"), _text(name, "name"), domain, city_id, _text(address, "address", False))
        self.colleges[college.college_id] = college
        self._save("college", college)
        return college

    @locked
    def add_recommendation(self, name, category, city_id, lat, lon, price_level=0, description="", address="",
                           details=None, event_date=None):
        if city_id not in self.cities:
            raise NotFound("city")
        try:
            category = Category(category)
        except ValueError:
            raise InvalidInput("category")
        if isinstance(price_level, bool) or price_level not in (0, 1, 2, 3):
            raise InvalidInput("price_level")
        details = details or {}
        if not isinstance(details, dict) or set(details) - set(CATEGORY_FIELDS[category]):
            raise InvalidInput("details")
        if category == Category.EVENT and event_date is None:
            raise InvalidInput("event_date")
        rec = Recommendation(
            self._next("RC"), _text(name, "name"), category, city_id, _number(lat, -90, 90, "lat"),
            _number(lon, -180, 180, "lon"), price_level, description=_text(description, "description", False, 500),
            address=_text(address, "address", False), details={k: _text(v, k, False) for k, v in details.items()},
            event_date=_as_date(event_date) if event_date is not None else None)
        self.recommendations[rec.rec_id] = rec
        self._save("recommendation", rec)
        return rec

    @locked
    def create_admin(self, name, email, password):
        user = User(self._next("AD"), name, normalise_email(email), hash_password(password), role="admin",
                    verified=True, created_at=self.clock())
        self.users[user.user_id] = user
        if self.store is not None:
            self.store.save_user(user)
        return user

    @locked
    def find_user(self, email):
        return self.users.by_email.get(normalise_email(email))

    @locked
    def register(self, name, email, password, college_id, phone=""):
        name = _text(name, "name", limit=100)
        email = normalise_email(_text(email, "email", limit=254))
        if not EMAIL_PATTERN.match(email):
            raise InvalidInput("email")
        if not isinstance(password, str):
            raise InvalidInput("password")
        if self.find_user(email):
            raise DuplicateAccount(email)
        college = self.colleges.get(college_id)
        if college is None:
            raise NotFound("college")
        domain = email.split("@")[-1]
        if domain != college.domain and not domain.endswith("." + college.domain):
            raise InvalidCollegeEmail(email)
        if len(password) < MIN_PASSWORD_LENGTH:
            raise InvalidInput("password")
        user = User(self._next("ST"), name, email, hash_password(password), college_id=college_id, verified=True,
                    phone=_text(phone, "phone", False, 20), created_at=self.clock())
        self.users[user.user_id] = user
        if self.store is not None:
            self.store.save_user(user)
        self._audit(user.user_id, "register", user.user_id, "college domain accepted; account marked verified")
        return user

    @locked
    def login(self, email, password):
        user = self.find_user(email) if isinstance(email, str) else None
        if user is None or not isinstance(password, str):
            self._audit("unknown", "login_failed", "", "no such account")
            raise InvalidCredentials(email)
        now = self.clock()
        if user.locked_until and now < user.locked_until:
            self._audit(user.user_id, "login_blocked", user.user_id, "account locked")
            raise AccountLocked(email)
        if user.locked_until and now >= user.locked_until:
            user.failed_attempts = 0
            user.locked_until = None
        if not verify_password(password, user.password_hash):
            user.failed_attempts += 1
            detail = f"attempt {user.failed_attempts}"
            if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=LOCK_MINUTES)
                detail += "; account locked for 15 minutes"
            self._audit(user.user_id, "login_failed", user.user_id, detail)
            self._persist_user(user)
            raise InvalidCredentials(email)
        if user.suspended:
            self._audit(user.user_id, "login_refused", user.user_id, "account suspended")
            raise AccountSuspended(email)
        user.failed_attempts = 0
        user.locked_until = None
        self._persist_user(user)
        return user

    def _persist_user(self, user):
        if self.store is not None:
            self.store.save_user(user)

    def _live(self, rec):
        return rec.active and not (rec.category == Category.EVENT and rec.event_date < self.clock().date())

    def _published_counts(self):
        counts = {}
        for review in self.reviews.values():
            if review.status == ReviewStatus.PUBLISHED:
                counts[review.rec_id] = counts.get(review.rec_id, 0) + 1
        return counts

    @locked
    def search(self, category, lat, lon, radius_km=DEFAULT_RADIUS_KM, max_price=None, min_rating=None, limit=None):
        try:
            category = Category(category)
        except ValueError:
            raise InvalidInput("category")
        _number(lat, -90, 90, "lat")
        _number(lon, -180, 180, "lon")
        _number(radius_km, 0.1, 100, "radius")
        found = []
        for rec in self.recommendations.values():
            if rec.category != category or not self._live(rec):
                continue
            d = distance_km(lat, lon, rec.lat, rec.lon)
            if d > radius_km:
                continue
            if max_price is not None and rec.price_level > max_price:
                continue
            if min_rating is not None and rec.average_rating < min_rating:
                continue
            found.append((d, rec))
        found.sort(key=lambda pair: pair[0])
        if limit is not None:
            found = found[:limit]
        counts = self._published_counts() if found else {}
        results = [{"rec": rec, "distance_km": round(d, 2), "review_count": counts.get(rec.rec_id, 0)}
                   for d, rec in found]
        message = "" if results else "No results nearby. Try expanding the search radius."
        return {"results": results, "message": message}

    @locked
    def list_events(self, city_id=None, event_type=None, date_from=None, date_to=None):
        start = _as_date(date_from) if date_from else self.clock().date()
        end = _as_date(date_to) if date_to else None
        events = []
        for rec in self.recommendations.values():
            if rec.category != Category.EVENT or not rec.active:
                continue
            if city_id and rec.city_id != city_id:
                continue
            if event_type and rec.details.get("event_type", "").lower() != event_type.lower():
                continue
            if rec.event_date < start or (end and rec.event_date > end):
                continue
            events.append(rec)
        return sorted(events, key=lambda r: (r.event_date, r.name))

    @locked
    def get_recommendation(self, rec_id):
        rec = self.recommendations.get(rec_id)
        if rec is None or not rec.active:
            raise NotFound("recommendation")
        return rec

    @locked
    def recommend(self, user_id, lat, lon, radius_km=DEFAULT_RADIUS_KM):
        user = self._user(user_id)
        scored = []
        for rec in self.recommendations.values():
            if not self._live(rec):
                continue
            d = distance_km(lat, lon, rec.lat, rec.lon)
            if d > radius_km:
                continue
            if user.preferences and rec.category.value not in user.preferences:
                continue
            scored.append((rec.average_rating - d * 0.2, rec))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [rec for _, rec in scored]

    @locked
    def set_preferences(self, user_id, categories):
        user = self._user(user_id)
        try:
            chosen = {Category(c).value for c in categories}
        except (ValueError, TypeError):
            raise InvalidInput("preferences")
        user.preferences = chosen
        self._persist_user(user)
        return user

    @locked
    def set_notification_settings(self, user_id, disabled):
        user = self._user(user_id)
        if not isinstance(disabled, (list, set, tuple)) or not set(disabled) <= set(NOTIFICATION_CATEGORIES):
            raise InvalidInput("disabled")
        user.disabled_notifications = set(disabled)
        self._persist_user(user)
        return user

    @locked
    def notifications(self, user_id):
        self._user(user_id)
        return sorted((n for n in self.notification_log if n.user_id == user_id),
                      key=lambda n: n.notification_id, reverse=True)

    @locked
    def mark_notification_read(self, user_id, notification_id):
        for note in self.notification_log:
            if note.notification_id == notification_id and note.user_id == user_id:
                note.read = True
                if self.store is not None:
                    self.store.mark_notification(notification_id)
                return note
        raise NotFound("notification")

    def _validate_comment(self, comment):
        if not isinstance(comment, str) or not comment.strip() or len(comment) > MAX_COMMENT_LENGTH:
            raise InvalidReview("comment is required and must be at most 1000 characters")
        words = set(re.findall(r"[a-z0-9]+", comment.lower()))
        if SPAM_PATTERN.search(comment) or words & BLOCKED_WORDS:
            raise InvalidReview("comment looks like spam or contains blocked language")

    @locked
    def submit_review(self, user_id, rec_id, rating, comment):
        user = self._user(user_id)
        if not user.verified:
            raise NotVerified(user_id)
        if user.suspended:
            raise AccountSuspended(user_id)
        rec = self.recommendations.get(rec_id)
        if rec is None or not rec.active:
            raise NotFound("recommendation")
        if isinstance(rating, bool) or not isinstance(rating, int) or rating < 1 or rating > 5:
            raise InvalidReview("rating must be between 1 and 5")
        self._validate_comment(comment)
        for existing in self._user_reviews.get(user_id, ()):
            if existing.rec_id == rec_id and existing.status != ReviewStatus.REJECTED:
                raise DuplicateReview(rec_id)
        review = Review(self._next("RV"), user_id, rec_id, rating, comment.strip(), submitted_at=self.clock())
        self.reviews[review.review_id] = review
        self._user_reviews.setdefault(user_id, []).append(review)
        self._save("review", review)
        self._audit(user_id, "review_submitted", review.review_id, rec_id)
        return review

    @locked
    def validate_review(self, admin_id, review_id, approve):
        admin = self._admin(admin_id)
        review = self.reviews.get(review_id)
        if review is None:
            raise NotFound("review")
        review.status = ReviewStatus.PUBLISHED if approve else ReviewStatus.REJECTED
        review.validated_at = self.clock()
        review.validated_by = admin.user_id
        self._save("review", review)
        self._refresh_rating(review.rec_id)
        outcome = "published" if approve else "rejected"
        place = self.recommendations[review.rec_id].name
        self._notify(review.user_id, "review", f"Your review of {place} was {outcome}.")
        for reporter in review.reports:
            kept = "kept after moderation" if approve else "removed after moderation"
            self._notify(reporter, "moderation", f"The review you reported on {place} was {kept}.")
        self._audit(admin_id, "review_" + outcome, review_id, place)
        return review

    def _refresh_rating(self, rec_id):
        published = [r.rating for r in self.reviews.values()
                     if r.rec_id == rec_id and r.status == ReviewStatus.PUBLISHED]
        rec = self.recommendations[rec_id]
        rec.average_rating = round(sum(published) / len(published), 1) if published else 0.0
        self._save("recommendation", rec)

    @locked
    def report_review(self, user_id, review_id, reason):
        self._user(user_id)
        review = self.reviews.get(review_id)
        if review is None:
            raise NotFound("review")
        if review.status == ReviewStatus.REJECTED:
            raise InvalidReview("review has already been removed")
        reason = _text(reason, "reason", limit=300)
        if user_id in review.reports:
            raise DuplicateReport(review_id)
        review.reports[user_id] = reason
        review.status = ReviewStatus.UNDER_REVIEW
        self._save("review", review)
        self._refresh_rating(review.rec_id)
        place = self.recommendations[review.rec_id].name
        for admin in [u for u in self.users.values() if u.role == "admin"]:
            self._notify(admin.user_id, "moderation", f"A review of {place} was reported: {reason}")
        self._audit(user_id, "review_reported", review_id, reason)
        return review

    @locked
    def published_reviews(self, rec_id):
        return [r for r in self.reviews.values()
                if r.rec_id == rec_id and r.status == ReviewStatus.PUBLISHED]

    @locked
    def moderation_queue(self, admin_id):
        self._admin(admin_id)
        waiting = [r for r in self.reviews.values()
                   if r.status in (ReviewStatus.PENDING, ReviewStatus.UNDER_REVIEW)]
        return sorted(waiting, key=lambda r: r.submitted_at)

    @locked
    def list_students(self, admin_id):
        self._admin(admin_id)
        return [u for u in self.users.values() if u.role == "student"]

    @locked
    def verify_student(self, admin_id, user_id):
        self._admin(admin_id)
        user = self._user(user_id)
        user.verified = True
        self._persist_user(user)
        self._notify(user_id, "account", "Your college verification was confirmed by an administrator.")
        self._audit(admin_id, "student_verified", user_id)
        return user

    @locked
    def suspend_user(self, admin_id, user_id):
        self._admin(admin_id)
        user = self._user(user_id)
        if user.role == "admin":
            raise InvalidInput("user")
        user.suspended = True
        self._persist_user(user)
        self._audit(admin_id, "user_suspended", user_id)

    @locked
    def reinstate_user(self, admin_id, user_id):
        self._admin(admin_id)
        user = self._user(user_id)
        user.suspended = False
        user.failed_attempts = 0
        user.locked_until = None
        self._persist_user(user)
        self._notify(user_id, "account", "Your account has been reinstated.")
        self._audit(admin_id, "user_reinstated", user_id)

    @locked
    def create_city(self, admin_id, name, state):
        self._admin(admin_id)
        city = self.add_city(name, state)
        self._audit(admin_id, "city_created", city.city_id, city.name)
        return city

    @locked
    def update_city(self, admin_id, city_id, name=None, state=None):
        self._admin(admin_id)
        city = self.cities.get(city_id)
        if city is None:
            raise NotFound("city")
        city.name = _text(name, "name") if name is not None else city.name
        city.state = _text(state, "state") if state is not None else city.state
        self._save("city", city)
        self._audit(admin_id, "city_updated", city_id)
        return city

    @locked
    def create_college(self, admin_id, name, domain, city_id, address=""):
        self._admin(admin_id)
        college = self.add_college(name, domain, city_id, address)
        self._audit(admin_id, "college_created", college.college_id, college.domain)
        return college

    @locked
    def update_college(self, admin_id, college_id, name=None, domain=None, address=None):
        self._admin(admin_id)
        college = self.colleges.get(college_id)
        if college is None:
            raise NotFound("college")
        if domain is not None:
            domain = _text(domain, "domain").lower().lstrip("@")
            if any(c.domain == domain and c.college_id != college_id for c in self.colleges.values()):
                raise InvalidInput("domain")
            college.domain = domain
        college.name = _text(name, "name") if name is not None else college.name
        college.address = _text(address, "address", False) if address is not None else college.address
        self._save("college", college)
        self._audit(admin_id, "college_updated", college_id)
        return college

    @locked
    def create_recommendation(self, admin_id, name, category, city_id, lat, lon, price_level=0, description="",
                              address="", details=None, event_date=None):
        self._admin(admin_id)
        rec = self.add_recommendation(name, category, city_id, lat, lon, price_level, description, address, details,
                                      event_date)
        self._audit(admin_id, "listing_created", rec.rec_id, rec.name)
        if rec.category == Category.EVENT:
            self._announce_event(rec)
        return rec

    def _announce_event(self, rec):
        for user in self.users.values():
            if user.role != "student" or user.suspended or not user.verified:
                continue
            college = self.colleges.get(user.college_id)
            if college is None or college.city_id != rec.city_id:
                continue
            if user.preferences and Category.EVENT.value not in user.preferences:
                continue
            self._notify(user.user_id, "event", f"New event: {rec.name} on {rec.event_date.isoformat()}.")

    @locked
    def update_recommendation(self, admin_id, rec_id, **fields):
        self._admin(admin_id)
        rec = self.recommendations.get(rec_id)
        if rec is None:
            raise NotFound("recommendation")
        allowed = {"name", "description", "address", "price_level", "lat", "lon", "details", "event_date"}
        if set(fields) - allowed:
            raise InvalidInput("fields")
        if "name" in fields:
            rec.name = _text(fields["name"], "name")
        if "description" in fields:
            rec.description = _text(fields["description"], "description", False, 500)
        if "address" in fields:
            rec.address = _text(fields["address"], "address", False)
        if "price_level" in fields:
            if isinstance(fields["price_level"], bool) or fields["price_level"] not in (0, 1, 2, 3):
                raise InvalidInput("price_level")
            rec.price_level = fields["price_level"]
        if "lat" in fields:
            rec.lat = _number(fields["lat"], -90, 90, "lat")
        if "lon" in fields:
            rec.lon = _number(fields["lon"], -180, 180, "lon")
        if "details" in fields:
            if not isinstance(fields["details"], dict) or set(fields["details"]) - set(CATEGORY_FIELDS[rec.category]):
                raise InvalidInput("details")
            rec.details = {k: _text(v, k, False) for k, v in fields["details"].items()}
        if "event_date" in fields:
            if rec.category != Category.EVENT:
                raise InvalidInput("event_date")
            rec.event_date = _as_date(fields["event_date"])
        self._save("recommendation", rec)
        self._audit(admin_id, "listing_updated", rec_id, ",".join(sorted(fields)))
        return rec

    @locked
    def delete_recommendation(self, admin_id, rec_id):
        self._admin(admin_id)
        rec = self.recommendations.get(rec_id)
        if rec is None:
            raise NotFound("recommendation")
        rec.active = False
        self._save("recommendation", rec)
        self._audit(admin_id, "listing_archived", rec_id, rec.name)

    @locked
    def audit_entries(self, admin_id, limit=100):
        self._admin(admin_id)
        return list(reversed(self.audit_log[-limit:]))
