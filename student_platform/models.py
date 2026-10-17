from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Category(str, Enum):
    PG_HOSTEL = "pg_hostel"
    RESTAURANT = "restaurant"
    STATIONERY = "stationery"
    SPORTS = "sports"
    EVENT = "event"


class ReviewStatus(str, Enum):
    PENDING = "Pending"
    UNDER_REVIEW = "Under Review"
    PUBLISHED = "Published"
    REJECTED = "Rejected"


@dataclass
class City:
    city_id: str
    name: str
    state: str


@dataclass
class College:
    college_id: str
    name: str
    domain: str
    city_id: str


@dataclass
class User:
    user_id: str
    name: str
    email: str
    password_hash: str
    role: str = "student"
    college_id: str = ""
    verified: bool = False
    suspended: bool = False
    failed_attempts: int = 0
    locked_until: datetime | None = None
    preferences: set = field(default_factory=set)


@dataclass
class Recommendation:
    rec_id: str
    name: str
    category: Category
    city_id: str
    lat: float
    lon: float
    price_level: int = 0
    average_rating: float = 0.0
    description: str = ""


@dataclass
class Review:
    review_id: str
    user_id: str
    rec_id: str
    rating: int
    comment: str
    status: ReviewStatus = ReviewStatus.PENDING
    reports: set = field(default_factory=set)
    submitted_at: datetime = field(default_factory=datetime.now)
    validated_at: datetime | None = None
