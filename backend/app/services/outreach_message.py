"""
X DM message generator for companion outreach.

Generates a uniquely-worded message per prospect by combining:
- One of N opening lines (varied by what we noticed about her profile)
- One of M body templates (varied by offer terms)
- One of K closing lines

The goal: 200 messages, none of them look templated.
"""
import hashlib
import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class OutreachContext:
    stage_name: str
    area: Optional[str]
    specialty: Optional[str]
    note: Optional[str]
    code: str
    # Offer terms (pulled from PlatformConfig at message-generation time)
    duration_months: int
    percent_off: int
    tier_label: str  # e.g. "Premium"
    includes_blue_tick: bool
    lifetime_discount_percent: int
    limit: int
    signups_so_far: int


# Openings — varied so we don't pattern-match
# Some reference what we noticed; others are warm but generic
_OPENINGS_WITH_NOTE = [
    "Hey {name} — saw {note_lower} on your profile, really nice work.",
    "Hi {name}, came across your page — {note_lower}, loved the way it's put together.",
    "Hey {name}, {note_lower} caught my eye on your profile.",
    "Hi {name} — your profile stood out, especially {note_lower}.",
    "Hey {name}, been following your work — {note_lower} is great.",
]

_OPENINGS_WITH_AREA = [
    "Hi {name}, came across your profile — looks like you're working {area_phrase}.",
    "Hey {name}, you've got a great-looking profile {area_phrase}.",
    "Hi {name} — really like how you've put your profile together {area_phrase}.",
    "Hey {name}, browsing through London profiles and yours stood out {area_phrase}.",
]

_OPENINGS_WITH_SPECIALTY = [
    "Hi {name}, your profile caught my attention — clear that {specialty_phrase} is your thing.",
    "Hey {name}, love that you specialise in {specialty_phrase}. Stands out in a crowded space.",
    "Hi {name} — {specialty_phrase} is exactly what we'd love to feature.",
]

_OPENINGS_GENERIC = [
    "Hi {name} — quick one from the team behind a new London directory I'd love to invite you to.",
    "Hey {name}, hope you don't mind me reaching out — I'm building something I think you'd be interested in.",
    "Hi {name}, my apologies for the cold DM but I think this is genuinely worth two minutes of your time.",
    "Hey {name} — short message, I'll be brief.",
]

# Bodies — describe the offer + what makes Bluechips different
_BODIES = [
    (
        "I'm one of the founders of Bluechips London — a new directory for independent companions only. "
        "No agencies, no commission, real ID verification, transparent pricing. "
        "We're inviting the first {limit} companions in as Founding Members — {duration_months} months of {tier_label} free "
        "({free_value_str}), {blue_tick_phrase}, plus a permanent {lifetime_discount}% lifetime discount when the free period ends. "
        "Currently {signups_so_far}/{limit} spots taken."
    ),
    (
        "Quick context: I'm launching Bluechips London — independent-only directory, no agencies, manual Blue Tick verification done by our team (not an automated scan), and zero commission ever. "
        "You'd be one of our founding {limit} members: {duration_months} months free on the {tier_label} tier, {blue_tick_phrase}, then {lifetime_discount}% off for life. "
        "{signups_remaining} spots remaining."
    ),
    (
        "I'm working on Bluechips London — a London-focused directory built around real verification and zero commission. "
        "Trying to assemble the first {limit} companions as founding members. The offer: {duration_months} months of {tier_label} free, {blue_tick_phrase}, "
        "a permanent founding badge, and {lifetime_discount}% lifetime discount after the free period. "
        "Up to {signups_so_far} confirmed so far, out of {limit}."
    ),
    (
        "Long story short — we built Bluechips London to fix what's wrong with the existing directories (fake photos, predatory pricing, no support for the women using them). "
        "We're letting the first {limit} companions in completely free for {duration_months} months on the {tier_label} tier, {blue_tick_phrase}, with a {lifetime_discount}% lifetime discount thereafter. "
        "Genuinely no strings."
    ),
]

