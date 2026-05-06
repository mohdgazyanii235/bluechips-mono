"""
Seed script — runs on first boot via docker-compose.
All functions are idempotent.
"""
import asyncio
import random
from datetime import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.borough import Borough
from app.models.admin import Admin
from app.models.escort import Escort, EscortService
from app.utils.security import hash_password
from app.utils.slugify import make_unique_slug
from app.config import settings


BOROUGHS = [
    {"name": "Mayfair", "slug": "mayfair", "is_premium_area": True, "sort_order": 1,
     "seo_title": "Escorts in Mayfair, London | Bluechips London",
     "seo_description": "Browse verified companion listings in Mayfair, London's most exclusive district.",
     "description": "Mayfair is London's most prestigious neighbourhood, home to five-star hotels, Michelin-starred restaurants, and the city's most discerning clientele."},
    {"name": "Kensington", "slug": "kensington", "is_premium_area": True, "sort_order": 2,
     "seo_title": "Escorts in Kensington, London | Bluechips London",
     "seo_description": "Find verified companion listings in Kensington. Elegant, discreet independent escorts.",
     "description": "Kensington blends royal heritage with contemporary luxury. Escorts listed here serve clients across Kensington's grand townhouses and boutique hotels."},
    {"name": "Chelsea", "slug": "chelsea", "is_premium_area": True, "sort_order": 3,
     "seo_title": "Escorts in Chelsea, London | Bluechips London",
     "seo_description": "Discover companion listings in Chelsea, SW3. Independent escorts available for incall and outcall.",
     "description": "Chelsea's blend of artistic heritage and modern affluence makes it one of London's most sought-after areas."},
    {"name": "Knightsbridge", "slug": "knightsbridge", "is_premium_area": True, "sort_order": 4,
     "seo_title": "Escorts in Knightsbridge, London | Bluechips London",
     "seo_description": "Elite companion listings in Knightsbridge, home to Harrods and London's finest hotels.",
     "description": "Steps from Harrods and Hyde Park, Knightsbridge is synonymous with luxury."},
    {"name": "Belgravia", "slug": "belgravia", "is_premium_area": True, "sort_order": 5,
     "seo_title": "Escorts in Belgravia, London | Bluechips London",
     "seo_description": "Premium companion directory for Belgravia, London SW1. Verified, discreet escorts.",
     "description": "One of London's most exclusive postcodes, Belgravia's white stucco townhouses set the scene for the city's most refined companionship."},
    {"name": "Soho", "slug": "soho", "is_premium_area": True, "sort_order": 6,
     "seo_title": "Escorts in Soho, London | Bluechips London",
     "seo_description": "Find companion listings in Soho, central London. Vibrant, diverse independent escorts in W1.",
     "description": "Soho's energy and cosmopolitan spirit attract a diverse and open-minded crowd."},
    {"name": "Marylebone", "slug": "marylebone", "is_premium_area": True, "sort_order": 7,
     "seo_title": "Escorts in Marylebone, London | Bluechips London",
     "seo_description": "Companion listings in Marylebone, W1. Elegant independent escorts near Regent's Park.",
     "description": "Marylebone's village atmosphere and elegant Georgian streets house some of London's most sophisticated companions."},
    {"name": "Westminster", "slug": "westminster", "is_premium_area": False, "sort_order": 8,
     "seo_title": "Escorts in Westminster, London | Bluechips London",
     "seo_description": "Companion directory for Westminster, central London.",
     "description": "Westminster's central location makes it one of London's most convenient areas for both incall and outcall companion services."},
    {"name": "Paddington", "slug": "paddington", "is_premium_area": False, "sort_order": 9,
     "seo_title": "Escorts in Paddington, London | Bluechips London",
     "seo_description": "Find companions in Paddington, W2. Independent escort listings close to Hyde Park.",
     "description": "Paddington's proximity to Hyde Park and excellent transport links make it popular with escorts offering incall services."},
    {"name": "Canary Wharf", "slug": "canary-wharf", "is_premium_area": True, "sort_order": 10,
     "seo_title": "Escorts in Canary Wharf, London | Bluechips London",
     "seo_description": "Companion listings in Canary Wharf and Docklands. Discreet escorts for London's business district.",
     "description": "Canary Wharf's gleaming towers house London's financial elite. Companions here cater to busy professionals."},
    {"name": "Notting Hill", "slug": "notting-hill", "is_premium_area": True, "sort_order": 11,
     "seo_title": "Escorts in Notting Hill, London | Bluechips London",
     "seo_description": "Independent companion listings in Notting Hill, W11. Verified profiles, discreet service.",
     "description": "Notting Hill's pastel townhouses and lively culture attract creative, cosmopolitan companions."},
    {"name": "Shoreditch", "slug": "shoreditch", "is_premium_area": False, "sort_order": 12,
     "seo_title": "Escorts in Shoreditch, London | Bluechips London",
     "seo_description": "Companion directory for Shoreditch and East London.",
     "description": "Shoreditch's creative energy and diverse scene attract bold, contemporary companions."},
    {"name": "Islington", "slug": "islington", "is_premium_area": False, "sort_order": 13,
     "seo_title": "Escorts in Islington, London | Bluechips London",
     "seo_description": "Companion listings in Islington, N1. Independent escorts in North London.",
     "description": "Islington's independent spirit and upmarket village feel make it home to some of North London's most sought-after companions."},
    {"name": "Camden", "slug": "camden", "is_premium_area": False, "sort_order": 14,
     "seo_title": "Escorts in Camden, London | Bluechips London",
     "seo_description": "Find companion listings in Camden, NW1. Eclectic, independent escorts.",
     "description": "Camden's eclectic character attracts a wide range of companions suited to clients who appreciate personality and individuality."},
    {"name": "Fulham", "slug": "fulham", "is_premium_area": False, "sort_order": 15,
     "seo_title": "Escorts in Fulham, London | Bluechips London",
     "seo_description": "Companion listings in Fulham, SW6. Independent escorts in West London.",
     "description": "Fulham's leafy streets and affluent residential character make it popular with companions catering to local professionals."},
    {"name": "Hammersmith", "slug": "hammersmith", "is_premium_area": False, "sort_order": 16,
     "seo_title": "Escorts in Hammersmith, London | Bluechips London",
     "seo_description": "Companion directory for Hammersmith, W6.",
     "description": "Hammersmith's central West London location provides easy access across the city."},
    {"name": "Hackney", "slug": "hackney", "is_premium_area": False, "sort_order": 17,
     "seo_title": "Escorts in Hackney, London | Bluechips London",
     "seo_description": "Find companion listings in Hackney, East London.",
     "description": "Hackney's cultural diversity and creative scene are reflected in the vibrant, international range of companions."},
    {"name": "Greenwich", "slug": "greenwich", "is_premium_area": False, "sort_order": 18,
     "seo_title": "Escorts in Greenwich, London | Bluechips London",
     "seo_description": "Companion listings in Greenwich, SE10.",
     "description": "Greenwich's historic charm and riverside setting provide a beautiful backdrop for companions serving South-East London."},
    {"name": "Brixton", "slug": "brixton", "is_premium_area": False, "sort_order": 19,
     "seo_title": "Escorts in Brixton, London | Bluechips London",
     "seo_description": "Companion directory for Brixton, SW9.",
     "description": "Brixton's vibrant energy and cultural richness attract a diverse community of companions."},
    {"name": "Clapham", "slug": "clapham", "is_premium_area": False, "sort_order": 20,
     "seo_title": "Escorts in Clapham, London | Bluechips London",
     "seo_description": "Companion listings in Clapham, SW4.",
     "description": "Clapham's young, professional population and lively social scene create strong demand for companion services."},
    {"name": "Battersea", "slug": "battersea", "is_premium_area": False, "sort_order": 21,
     "seo_title": "Escorts in Battersea, London | Bluechips London",
     "seo_description": "Find companion listings in Battersea, SW11.",
     "description": "Battersea's regeneration and growing luxury residential developments have brought a new, affluent clientele."},
    {"name": "Richmond", "slug": "richmond", "is_premium_area": False, "sort_order": 22,
     "seo_title": "Escorts in Richmond, London | Bluechips London",
     "seo_description": "Companion listings in Richmond, Surrey.",
     "description": "Richmond's riverside beauty and wealthy residential character attract companions catering to a privacy-conscious clientele."},
    {"name": "Wimbledon", "slug": "wimbledon", "is_premium_area": False, "sort_order": 23,
     "seo_title": "Escorts in Wimbledon, London | Bluechips London",
     "seo_description": "Companion directory for Wimbledon, SW19.",
     "description": "Wimbledon's prestigious address and well-heeled residents create steady demand for high-quality, discreet companionship."},
    {"name": "Stratford", "slug": "stratford", "is_premium_area": False, "sort_order": 24,
     "seo_title": "Escorts in Stratford, London | Bluechips London",
     "seo_description": "Find companion listings in Stratford, E15.",
     "description": "Stratford's regeneration and excellent transport links to central London attract companions throughout East London."},
    {"name": "Wembley", "slug": "wembley", "is_premium_area": False, "sort_order": 25,
     "seo_title": "Escorts in Wembley, London | Bluechips London",
     "seo_description": "Companion listings in Wembley, North-West London.",
     "description": "Wembley's diverse community and central North-West London location make it home to a wide range of companions."},
    {"name": "Covent Garden", "slug": "covent-garden", "is_premium_area": True, "sort_order": 26,
     "seo_title": "Escorts in Covent Garden, London | Bluechips London",
     "seo_description": "Companion listings in Covent Garden, WC2. Premium escorts in central London.",
     "description": "Covent Garden's theatre district, fine dining, and luxury hotels make it a hub for companions catering to sociable clientele."},
    {"name": "South Kensington", "slug": "south-kensington", "is_premium_area": True, "sort_order": 27,
     "seo_title": "Escorts in South Kensington, London | Bluechips London",
     "seo_description": "Companion directory for South Kensington, SW7. Elite independent escorts.",
     "description": "South Kensington's French community, world-class museums, and beautiful garden squares attract cultured, multilingual companions."},
    {"name": "Earl's Court", "slug": "earls-court", "is_premium_area": False, "sort_order": 28,
     "seo_title": "Escorts in Earl's Court, London | Bluechips London",
     "seo_description": "Companion listings in Earl's Court, SW5.",
     "description": "Earl's Court's international character and excellent transport links make it a convenient base for companions serving West London."},
    {"name": "Shepherd's Bush", "slug": "shepherds-bush", "is_premium_area": False, "sort_order": 29,
     "seo_title": "Escorts in Shepherd's Bush, London | Bluechips London",
     "seo_description": "Find companion listings in Shepherd's Bush, W12.",
     "description": "Shepherd's Bush's diverse and cosmopolitan community is reflected in the range of companions available."},
    {"name": "Croydon", "slug": "croydon", "is_premium_area": False, "sort_order": 30,
     "seo_title": "Escorts in Croydon, London | Bluechips London",
     "seo_description": "Companion listings in Croydon, South London.",
     "description": "Croydon's status as South London's commercial centre makes it accessible for companions serving the southern suburbs."},
    {"name": "Ilford", "slug": "ilford", "is_premium_area": False, "sort_order": 31,
     "seo_title": "Escorts in Ilford, East London | Bluechips London",
     "seo_description": "Find companion listings in Ilford, IG1.",
     "description": "Ilford's diverse community and excellent links into central London make it practical for companion services in East London."},
    {"name": "Romford", "slug": "romford", "is_premium_area": False, "sort_order": 32,
     "seo_title": "Escorts in Romford, London | Bluechips London",
     "seo_description": "Companion listings in Romford, RM1.",
     "description": "Romford's busy town centre and strong residential community create consistent demand for companion services."},
    # Additional London areas
    {"name": "Putney", "slug": "putney", "is_premium_area": False, "sort_order": 33,
     "seo_title": "Escorts in Putney, London | Bluechips London",
     "seo_description": "Companion listings in Putney, SW15. Independent escorts in South-West London.",
     "description": "Putney's riverside location and affluent residential streets attract companions catering to a well-heeled local and visiting clientele."},
    {"name": "Chiswick", "slug": "chiswick", "is_premium_area": False, "sort_order": 34,
     "seo_title": "Escorts in Chiswick, London | Bluechips London",
     "seo_description": "Companion listings in Chiswick, W4. Independent escorts in West London.",
     "description": "Chiswick's village feel and affluent character make it a sought-after location for companions serving West London."},
    {"name": "Wandsworth", "slug": "wandsworth", "is_premium_area": False, "sort_order": 35,
     "seo_title": "Escorts in Wandsworth, London | Bluechips London",
     "seo_description": "Companion listings in Wandsworth, SW18.",
     "description": "Wandsworth's growing affluence and strong residential community provide consistent demand for companion services."},
    {"name": "Lewisham", "slug": "lewisham", "is_premium_area": False, "sort_order": 36,
     "seo_title": "Escorts in Lewisham, London | Bluechips London",
     "seo_description": "Companion listings in Lewisham, South-East London.",
     "description": "Lewisham's vibrant community and transport links make it a practical hub for companions in South-East London."},
    {"name": "Vauxhall", "slug": "vauxhall", "is_premium_area": False, "sort_order": 37,
     "seo_title": "Escorts in Vauxhall, London | Bluechips London",
     "seo_description": "Companion listings in Vauxhall, SW8.",
     "description": "Vauxhall's proximity to central London and vibrant nightlife scene attract companions across many tastes."},
    {"name": "Victoria", "slug": "victoria", "is_premium_area": True, "sort_order": 38,
     "seo_title": "Escorts in Victoria, London | Bluechips London",
     "seo_description": "Companion listings in Victoria, SW1. Independent escorts near Buckingham Palace.",
     "description": "Victoria's central location and luxury hotels make it ideal for companions serving international and business clientele."},
    {"name": "King's Cross", "slug": "kings-cross", "is_premium_area": False, "sort_order": 39,
     "seo_title": "Escorts in King's Cross, London | Bluechips London",
     "seo_description": "Companion listings in King's Cross, N1C.",
     "description": "King's Cross has undergone dramatic transformation into one of London's most vibrant, well-connected districts."},
    {"name": "Fitzrovia", "slug": "fitzrovia", "is_premium_area": True, "sort_order": 40,
     "seo_title": "Escorts in Fitzrovia, London | Bluechips London",
     "seo_description": "Companion listings in Fitzrovia, W1T. Independent escorts in central London.",
     "description": "Fitzrovia's media and creative industries, boutique hotels, and fine restaurants attract sophisticated companions."},
    {"name": "Bloomsbury", "slug": "bloomsbury", "is_premium_area": False, "sort_order": 41,
     "seo_title": "Escorts in Bloomsbury, London | Bluechips London",
     "seo_description": "Companion listings in Bloomsbury, WC1.",
     "description": "Bloomsbury's literary heritage and central location attract cultured, well-read companions."},
    {"name": "Holborn", "slug": "holborn", "is_premium_area": False, "sort_order": 42,
     "seo_title": "Escorts in Holborn, London | Bluechips London",
     "seo_description": "Companion listings in Holborn, WC2.",
     "description": "Holborn's legal and financial districts create strong demand for discreet companion services during the working week."},
    {"name": "Dalston", "slug": "dalston", "is_premium_area": False, "sort_order": 43,
     "seo_title": "Escorts in Dalston, London | Bluechips London",
     "seo_description": "Companion listings in Dalston, E8. Independent escorts in East London.",
     "description": "Dalston's creative scene and thriving nightlife make it a hub for contemporary companions serving East London."},
    {"name": "Bethnal Green", "slug": "bethnal-green", "is_premium_area": False, "sort_order": 44,
     "seo_title": "Escorts in Bethnal Green, London | Bluechips London",
     "seo_description": "Companion listings in Bethnal Green, E2.",
     "description": "Bethnal Green's eclectic mix of artists, professionals, and international residents creates diverse demand."},
    {"name": "Whitechapel", "slug": "whitechapel", "is_premium_area": False, "sort_order": 45,
     "seo_title": "Escorts in Whitechapel, London | Bluechips London",
     "seo_description": "Companion listings in Whitechapel, E1.",
     "description": "Whitechapel's diverse community and proximity to the City make it a practical base for companions in East London."},
    {"name": "Tooting", "slug": "tooting", "is_premium_area": False, "sort_order": 46,
     "seo_title": "Escorts in Tooting, London | Bluechips London",
     "seo_description": "Companion listings in Tooting, SW17.",
     "description": "Tooting's multicultural character and growing popularity attract a wide range of companions in South London."},
    {"name": "Balham", "slug": "balham", "is_premium_area": False, "sort_order": 47,
     "seo_title": "Escorts in Balham, London | Bluechips London",
     "seo_description": "Companion listings in Balham, SW12.",
     "description": "Balham's professional demographic and leafy streets attract companions catering to a discerning South London clientele."},
    {"name": "Ealing", "slug": "ealing", "is_premium_area": False, "sort_order": 48,
     "seo_title": "Escorts in Ealing, London | Bluechips London",
     "seo_description": "Companion listings in Ealing, W5.",
     "description": "Ealing's leafy suburbs and strong professional community create consistent demand for companion services in West London."},
    {"name": "Acton", "slug": "acton", "is_premium_area": False, "sort_order": 49,
     "seo_title": "Escorts in Acton, London | Bluechips London",
     "seo_description": "Companion listings in Acton, W3.",
     "description": "Acton's convenient transport links and diverse community make it a practical base for West London companions."},
    {"name": "Twickenham", "slug": "twickenham", "is_premium_area": False, "sort_order": 50,
     "seo_title": "Escorts in Twickenham, London | Bluechips London",
     "seo_description": "Companion listings in Twickenham, TW1.",
     "description": "Twickenham's affluent riverside setting attracts companions serving a professional and international clientele."},
    {"name": "Kingston", "slug": "kingston", "is_premium_area": False, "sort_order": 51,
     "seo_title": "Escorts in Kingston upon Thames, London | Bluechips London",
     "seo_description": "Companion listings in Kingston upon Thames.",
     "description": "Kingston's vibrant town centre and wealthy suburbs provide strong demand for companion services in South-West London."},
    {"name": "Sutton", "slug": "sutton", "is_premium_area": False, "sort_order": 52,
     "seo_title": "Escorts in Sutton, London | Bluechips London",
     "seo_description": "Companion listings in Sutton, South London.",
     "description": "Sutton's suburban setting and strong local community create steady demand for discreet companion services."},
    {"name": "Bromley", "slug": "bromley", "is_premium_area": False, "sort_order": 53,
     "seo_title": "Escorts in Bromley, London | Bluechips London",
     "seo_description": "Companion listings in Bromley, South-East London.",
     "description": "Bromley's affluent suburbs and excellent transport into central London make it popular with companions and clients alike."},
    {"name": "Enfield", "slug": "enfield", "is_premium_area": False, "sort_order": 54,
     "seo_title": "Escorts in Enfield, London | Bluechips London",
     "seo_description": "Companion listings in Enfield, North London.",
     "description": "Enfield's large residential population and northern location provide consistent demand for companion services."},
    {"name": "Tottenham", "slug": "tottenham", "is_premium_area": False, "sort_order": 55,
     "seo_title": "Escorts in Tottenham, London | Bluechips London",
     "seo_description": "Companion listings in Tottenham, N17.",
     "description": "Tottenham's diverse community and central North London location attract companions serving a wide range of clientele."},
    {"name": "Wood Green", "slug": "wood-green", "is_premium_area": False, "sort_order": 56,
     "seo_title": "Escorts in Wood Green, London | Bluechips London",
     "seo_description": "Companion listings in Wood Green, N22.",
     "description": "Wood Green's transport links and diverse population make it a practical base for companions in North London."},
    {"name": "Finchley", "slug": "finchley", "is_premium_area": False, "sort_order": 57,
     "seo_title": "Escorts in Finchley, London | Bluechips London",
     "seo_description": "Companion listings in Finchley, North London.",
     "description": "Finchley's affluent neighbourhoods and strong residential character attract companions serving North London professionals."},
    {"name": "Harrow", "slug": "harrow", "is_premium_area": False, "sort_order": 58,
     "seo_title": "Escorts in Harrow, London | Bluechips London",
     "seo_description": "Companion listings in Harrow, North-West London.",
     "description": "Harrow's large and diverse community creates consistent demand for companion services in North-West London."},
    {"name": "Barking", "slug": "barking", "is_premium_area": False, "sort_order": 59,
     "seo_title": "Escorts in Barking, London | Bluechips London",
     "seo_description": "Companion listings in Barking, East London.",
     "description": "Barking's growing population and transport links into central London support a strong companion services community."},
    {"name": "Crystal Palace", "slug": "crystal-palace", "is_premium_area": False, "sort_order": 60,
     "seo_title": "Escorts in Crystal Palace, London | Bluechips London",
     "seo_description": "Companion listings in Crystal Palace, SE19.",
     "description": "Crystal Palace's artistic community and high vantage point above London attract creative and confident companions."},
]


