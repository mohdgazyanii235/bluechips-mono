"""
Borough seed data — runs on first boot via docker-compose command.
Idempotent: skips if boroughs already exist.
"""
import asyncio
from datetime import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal, engine, Base
from app.models.borough import Borough
from app.models.admin import Admin
from app.utils.security import hash_password
from app.config import settings


BOROUGHS = [
    {"name": "Mayfair", "slug": "mayfair", "is_premium_area": True, "sort_order": 1,
     "seo_title": "Escorts in Mayfair, London | Bluechips London",
     "seo_description": "Browse verified companion listings in Mayfair, London's most exclusive district. Independent escorts, verified profiles.",
     "description": "Mayfair is London's most prestigious neighbourhood, home to five-star hotels, Michelin-starred restaurants, and the city's most discerning clientele. Our Mayfair companions offer the highest level of companionship and discretion."},
    {"name": "Kensington", "slug": "kensington", "is_premium_area": True, "sort_order": 2,
     "seo_title": "Escorts in Kensington, London | Bluechips London",
     "seo_description": "Find verified companion listings in Kensington. Elegant, discreet independent escorts in one of London's finest areas.",
     "description": "Kensington blends royal heritage with contemporary luxury. Escorts listed here serve clients across Kensington's grand townhouses, boutique hotels, and private residences."},
    {"name": "Chelsea", "slug": "chelsea", "is_premium_area": True, "sort_order": 3,
     "seo_title": "Escorts in Chelsea, London | Bluechips London",
     "seo_description": "Discover companion listings in Chelsea, SW3. Independent escorts available for incall and outcall in Chelsea.",
     "description": "Chelsea's blend of artistic heritage and modern affluence makes it one of London's most sought-after areas. Our Chelsea companions are elegant, cultured, and experienced."},
    {"name": "Knightsbridge", "slug": "knightsbridge", "is_premium_area": True, "sort_order": 4,
     "seo_title": "Escorts in Knightsbridge, London | Bluechips London",
     "seo_description": "Elite companion listings in Knightsbridge, home to Harrods and London's finest hotels.",
     "description": "Steps from Harrods and Hyde Park, Knightsbridge is synonymous with luxury. Companions in this area cater to an international, high-net-worth clientele."},
    {"name": "Belgravia", "slug": "belgravia", "is_premium_area": True, "sort_order": 5,
     "seo_title": "Escorts in Belgravia, London | Bluechips London",
     "seo_description": "Premium companion directory for Belgravia, London SW1. Verified, discreet escorts.",
     "description": "One of London's most exclusive postcodes, Belgravia's white stucco townhouses and private garden squares set the scene for the city's most refined companionship experiences."},
    {"name": "Soho", "slug": "soho", "is_premium_area": True, "sort_order": 6,
     "seo_title": "Escorts in Soho, London | Bluechips London",
     "seo_description": "Find companion listings in Soho, central London. Vibrant, diverse independent escorts in W1.",
     "description": "Soho's energy and cosmopolitan spirit attract a diverse and open-minded crowd. Companions listed here reflect the neighbourhood's bold, expressive character."},
    {"name": "Marylebone", "slug": "marylebone", "is_premium_area": True, "sort_order": 7,
     "seo_title": "Escorts in Marylebone, London | Bluechips London",
     "seo_description": "Companion listings in Marylebone, W1. Elegant independent escorts near Harley Street and Regent's Park.",
     "description": "Marylebone's village atmosphere and elegant Georgian streets house some of London's most sophisticated companions, popular with both city professionals and international visitors."},
    {"name": "Westminster", "slug": "westminster", "is_premium_area": False, "sort_order": 8,
     "seo_title": "Escorts in Westminster, London | Bluechips London",
     "seo_description": "Companion directory for Westminster, central London. Independent escort listings.",
     "description": "Westminster's central location makes it one of London's most convenient areas for both incall and outcall companion services."},
    {"name": "Paddington", "slug": "paddington", "is_premium_area": False, "sort_order": 9,
     "seo_title": "Escorts in Paddington, London | Bluechips London",
     "seo_description": "Find companions in Paddington, W2. Independent escort listings close to Hyde Park.",
     "description": "Paddington's proximity to Hyde Park and excellent transport links make it popular with escorts offering incall services in comfortable, private apartments."},
    {"name": "Canary Wharf", "slug": "canary-wharf", "is_premium_area": True, "sort_order": 10,
     "seo_title": "Escorts in Canary Wharf, London | Bluechips London",
     "seo_description": "Companion listings in Canary Wharf and Docklands. Discreet escorts for London's business district.",
     "description": "Canary Wharf's gleaming towers house London's financial elite. Companions in this area frequently serve busy professionals, offering flexible scheduling and the highest discretion."},
    {"name": "Notting Hill", "slug": "notting-hill", "is_premium_area": True, "sort_order": 11,
     "seo_title": "Escorts in Notting Hill, London | Bluechips London",
     "seo_description": "Independent companion listings in Notting Hill, W11. Verified profiles, discreet service.",
     "description": "Notting Hill's pastel townhouses and lively culture attract creative, cosmopolitan companions who blend sophistication with a relaxed, warm approach."},
    {"name": "Shoreditch", "slug": "shoreditch", "is_premium_area": False, "sort_order": 12,
     "seo_title": "Escorts in Shoreditch, London | Bluechips London",
     "seo_description": "Companion directory for Shoreditch and East London. Modern, independent escort listings.",
     "description": "Shoreditch's creative energy and diverse scene attract bold, contemporary companions serving London's tech and creative industries."},
    {"name": "Islington", "slug": "islington", "is_premium_area": False, "sort_order": 13,
     "seo_title": "Escorts in Islington, London | Bluechips London",
     "seo_description": "Companion listings in Islington, N1. Independent escorts in North London.",
     "description": "Islington's independent spirit and upmarket village feel make it home to some of North London's most sought-after companions."},
    {"name": "Camden", "slug": "camden", "is_premium_area": False, "sort_order": 14,
     "seo_title": "Escorts in Camden, London | Bluechips London",
     "seo_description": "Find companion listings in Camden, NW1. Eclectic, independent escorts in North London.",
     "description": "Camden's eclectic character attracts a wide range of companions suited to clients who appreciate personality and individuality alongside beauty."},
    {"name": "Fulham", "slug": "fulham", "is_premium_area": False, "sort_order": 15,
     "seo_title": "Escorts in Fulham, London | Bluechips London",
     "seo_description": "Companion listings in Fulham, SW6. Independent escorts in West London.",
     "description": "Fulham's leafy streets and affluent residential character make it popular with companions catering to local professionals and families seeking discretion."},
    {"name": "Hammersmith", "slug": "hammersmith", "is_premium_area": False, "sort_order": 16,
     "seo_title": "Escorts in Hammersmith, London | Bluechips London",
     "seo_description": "Companion directory for Hammersmith, W6. Independent escorts in West London.",
     "description": "Hammersmith's central West London location provides easy access across the city, making it a practical base for companions offering outcall services."},
    {"name": "Hackney", "slug": "hackney", "is_premium_area": False, "sort_order": 17,
     "seo_title": "Escorts in Hackney, London | Bluechips London",
     "seo_description": "Find companion listings in Hackney, East London. Independent escort directory.",
     "description": "Hackney's cultural diversity and creative scene are reflected in the vibrant, international range of companions listing in this area."},
    {"name": "Greenwich", "slug": "greenwich", "is_premium_area": False, "sort_order": 18,
     "seo_title": "Escorts in Greenwich, London | Bluechips London",
     "seo_description": "Companion listings in Greenwich, SE10. Independent escorts in South-East London.",
     "description": "Greenwich's historic charm and riverside setting provide a beautiful backdrop for companions serving South-East London and the wider Thames area."},
    {"name": "Brixton", "slug": "brixton", "is_premium_area": False, "sort_order": 19,
     "seo_title": "Escorts in Brixton, London | Bluechips London",
     "seo_description": "Companion directory for Brixton, SW9. Independent escorts in South London.",
     "description": "Brixton's vibrant energy and cultural richness attract a diverse community of companions who bring warmth, passion, and individuality to every encounter."},
    {"name": "Clapham", "slug": "clapham", "is_premium_area": False, "sort_order": 20,
     "seo_title": "Escorts in Clapham, London | Bluechips London",
     "seo_description": "Companion listings in Clapham, SW4. Independent escorts in South London.",
     "description": "Clapham's young, professional population and lively social scene create strong demand for companion services throughout the week and weekends."},
    {"name": "Battersea", "slug": "battersea", "is_premium_area": False, "sort_order": 21,
     "seo_title": "Escorts in Battersea, London | Bluechips London",
     "seo_description": "Find companion listings in Battersea, SW11. Independent escorts near Nine Elms.",
     "description": "Battersea's regeneration and growing luxury residential developments have brought a new, affluent clientele to this part of South-West London."},
    {"name": "Richmond", "slug": "richmond", "is_premium_area": False, "sort_order": 22,
     "seo_title": "Escorts in Richmond, London | Bluechips London",
     "seo_description": "Companion listings in Richmond, Surrey. Independent escorts in South-West London.",
     "description": "Richmond's riverside beauty and wealthy residential character attract companions who cater to an affluent, privacy-conscious clientele in South-West London."},
    {"name": "Wimbledon", "slug": "wimbledon", "is_premium_area": False, "sort_order": 23,
     "seo_title": "Escorts in Wimbledon, London | Bluechips London",
     "seo_description": "Companion directory for Wimbledon, SW19. Independent escorts in South-West London.",
     "description": "Wimbledon's prestigious address and well-heeled residents create a steady demand for high-quality, discreet companionship throughout the year."},
    {"name": "Stratford", "slug": "stratford", "is_premium_area": False, "sort_order": 24,
     "seo_title": "Escorts in Stratford, London | Bluechips London",
     "seo_description": "Find companion listings in Stratford, E15. Independent escorts in East London.",
     "description": "Stratford's regeneration following the 2012 Olympics has transformed it into a thriving hub with excellent transport links to central London and beyond."},
    {"name": "Wembley", "slug": "wembley", "is_premium_area": False, "sort_order": 25,
     "seo_title": "Escorts in Wembley, London | Bluechips London",
     "seo_description": "Companion listings in Wembley, North-West London. Independent escort directory.",
     "description": "Wembley's diverse community and central North-West London location make it home to a wide range of companions serving the local and surrounding area."},
    {"name": "Covent Garden", "slug": "covent-garden", "is_premium_area": True, "sort_order": 26,
     "seo_title": "Escorts in Covent Garden, London | Bluechips London",
     "seo_description": "Companion listings in Covent Garden, WC2. Premium escorts in central London.",
     "description": "Covent Garden's theatre district, fine dining, and luxury hotels make it a hub for companions catering to culture-loving, sociable clientele."},
    {"name": "South Kensington", "slug": "south-kensington", "is_premium_area": True, "sort_order": 27,
     "seo_title": "Escorts in South Kensington, London | Bluechips London",
     "seo_description": "Companion directory for South Kensington, SW7. Elite independent escorts.",
     "description": "South Kensington's French community, world-class museums, and beautiful garden squares attract cultured, multilingual companions from across Europe."},
    {"name": "Earl's Court", "slug": "earls-court", "is_premium_area": False, "sort_order": 28,
     "seo_title": "Escorts in Earl's Court, London | Bluechips London",
     "seo_description": "Companion listings in Earl's Court, SW5. Independent escorts in West London.",
     "description": "Earl's Court's international character and excellent transport links make it a convenient base for companions serving West London and beyond."},
    {"name": "Shepherd's Bush", "slug": "shepherds-bush", "is_premium_area": False, "sort_order": 29,
     "seo_title": "Escorts in Shepherd's Bush, London | Bluechips London",
     "seo_description": "Find companion listings in Shepherd's Bush, W12. Independent escorts in West London.",
     "description": "Shepherd's Bush's diverse and cosmopolitan community is reflected in the range of companions available in this vibrant West London neighbourhood."},
    {"name": "Croydon", "slug": "croydon", "is_premium_area": False, "sort_order": 30,
     "seo_title": "Escorts in Croydon, London | Bluechips London",
     "seo_description": "Companion listings in Croydon, South London. Independent escort directory.",
     "description": "Croydon's status as South London's commercial centre and transport hub makes it an accessible location for companions serving clients across the southern suburbs."},
    {"name": "Ilford", "slug": "ilford", "is_premium_area": False, "sort_order": 31,
     "seo_title": "Escorts in Ilford, East London | Bluechips London",
     "seo_description": "Find companion listings in Ilford, IG1. Independent escorts in East London.",
     "description": "Ilford's diverse community and excellent links into central London make it a practical and convenient area for companion services in East London."},
    {"name": "Romford", "slug": "romford", "is_premium_area": False, "sort_order": 32,
     "seo_title": "Escorts in Romford, London | Bluechips London",
     "seo_description": "Companion listings in Romford, RM1. Independent escorts in East London.",
     "description": "Romford's busy town centre and strong residential community create consistent demand for companion services across this part of East London."},
]


async def seed_boroughs():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Borough).limit(1))
        if result.scalar_one_or_none():
            print("[SEED] Boroughs already seeded, skipping.")
            return

        for data in BOROUGHS:
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
        print(f"[SEED] {len(BOROUGHS)} London boroughs seeded successfully.")


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


async def seed_all():
    await seed_boroughs()
    await seed_admin()


if __name__ == "__main__":
    asyncio.run(seed_all())
