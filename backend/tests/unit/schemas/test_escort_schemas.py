"""Pydantic-v2 schema validation tests for app.schemas.escort and app.schemas.auth.

These run without any DB/HTTP setup — pure model-level validation. They catch
field-validator regressions (phone format, age range, password length) before
they reach a router.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest, LoginRequest, PasswordChangeRequest
from app.schemas.escort import EscortUpdateRequest


class TestRegisterRequest:
    @pytest.mark.parametrize("password", ["", "x", "1234567"])
    def test_short_password_rejected(self, password):
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", password=password, stage_name="Foo")

    def test_min_password_accepted(self):
        m = RegisterRequest(email="a@b.com", password="12345678", stage_name="Foo")
        assert m.password == "12345678"

    @pytest.mark.parametrize("name", ["", " ", "x", "  a  ", "x" * 51])
    def test_bad_stage_name_rejected(self, name):
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", password="Password123!", stage_name=name)

    def test_stage_name_stripped(self):
        m = RegisterRequest(email="a@b.com", password="Password123!", stage_name="  Lily  ")
        assert m.stage_name == "Lily"

    @pytest.mark.parametrize("bad_email", ["", "no-at", "@bad", "user@", "a b@c.com"])
    def test_invalid_email_rejected(self, bad_email):
        with pytest.raises(ValidationError):
            RegisterRequest(email=bad_email, password="Password123!", stage_name="Ok")


class TestLoginRequest:
    def test_basic(self):
        m = LoginRequest(email="a@b.com", password="anything")
        assert m.email == "a@b.com"

    def test_email_required(self):
        with pytest.raises(ValidationError):
            LoginRequest(password="x")  # type: ignore


class TestPasswordChangeRequest:
    def test_short_new_password_rejected(self):
        with pytest.raises(ValidationError):
            PasswordChangeRequest(current_password="OldPass1!", new_password="short")


class TestEscortUpdateRequest:
    @pytest.mark.parametrize("phone", ["+44 7700 900000", "+447700900000", "07700900000", "020 7946 0958"])
    def test_valid_phone(self, phone):
        m = EscortUpdateRequest(phone_number=phone)
        assert m.phone_number is not None

    @pytest.mark.parametrize("phone", ["abc", "<script>", "phone!", "!!!", "x" * 30])
    def test_invalid_phone(self, phone):
        with pytest.raises(ValidationError):
            EscortUpdateRequest(phone_number=phone)

    def test_empty_phone_normalises_to_none(self):
        m = EscortUpdateRequest(phone_number="")
        assert m.phone_number is None

    @pytest.mark.parametrize("age", [17, 0, -1, 100, 200])
    def test_invalid_age(self, age):
        with pytest.raises(ValidationError):
            EscortUpdateRequest(age=age)

    @pytest.mark.parametrize("age", [18, 30, 99])
    def test_valid_age(self, age):
        m = EscortUpdateRequest(age=age)
        assert m.age == age

    def test_about_me_capped_at_600(self):
        long_text = "x" * 1000
        m = EscortUpdateRequest(about_me=long_text)
        assert len(m.about_me) == 600

    def test_about_me_under_limit_unchanged(self):
        m = EscortUpdateRequest(about_me="short")
        assert m.about_me == "short"