async def seed_boroughs():
    """Idempotently insert any missing boroughs (checks by slug)."""
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Borough.slug))
        existing_slugs = {row[0] for row in existing.fetchall()}

        to_add = [b for b in BOROUGHS if b["slug"] not in existing_slugs]
        if not to_add:
            print("[SEED] All boroughs already present, skipping.")
            return

        for data in to_add:
            borough = Borough(
                name=data["name"],
                slug=data["slug"],
                description=data.get("description"),
                seo_title=data.get("seo_title"),
                seo_description=data.get("seo_description"),
                is_premium_area=data.get("is_premium_area", False),
                sort_order=data.get("sort_order", 99),
                created_at=datetime.utcnow(),
            )
            db.add(borough)

        await db.commit()
        print(f"[SEED] Added {len(to_add)} new London borough(s).")


async def seed_admin():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Admin).where(Admin.email == settings.ADMIN_EMAIL))
        if result.scalar_one_or_none():
            return
        admin = Admin(
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_INITIAL_PASSWORD),
        )
        db.add(admin)
        await db.commit()
        print(f"[SEED] Admin account created: {settings.ADMIN_EMAIL}")
        print(f"[SEED] Default password: {settings.ADMIN_INITIAL_PASSWORD} — change this in production!")


# ---------------------------------------------------------------------------
# Demo escort data
# ---------------------------------------------------------------------------

