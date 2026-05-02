import re
from slugify import slugify as _slugify


def make_slug(text: str) -> str:
    return _slugify(text, max_length=100, word_boundary=True)


def make_unique_slug(text: str, existing_slugs: set[str]) -> str:
    base = make_slug(text)
    slug = base
    counter = 1
    while slug in existing_slugs:
        slug = f"{base}-{counter}"
        counter += 1
    return slug
