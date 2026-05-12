import re
import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator
from typing import Optional

_PHONE_RE = re.compile(r'^\+?[\d\s\-().]{7,25}$')


class PhotoOut(BaseModel):
    id: uuid.UUID
    url: str
    thumbnail_url: Optional[str]
    is_primary: bool
    sort_order: int

    model_config = {"from_attributes": True}


class EscortCardOut(BaseModel):
    """Lightweight schema for grid/listing views."""
    id: uuid.UUID
    stage_name: str
    slug: str
    age: Optional[int]
    nationality: Optional[str]
    ethnicity: Optional[str]
    borough_name: Optional[str] = None
    borough_slug: Optional[str] = None
    availability_type: Optional[str]
    rate_1hour: Optional[int]
    subscription_tier: str
    verification_level: int
    blue_tick_active: bool = False
    is_founding_member: bool = False
    available_now: bool
    std_tested: bool
    primary_photo_url: Optional[str]
    service_tags: list[str] = []
    profile_type: str = "individual"

    model_config = {"from_attributes": True}


class EscortProfileOut(BaseModel):
    """Full profile schema for individual profile pages."""
    id: uuid.UUID
    stage_name: str
    slug: str
    age: Optional[int]
    nationality: Optional[str]
    ethnicity: Optional[str]
    height_cm: Optional[int]
    build: Optional[str]
    hair_colour: Optional[str]
    eye_colour: Optional[str]
    dress_size: Optional[str]
    chest: Optional[str]
    borough_name: Optional[str] = None
    borough_slug: Optional[str] = None
    availability_type: Optional[str]
    rate_30min: Optional[int]
    rate_1hour: Optional[int]
    rate_2hours: Optional[int]
    rate_overnight: Optional[int]
    about_me: Optional[str]
    languages: Optional[list[str]]
    booking_notice: Optional[str]
    std_tested: bool
    std_tested_date: Optional[str]
    subscription_tier: str
    verification_level: int
    blue_tick_active: bool = False
    is_founding_member: bool = False
    available_now: bool
    profile_views: int
    service_tags: list[str] = []
    photos: list[PhotoOut] = []
    created_at: datetime
    profile_type: str = "individual"
    whatsapp_number: Optional[str] = None
    phone_number: Optional[str] = None

    model_config = {"from_attributes": True}


class EscortUpdateRequest(BaseModel):
    stage_name: Optional[str] = None
    age: Optional[int] = None
    nationality: Optional[str] = None
    ethnicity: Optional[str] = None
    height_cm: Optional[int] = None
    build: Optional[str] = None
    hair_colour: Optional[str] = None
    eye_colour: Optional[str] = None
    dress_size: Optional[str] = None
    chest: Optional[str] = None
    borough_id: Optional[uuid.UUID] = None
    availability_type: Optional[str] = None
    rate_30min: Optional[int] = None
    rate_1hour: Optional[int] = None
    rate_2hours: Optional[int] = None
    rate_overnight: Optional[int] = None
    about_me: Optional[str] = None
    languages: Optional[list[str]] = None
    booking_notice: Optional[str] = None
    std_tested: Optional[bool] = None
    std_tested_date: Optional[str] = None
    service_tags: Optional[list[str]] = None
    available_now: Optional[bool] = None
    profile_type: Optional[str] = None
    whatsapp_number: Optional[str] = None
    phone_number: Optional[str] = None

    @field_validator("whatsapp_number", "phone_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and v.strip():
            v = v.strip()
            if not _PHONE_RE.match(v):
                raise ValueError("Phone number must be in international format, e.g. +44 7700 900000")
            if len(v) > 25:
                raise ValueError("Phone number too long")
        return v or None

    @field_validator("about_me")
    @classmethod
    def cap_about_me(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 600:
            return v[:600]
        return v

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 18 or v > 99):
            raise ValueError("Age must be between 18 and 99")
        return v


class EscortDashboardOut(BaseModel):
    """Full escort object returned to authenticated escort for dashboard."""
    id: uuid.UUID
    email: str
    stage_name: str
    slug: str
    age: Optional[int]
    nationality: Optional[str]
    ethnicity: Optional[str]
    height_cm: Optional[int]
    build: Optional[str]
    hair_colour: Optional[str]
    eye_colour: Optional[str]
    dress_size: Optional[str]
    chest: Optional[str]
    borough_id: Optional[uuid.UUID]
    borough_name: Optional[str] = None
    availability_type: Optional[str]
    rate_30min: Optional[int]
    rate_1hour: Optional[int]
    rate_2hours: Optional[int]
    rate_overnight: Optional[int]
    about_me: Optional[str]
    languages: Optional[list[str]]
    booking_notice: Optional[str]
    std_tested: bool
    std_tested_date: Optional[str]
    is_email_verified: bool
    verification_level: int
    profile_complete: bool
    available_now: bool
    subscription_tier: str
    subscription_expires_at: Optional[datetime]
    blue_tick_active: bool = False
    is_founding_member: bool = False
    blue_tick_stripe_subscription_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    profile_views: int
    contact_clicks: int
    service_tags: list[str] = []
    photos: list[PhotoOut] = []
    photo_limit: int
    created_at: datetime
    profile_type: str = "individual"
    whatsapp_number: Optional[str] = None
    phone_number: Optional[str] = None
    referral_code: Optional[str] = None

    model_config = {"from_attributes": True}


class EscortSearchParams(BaseModel):
    borough_slug: Optional[str] = None
    ethnicity: Optional[str] = None
    availability_type: Optional[str] = None
    profile_type: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    min_rate: Optional[int] = None
    max_rate: Optional[int] = None
    std_tested: Optional[bool] = None
    available_now: Optional[bool] = None
    blue_tick_only: Optional[bool] = None
    service_tag: Optional[str] = None
    page: int = 1
    per_page: int = 24