_DEMO_PASSWORD = hash_password("Demo1234!")

_NAMES = [
    # Free tier (25)
    "Amber", "Crystal", "Diamond", "Ruby", "Pearl",
    "Jade", "Jasmine", "Luna", "Stella", "Aurora",
    "Lily", "Rose", "Scarlett", "Maya", "Zara",
    "Mia", "Ava", "Gigi", "Nina", "Talia",
    "Leila", "Nadia", "Kira", "Sasha", "Vera",
    # Essential tier (30)
    "Sophia", "Valentina", "Melanie", "Lara", "Lana",
    "Chloe", "Daniela", "Isabella", "Natasha", "Anastasia",
    "Victoria", "Alexandra", "Monica", "Juliette", "Camille",
    "Elise", "Katerina", "Svetlana", "Roxana", "Bianca",
    "Alina", "Vivienne", "Seraphina", "Kristina", "Adriana",
    "Priya", "Carmen", "Lucia", "Francesca", "Yasmin",
    # Premium tier (25)
    "Alessandra", "Giselle", "Ariel", "Serena", "Elena",
    "Nikita", "Tatiana", "Mariela", "Irina", "Olga",
    "Ekaterina", "Oksana", "Darya", "Mila", "Veronika",
    "Larisa", "Daria", "Yuliya", "Mariya", "Katya",
    "Nastya", "Ingrid", "Brigitte", "Helene", "Monique",
    # Elite tier (20)
    "Chanel", "Arabella", "Evangeline", "Mirabelle", "Celestine",
    "Viviana", "Cordelia", "Isadora", "Lavinia", "Octavia",
    "Rosalind", "Isolde", "Genevieve", "Clementine", "Theodora",
    "Persephone", "Eleonora", "Wilhelmina", "Cassandra", "Veronique",
]