# Closings — call to action with personal code
_CLOSINGS = [
    "Here's your personal founding code: {code}. Use it at signup and the discount applies automatically. Let me know if you have any questions.",
    "If you want to take a look, your founding code is {code} — applies automatically at signup. Happy to answer anything.",
    "Personal code for you: {code} (just enter it when you register). Reply here if anything is unclear.",
    "Your founding code if interested: {code}. Sign up at bluechips.live/join and it applies automatically.",
    "I'd love to have you on board — your personal code is {code}, valid for signup. Reply with any questions, no pressure.",
]


def _seed_for_prospect(seed_str: str) -> random.Random:
    """Deterministic but unique random per prospect, so regenerating gives different combos each time."""
    h = hashlib.md5(seed_str.lower().encode("utf-8")).hexdigest()
    return random.Random(int(h, 16))


def _area_phrase(area: Optional[str]) -> str:
    if not area:
        return "in London"
    area = area.strip()
    if area.lower().startswith("in "):
        return area
    return f"in {area}"


def _specialty_phrase(specialty: Optional[str]) -> str:
    if not specialty:
        return "your specialty"
    return specialty.strip()


def _format_free_value(percent_off: int, duration_months: int, monthly_pence: int = 4999) -> str:
    """Show the £ value of the free period (helps the offer feel concrete)."""
    if percent_off >= 100:
        total = (monthly_pence * duration_months) / 100
        return f"£{total:.0f} value"
    return f"{percent_off}% off"


def _blue_tick_phrase(includes: bool) -> str:
    return "free Blue Tick verification included" if includes else "Blue Tick add-on available"


def _humanize(text: str) -> str:
    """Minor human-feel touches — collapse double spaces within paragraphs, preserve paragraph breaks."""
    paragraphs = text.split("\n\n")
    cleaned = [" ".join(p.split()) for p in paragraphs]
    return "\n\n".join(p for p in cleaned if p)


def generate_message(ctx: OutreachContext, monthly_pence: int = 4999, regenerate_token: int = 0) -> str:
    """
    Generate a personalised DM. Pass `regenerate_token` (e.g. iteration counter) to force a different
    variant from the same prospect handle on subsequent calls.
    """
    # Use the unique code + regen token as the seed — unique per prospect, varies on regen
    rng = _seed_for_prospect(f"{ctx.code}|{regenerate_token}")

    # Pick an opening — biased toward whatever personalisation we have
    note_clean = (ctx.note or "").strip()
    name = ctx.stage_name.strip().split()[0] if ctx.stage_name else "there"

    if note_clean and len(note_clean) > 6:
        opening_template = rng.choice(_OPENINGS_WITH_NOTE)
        opening = opening_template.format(name=name, note_lower=note_clean[0].lower() + note_clean[1:])
    elif ctx.specialty:
        opening_template = rng.choice(_OPENINGS_WITH_SPECIALTY)
        opening = opening_template.format(name=name, specialty_phrase=_specialty_phrase(ctx.specialty))
    elif ctx.area:
        opening_template = rng.choice(_OPENINGS_WITH_AREA)
        opening = opening_template.format(name=name, area_phrase=_area_phrase(ctx.area))
    else:
        opening_template = rng.choice(_OPENINGS_GENERIC)
        opening = opening_template.format(name=name)

    body_template = rng.choice(_BODIES)
    body = body_template.format(
        limit=ctx.limit,
        duration_months=ctx.duration_months,
        tier_label=ctx.tier_label,
        free_value_str=_format_free_value(ctx.percent_off, ctx.duration_months, monthly_pence),
        blue_tick_phrase=_blue_tick_phrase(ctx.includes_blue_tick),
        lifetime_discount=ctx.lifetime_discount_percent,
        signups_so_far=ctx.signups_so_far,
        signups_remaining=max(0, ctx.limit - ctx.signups_so_far),
    )

    closing_template = rng.choice(_CLOSINGS)
    closing = closing_template.format(code=ctx.code)

    msg = f"{opening}\n\n{body}\n\n{closing}"
    return _humanize(msg)
