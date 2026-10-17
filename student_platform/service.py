import hashlib
import itertools
import math
from datetime import datetime, timedelta

from errors import (AccountLocked, AccountSuspended, DuplicateAccount, DuplicateReport, InvalidCollegeEmail,
                    InvalidCredentials, InvalidReview, NotAuthorised, NotFound, NotVerified)
from models import (Category, City, College, Recommendation, Review, ReviewStatus, User)

MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15
DEFAULT_RADIUS_KM = 5


def normalise_email(email):
    return email.strip().lower()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def distance_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class Platform:
    def __init__(self, clock=datetime.now):
        self.clock = clock
        self.cities = {}
        self.colleges = {}
        self.users = {}
        self.recommendations = {}
        self.reviews = {}
        self._ids = itertools.count(1)

    def _next(self, prefix):
        return f"{prefix}{next(self._ids):04d}"

    def add_city(self, name, state):
        city = City(self._next("CT"), name, state)
        self.cities[city.city_id] = city
        return city

    def add_college(self, name, domain, city_id):
        if city_id not in self.cities:
            raise NotFound("city")
        college = College(self._next("CL"), name, domain, city_id)
        self.colleges[college.college_id] = college
        return college

    def add_recommendation(self, name, category, city_id, lat, lon, price_level=0, description=""):
        if city_id not in self.cities:
            raise NotFound("city")
        rec = Recommendation(self._next("RC"), name, Category(category), city_id, lat, lon, price_level,
                             description=description)
        self.recommendations[rec.rec_id] = rec
        return rec

    def create_admin(self, name, email, password):
        user = User(self._next("AD"), name, normalise_email(email), hash_password(password), role="admin",
                    verified=True)
        self.users[user.user_id] = user
        return user

    def find_user(self, email):
        email = normalise_email(email)
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    def register(self, name, email, password, college_id):
        if self.find_user(email):
            raise DuplicateAccount(email)
        college = self.colleges.get(college_id)
        if college is None:
            raise NotFound("college")
        email = normalise_email(email)
        domain = email.split("@")[-1]
        if domain != college.domain and not domain.endswith("." + college.domain):
            raise InvalidCollegeEmail(email)
        user = User(self._next("ST"), name, email, hash_password(password), college_id=college_id, verified=True)
        self.users[user.user_id] = user
        return user

    def login(self, email, password):
        user = self.find_user(email)
        if user is None:
            raise InvalidCredentials(email)
        now = self.clock()
        if user.locked_until and now < user.locked_until:
            raise AccountLocked(email)
        if user.password_hash != hash_password(password):
            user.failed_attempts += 1
            if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=LOCK_MINUTES)
            raise InvalidCredentials(email)
        if user.suspended:
            raise AccountSuspended(email)
        user.failed_attempts = 0
        user.locked_until = None
        return user

    def search(self, category, lat, lon, radius_km=DEFAULT_RADIUS_KM, max_price=None, min_rating=None):
        category = Category(category)
        found = []
        for rec in self.recommendations.values():
            if rec.category != category:
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
        results = [{"rec": rec, "distance_km": round(d, 2)} for d, rec in found]
        message = "" if results else "No results nearby. Try expanding the search radius."
        return {"results": results, "message": message}

    def recommend(self, user_id, lat, lon, radius_km=DEFAULT_RADIUS_KM):
        user = self._user(user_id)
        scored = []
        for rec in self.recommendations.values():
            d = distance_km(lat, lon, rec.lat, rec.lon)
            if d > radius_km:
                continue
            if user.preferences and rec.category.value not in user.preferences:
                continue
            scored.append((rec.average_rating - d * 0.2, rec))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [rec for _, rec in scored]

    def _user(self, user_id):
        user = self.users.get(user_id)
        if user is None:
            raise NotFound("user")
        return user

    def submit_review(self, user_id, rec_id, rating, comment):
        user = self._user(user_id)
        if not user.verified:
            raise NotVerified(user_id)
        if rec_id not in self.recommendations:
            raise NotFound("recommendation")
        if isinstance(rating, bool) or not isinstance(rating, int) or rating < 1 or rating > 5:
            raise InvalidReview("rating must be between 1 and 5")
        review = Review(self._next("RV"), user_id, rec_id, rating, comment)
        self.reviews[review.review_id] = review
        return review

    def validate_review(self, admin_id, review_id, approve):
        admin = self._user(admin_id)
        if admin.role != "admin":
            raise NotAuthorised(admin_id)
        review = self.reviews.get(review_id)
        if review is None:
            raise NotFound("review")
        review.status = ReviewStatus.PUBLISHED if approve else ReviewStatus.REJECTED
        review.validated_at = self.clock()
        self._refresh_rating(review.rec_id)
        return review

    def _refresh_rating(self, rec_id):
        published = [r.rating for r in self.reviews.values()
                     if r.rec_id == rec_id and r.status == ReviewStatus.PUBLISHED]
        rec = self.recommendations[rec_id]
        rec.average_rating = round(sum(published) / len(published), 1) if published else 0.0

    def report_review(self, user_id, review_id, reason):
        self._user(user_id)
        review = self.reviews.get(review_id)
        if review is None:
            raise NotFound("review")
        if user_id in review.reports:
            raise DuplicateReport(review_id)
        review.reports.add(user_id)
        review.status = ReviewStatus.UNDER_REVIEW
        return review

    def published_reviews(self, rec_id):
        return [r for r in self.reviews.values()
                if r.rec_id == rec_id and r.status == ReviewStatus.PUBLISHED]

    def suspend_user(self, admin_id, user_id):
        if self._user(admin_id).role != "admin":
            raise NotAuthorised(admin_id)
        self._user(user_id).suspended = True