_TIERS = (
    ["free"] * 25 +
    ["essential"] * 30 +
    ["premium"] * 25 +
    ["elite"] * 20
)

_ETHNICITIES = ["White", "Black", "Asian", "Latin", "Mixed", "Middle Eastern", "Indian", "Other"]
_ETHNICITY_WEIGHTS = [35, 15, 12, 15, 10, 5, 6, 2]

_NATIONALITIES = [
    "British", "Romanian", "Brazilian", "Spanish", "Russian",
    "Polish", "Thai", "Italian", "French", "Hungarian",
    "Colombian", "Ukrainian", "Portuguese", "Czech", "Greek",
    "German", "Filipino", "Malaysian", "Albanian", "Moldovan",
]

_HAIR_COLOURS = ["Brunette", "Blonde", "Black", "Red", "Auburn", "Dark Brown"]
_EYE_COLOURS = ["Brown", "Blue", "Green", "Hazel", "Grey"]
_BUILDS = ["slim", "athletic", "curvy", "petite", "bbw"]
_BUILD_WEIGHTS = [30, 25, 25, 15, 5]

_AVAILABILITY = ["incall", "outcall", "both"]
_AVAIL_WEIGHTS = [40, 20, 40]

_LANGUAGES_POOL = [
    ["English"], ["English", "Romanian"], ["English", "Spanish"],
    ["English", "Russian"], ["English", "Polish"], ["English", "Italian"],
    ["English", "French"], ["English", "Portuguese"], ["English", "Thai"],
    ["English", "Hungarian"], ["English", "German"], ["English", "Arabic"],
    ["English", "Mandarin"], ["English", "Romanian", "Italian"],
    ["English", "Spanish", "Portuguese"], ["English"],
]

