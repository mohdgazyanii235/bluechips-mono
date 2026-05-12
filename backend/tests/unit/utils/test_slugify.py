"""Unit tests for app.utils.slugify."""
from __future__ import annotations

import pytest

from app.utils.slugify import make_slug, make_unique_slug


class TestMakeSlug:
    @pytest.mark.parametrize("input_text,expected", [
        ("Sasha Petrova", "sasha-petrova"),
        ("Lily 22", "lily-22"),
        ("  Ella  ", "ella"),
        ("Élodie", "elodie"),
        ("Naïve Café", "naive-cafe"),
    ])
    def test_basic_normalisation(self, input_text, expected):
        assert make_slug(input_text) == expected

    def test_empty_string(self):
        assert make_slug("") == ""

    def test_long_name_truncates(self):
        long_name = "a" * 200
        slug = make_slug(long_name)
        assert len(slug) <= 100

    def test_special_chars_stripped(self):
        assert make_slug("!!!@@@###") == ""

    def test_numeric_only(self):
        assert make_slug("12345") == "12345"


class TestMakeUniqueSlug:
    def test_returns_base_when_unused(self):
        assert make_unique_slug("Sasha", set()) == "sasha"

    def test_appends_counter_on_collision(self):
        existing = {"sasha"}
        assert make_unique_slug("Sasha", existing) == "sasha-1"

    def test_skips_multiple_existing(self):
        existing = {"sasha", "sasha-1", "sasha-2"}
        assert make_unique_slug("Sasha", existing) == "sasha-3"

    def test_does_not_mutate_input_set(self):
        existing = {"sasha"}
        before = set(existing)
        make_unique_slug("Sasha", existing)
        assert existing == before
