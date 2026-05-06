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
    # GFE / romantic
    "Hey baby, I'm {name} 💋 I'm the kind of girl who'll kiss you like she means it, hold you close and make you forget about the outside world for a few hours. I love the girlfriend experience — real kissing, real passion, real connection. I'll run my hands through your hair, whisper in your ear and give you everything a good girl shouldn't. If you want someone who's genuinely into it and not just going through the motions, you've found her. I'm tactile, affectionate and I genuinely love sex — so don't be shy about telling me exactly what you want.",

    # PSE / explicit
    "Hi, I'm {name} and I'll be brutally honest — I love sex. I'm one of those girls who actually gets turned on by her clients, and trust me, you'll feel the difference. I offer a full PSE which means nothing is off the table. I love OWO, I swallow, I'll go on top and ride you until you can't take it anymore, and I'm not squeamish about anything. Deep throat, anal, facials — all available for the right gentleman. I don't do rushed or mechanical. Come to me when you want someone who's going to absolutely devour you.",

    # Dominant / confident
    "I'm {name}. I'm not your average girl next door — I'm the woman who takes control the moment you walk through my door. Whether you want me to tie you up, tease you until you beg, or simply take charge in bed, I know exactly what I'm doing. I've been told my hands are magic and my mouth is even better. I'm dominant by nature but I can read what a man needs — sometimes that's a firm hand, sometimes it's a filthy whisper telling you exactly what I'm going to do to you. Think you can handle me?",

    # Playful / naughty
    "Hello gorgeous 😈 I'm {name}, your favourite bad girl. I'm cheeky, fun and absolutely filthy once you get me going. I love a good laugh but I love a good shag even more. I'm the type who'll tease you mercilessly, get you rock hard and then make it very, very worth the wait. Expect lots of kissing, lots of touching, and me making sounds that'll drive you crazy. I'm naturally high energy in the bedroom — my regulars say I'm absolutely addictive. Come find out why.",

    # Sensual / slow burn
    "I'm {name}, and I believe the best sex starts long before you get to the bedroom. I'm all about build-up — slow kisses down your neck, fingertips running across your chest, taking my time until you're desperate for more. I love erotic massage and full body contact. I'll use every inch of my body to drive you wild. When you finally have me, it'll feel like nothing you've experienced before. I'm passionate, sensual and completely present with every man I meet. No rushing, no clock-watching — just pure, unhurried pleasure.",

    # Direct / no-nonsense
    "Let me keep this simple. I'm {name}, I'm sexy, I'm clean, and I'm very, very good at what I do. I give brilliant OWO, I love being on top, and I genuinely enjoy anal with the right person. I keep myself in great shape, I'm always freshly waxed and I smell incredible. My incall is clean and private. I don't do drama, I don't do timewasters. If you want a no-fuss, high-quality experience with a girl who's actually enthusiastic, book me. You won't be disappointed.",

    # Exotic / international
    "Hola, I'm {name} 🌹 Born in Europe, now bringing a little Mediterranean fire to London. Back home, sex isn't something to be shy about — it's something to celebrate, to savour, to do loudly and often. I bring that same energy to every appointment. I'm very oral — I love giving and receiving — and I'm the type who'll grab your head and guide you exactly where I want you. I also speak from experience when I say my hips don't lie. Book me and I'll show you what passion really means.",

    # Experienced / mature confidence
    "I'm {name} — older than some of the girls on here and better than all of them 😏 I've been doing this long enough to know exactly how to read a man and give him what he actually wants, not just what he asks for. I'm very oral, very tactile, and I have zero inhibitions. I enjoy sex — genuinely, properly enjoy it — and I'm not embarrassed to show it. My regulars keep coming back because I make them feel like the only man in the world for the time we're together. That's not an act. That's just me.",

    # Submissive / eager to please
    "Hi, I'm {name} and I live to please. I'm the kind of girl who gets satisfaction from making you completely lose control. Tell me what you want and I'll do it — I love following instructions in the bedroom and I'm incredibly responsive. I'm very tactile, I love oral both ways, and I won't stop until you're completely spent. I'm soft-spoken and sweet outside the bedroom but an absolute pleaser once the door is closed. If you want a girl who'll look up at you with those eyes and ask 'is that good, baby?' — call me.",

    # Horny / high energy
    "Okay real talk — I'm {name} and I have an absolutely filthy mind. I think about sex constantly and I need an outlet for it. I'm one of those girls who genuinely gets dripping wet for her clients and isn't embarrassed about it. I love OWO, I love being bent over, I love it when a man grabs my hips and takes control. I also give an incredible oral experience — slow, sloppy, enthusiastic. I'll moan, I'll writhe, I'll scratch your back. This isn't a performance — this is just me when I'm turned on, which is basically always.",

    # BDSM / adventurous
    "I'm {name} — adventurous, open-minded, and completely unshockable. If your tastes run a little darker than vanilla, you're in the right place. I love bondage, teasing, spanking, role play and power dynamics. I can be dominant or submissive depending on your preference — I've been told I'm equally terrifying and irresistible in both roles. I take safety and consent seriously but within that I'll push every boundary you want pushed. If you have a fantasy you've never told anyone, tell me. Chances are I'll not only be up for it — I'll make it even better than you imagined.",

    # Girlfriend experience (detailed)
    "I'm {name} 💕 and if you've been craving real intimacy — not just sex but actual connection — you've found the right girl. I offer a genuine GFE: proper kissing (I'm a fantastic kisser), cuddling, whispering, looking into your eyes. I'll make you feel wanted and desired. In the bedroom I'm passionate and generous — I love long sessions where we take our time exploring each other. I'm very into oral — giving and receiving — and I love that lazy, slow, intimate sex where you pull me close and we lose track of time. My regulars say being with me feels like being with a girlfriend who's mad about you. That's exactly what I'm going for.",

    # Luxury / high-end
    "Darling, I'm {name}. I'm selective about who I see — not because I'm precious, but because I give everything to the men I meet and I need to know you're serious. What you get with me is an immaculate experience: I'm impeccably groomed, I smell divine, my incall is luxurious, and in bed I am absolutely insatiable. I love sex in every position, every configuration. I'm particularly known for my oral — slow, deep and with full eye contact. I love to finish covered and I love to swallow. If you want the best, I'm it.",

    # Young and fresh
    "Hi I'm {name} 🌸 I know I look innocent but trust me, I'm really not 😂 I'm one of those girls who discovered she loves sex and never looked back. I'm enthusiastic, flexible (literally), and I genuinely get excited meeting new people. I love OWO and I'm told I'm very good at it. I love riding on top, I love doggy, and I'm not shy about telling you when I'm enjoying myself — which I usually am. I'm very tactile so expect lots of touching and kissing throughout. Come make my day 💋",

    # Older man specialist
    "I'm {name}, and I have a confession — I have a thing for older men. The confidence, the knowing what they want, the experience. If you're a mature gentleman who appreciates a young, willing woman who'll treat you like a king, we are going to get along very well. I love slow, appreciative sex — the kind where a man takes his time with a woman's body. I'll give you OWO to start things off right, and I'm very flexible about how we spend our time together. Discretion is everything and I am the soul of it.",

    # Party girl / social
    "Hey! I'm {name} — the fun one 🥂 I'm sociable, bubbly and absolutely love going out. If you want a date for dinner, drinks or an event before we head back somewhere private, I'm your girl — I'm great company and I scrub up beautifully. Behind closed doors though, I'm a completely different animal. I love sex and I'm not polite about it. I'll tell you what I want, I'll ask what you want, and then we'll spend the rest of the night making it happen. Life's too short for boring sex.",
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
            about = rng.choice(_ABOUT_TEMPLATES).format(name=name)[:600]
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