_ABOUT_TEMPLATES = [
    "Hi darling, I'm {name}, a passionate and attentive companion based in London. I love meeting new people and creating unforgettable experiences. I am warm, genuine and always put my clients first. Whether you're looking for stimulating conversation over dinner or a more intimate encounter, I'm here to make your time with me something truly special.",
    "Hello, I'm {name}. I'm an independent companion offering a discreet, sophisticated and pleasurable experience. I take great pride in my appearance and love to make every meeting memorable. I'm fluent in English and always happy to chat beforehand to put you at ease.",
    "Welcome! I'm {name}, a professional companion with a passion for making genuine connections. I offer a warm, friendly and completely non-judgemental service. I believe in quality over quantity and dedicate my full attention to each and every client.",
    "Hi there, I'm {name}. I'm an elegant, adventurous companion who loves life and everything it has to offer. I'm available for incall and outcall appointments and always ensure complete discretion. I'm confident, fun and down to earth — I promise you'll feel relaxed from the moment we meet.",
    "I'm {name}, a sophisticated London companion with a genuine passion for people. I take care of my appearance and love to dress up for a special occasion. Whether you want a GFE or something more adventurous, I promise to leave you wanting more.",
]

_COMMON_TAGS = ["GFE", "DFK", "OWO", "Massage", "69"]
_EXTRA_TAGS = [
    "PSE", "OWO-CIM", "CIM", "COB", "Anal", "Deep Throat", "Rimming",
    "Happy Ending", "BDSM", "Role Play", "Striptease", "Lap Dance",
    "Tantric Massage", "Erotic Massage", "Overnight", "Dinner Date",
    "Travel Companion", "Foot Fetish", "Toys",
]

