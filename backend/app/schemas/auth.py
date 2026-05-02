from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    stage_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("stage_name")
    @classmethod
    def stage_name_length(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Stage name must be at least 2 characters")
        if len(v) > 50:
            raise ValueError("Stage name must be under 50 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    escort_id: str
    stage_name: str
    subscription_tier: str
    verification_level: int
    profile_complete: bool


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