# Premium borough slugs — heavier weighting for seeded escorts
_PREMIUM_SLUGS = [
    "mayfair", "kensington", "chelsea", "knightsbridge", "belgravia",
    "soho", "marylebone", "canary-wharf", "notting-hill", "covent-garden",
    "south-kensington", "victoria", "fitzrovia",
]
_REGULAR_SLUGS = [
    "westminster", "paddington", "shoreditch", "islington", "camden",
    "fulham", "hackney", "clapham", "battersea", "notting-hill",
    "earl's-court", "shepherds-bush", "brixton", "greenwich", "stratford",
    "putney", "chiswick", "wandsworth", "balham", "ealing",
]

_BOOKING_NOTICES = [
    "30 minutes notice", "1 hour notice", "2 hours notice",
    "Same day welcome", "24 hours preferred",
]

_STD_DATES = ["Jan 2025", "Feb 2025", "Mar 2025", "Apr 2025", "May 2025"]


def _random_rate(tier: str) -> dict:
    rng = random.Random()
    if tier == "free":
        base = random.choice([0, 100, 120, 150])
        return {"rate_1hour": base or None, "rate_30min": None, "rate_2hours": None, "rate_overnight": None}
    elif tier == "essential":
        h = random.choice([150, 180, 200, 220])
        return {"rate_1hour": h, "rate_30min": h // 2, "rate_2hours": h * 2, "rate_overnight": h * 6}
    elif tier == "premium":
        h = random.choice([220, 250, 280, 300])
        return {"rate_1hour": h, "rate_30min": h // 2, "rate_2hours": h * 2, "rate_overnight": h * 5}
    else:  # elite
        h = random.choice([350, 400, 450, 500, 600])
        return {"rate_1hour": h, "rate_30min": h // 2, "rate_2hours": h * 2, "rate_overnight": h * 4}


async def seed_demo_escorts():
    """Generate 100 realistic demo escort accounts. Idempotent — skips if already done."""
    async with AsyncSessionLocal() as db:
        check = await db.execute(
            select(Escort).where(Escort.email.like("%@demo.bluechips.live")).limit(1)
        )
        if check.scalar_one_or_none():
            print("[SEED] Demo escorts already seeded, skipping.")
            return

        # Load all borough IDs by slug
        boroughs_result = await db.execute(select(Borough))
        boroughs = boroughs_result.scalars().all()
        if not boroughs:
            print("[SEED] No boroughs found — run seed_boroughs() first.")
            return

        borough_map = {b.slug: b.id for b in boroughs}
        premium_boroughs = [borough_map[s] for s in _PREMIUM_SLUGS if s in borough_map]
        all_borough_ids = [b.id for b in boroughs]

        rng = random.Random(42)  # fixed seed for reproducibility

        # Pre-load all existing slugs to avoid per-row queries
        existing_slugs_res = await db.execute(select(Escort.slug))
        used_slugs: set[str] = {r[0] for r in existing_slugs_res.fetchall()}

        created = 0
        for i, (name, tier) in enumerate(zip(_NAMES, _TIERS)):
            safe_name = name.lower().replace(" ", "")
            email = f"{safe_name}{i}@demo.bluechips.live"

            ethnicity = rng.choices(_ETHNICITIES, weights=_ETHNICITY_WEIGHTS, k=1)[0]
            nationality = rng.choice(_NATIONALITIES)
            age = rng.randint(19, 38)
            height = rng.randint(158, 178)
            build = rng.choices(_BUILDS, weights=_BUILD_WEIGHTS, k=1)[0]
            hair = rng.choice(_HAIR_COLOURS)
            eye = rng.choice(_EYE_COLOURS)
            availability = rng.choices(_AVAILABILITY, weights=_AVAIL_WEIGHTS, k=1)[0]
            languages = rng.choice(_LANGUAGES_POOL)
            about = rng.choice(_ABOUT_TEMPLATES).format(name=name)
            booking_notice = rng.choice(_BOOKING_NOTICES)
            available_now = rng.random() < 0.4

            rates = _random_rate(tier)

            # Borough: 60% premium area for premium/elite, 40% for others
            if tier in ("premium", "elite") and rng.random() < 0.7:
                borough_id = rng.choice(premium_boroughs) if premium_boroughs else rng.choice(all_borough_ids)
            else:
                # 40% chance premium even for lower tiers
                if rng.random() < 0.4 and premium_boroughs:
                    borough_id = rng.choice(premium_boroughs)
                else:
                    borough_id = rng.choice(all_borough_ids)

            # Verification level based on tier
            if tier == "free":
                verification_level = 1
                blue_tick_active = False
            elif tier == "essential":
                # Half have identity verified, half just email
                verification_level = rng.choice([1, 2])
                blue_tick_active = False
            elif tier == "premium":
                verification_level = 2
                blue_tick_active = True  # auto-granted with premium
            else:  # elite
                verification_level = 2
                blue_tick_active = False  # purple tick (shown via tier + level in UI)

            std_tested = tier in ("premium", "elite") and rng.random() < 0.7
            std_date = rng.choice(_STD_DATES) if std_tested else None

            # Service tags: common + random extras
            n_extra = rng.randint(2, 8)
            tags = list(_COMMON_TAGS) + rng.sample(_EXTRA_TAGS, min(n_extra, len(_EXTRA_TAGS)))
            tags = list(set(tags))

            slug = make_unique_slug(name, used_slugs)
            used_slugs.add(slug)

            escort = Escort(
                email=email,
                hashed_password=_DEMO_PASSWORD,
                stage_name=name,
                slug=slug,
                age=age,
                nationality=nationality,
                ethnicity=ethnicity,
                height_cm=height,
                build=build,
                hair_colour=hair,
                eye_colour=eye,
                borough_id=borough_id,
                availability_type=availability,
                profile_type="individual",
                rate_1hour=rates["rate_1hour"],
                rate_30min=rates["rate_30min"],
                rate_2hours=rates["rate_2hours"],
                rate_overnight=rates["rate_overnight"],
                about_me=about,
                languages=languages,
                booking_notice=booking_notice,
                std_tested=std_tested,
                std_tested_date=std_date,
                whatsapp_number="+447955170009",
                phone_number="+447955170009",
                verification_level=verification_level,
                is_email_verified=True,
                is_active=True,
                is_approved=True,
                available_now=available_now,
                profile_complete=True,
                subscription_tier=tier,
                blue_tick_active=blue_tick_active,
                created_at=datetime.utcnow(),
            )
            db.add(escort)
            await db.flush()

            for tag in tags:
                db.add(EscortService(escort_id=escort.id, tag=tag))

            created += 1

        await db.commit()
        print(f"[SEED] Created {created} demo escort accounts.")


async def seed_all():
    await seed_boroughs()
    await seed_admin()


if __name__ == "__main__":
    asyncio.run(seed_all())
