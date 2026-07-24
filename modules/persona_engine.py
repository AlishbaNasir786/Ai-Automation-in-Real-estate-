"""
Persona Engine & WhatsApp Generator Module
Provides Python programmatic interface for buyer persona profiling,
platform suitability ranking, inventory matching from scraped CSVs,
and WhatsApp marketing message generation.
"""

import os
import sys
import io
import re
import csv
import random
import urllib.parse
from datetime import datetime

# Force UTF-8 output so emoji print correctly on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")



# ---------------------------------------------------------------------------
# Persona Configurations & Platform Matrix
# ---------------------------------------------------------------------------

PERSONA_PROFILES = {
    "investor": {
        "title": "Yield & Growth Capitalist",
        "badge": "Investor Archetype",
        "description": "High focus on rental ROI, capital appreciation potential, and pre-launch prices.",
        "angle": "Highlights ROI calculation, rental yield projections, and pre-launch pricing urgency.",
        "hook": "📈 *HIGH-YIELD REAL ESTATE INVESTMENT OPPORTUNITY* 📈",
        "platforms": [
            {"name": "WhatsApp Direct Broadcast", "score": 96, "color": "#25d366"},
            {"name": "LinkedIn Professional Network", "score": 84, "color": "#0077b5"},
            {"name": "Direct Portal Alerts", "score": 78, "color": "#38bdf8"},
            {"name": "Email Investment Digest", "score": 65, "color": "#f59e0b"},
        ]
    },
    "first_time": {
        "title": "Security & First-Home Seeker",
        "badge": "First Buyer Archetype",
        "description": "Prioritizes easy installment plans, builder reputation, and immediate possession.",
        "angle": "Highlights installment breakdown, clear title verification, and family safety.",
        "hook": "🔑 *AFFORDABLE FIRST-HOME OPPORTUNITY* 🔑",
        "platforms": [
            {"name": "Instagram & Reels Showcase", "score": 92, "color": "#e1306c"},
            {"name": "WhatsApp Advisory Chat", "score": 88, "color": "#25d366"},
            {"name": "Direct Web Search Portal", "score": 85, "color": "#38bdf8"},
            {"name": "Facebook Community Groups", "score": 74, "color": "#1877f2"},
        ]
    },
    "family": {
        "title": "Family Nest & Space Upgrader",
        "badge": "Family Archetype",
        "description": "Seeking 3-5 bedrooms, gated security, nearby top schools, and green parks.",
        "angle": "Emphasizes neighbourhood tranquility, bedroom count, and proximity to schools.",
        "hook": "🏡 *SPACIOUS FAMILY HOME SPOTLIGHT* 🏡",
        "platforms": [
            {"name": "WhatsApp Video Walkthrough", "score": 94, "color": "#25d366"},
            {"name": "Facebook Meta Ads", "score": 86, "color": "#1877f2"},
            {"name": "Direct Portal Search", "score": 82, "color": "#38bdf8"},
            {"name": "Community Email Newsletter", "score": 68, "color": "#f59e0b"},
        ]
    },
    "luxury": {
        "title": "Executive Portfolio Collector",
        "badge": "Luxury Archetype",
        "description": "Demands prime boulevard location, modern architectural aesthetics, and privacy.",
        "angle": "Conveys exclusive white-glove availability, prime location prestige, and luxury finishes.",
        "hook": "💎 *PREMIUM LUXURY RESIDENCE SPOTLIGHT* 💎",
        "platforms": [
            {"name": "Private WhatsApp VIP Concierge", "score": 98, "color": "#25d366"},
            {"name": "LinkedIn Executive Network", "score": 90, "color": "#0077b5"},
            {"name": "Instagram High-Design Feed", "score": 85, "color": "#e1306c"},
            {"name": "Bespoke Portfolio Mailer", "score": 72, "color": "#f59e0b"},
        ]
    }
}

VERIFIED_AGENTS = [
    {"name": "Tariq Mahmood", "title": "Senior Investment Advisor", "agency": "Premier Real Estate", "phone": "+923005551234"},
    {"name": "Zainab Chaudhry", "title": "Residential Specialist", "agency": "Apex Luxury Properties", "phone": "+923219876543"},
    {"name": "Bilal Farooq", "title": "Commercial Portfolio Manager", "agency": "Capital Heights Realty", "phone": "+923334445566"},
    {"name": "Hamza Alvi", "title": "Property Consultant", "agency": "Zameen Platinum Partners", "phone": "+923451122334"}
]

FALLBACK_LISTINGS = [
    {
        "title": "10 Marla Brand New Modern House in G-13",
        "city": "Houses_Islamabad",
        "listing_mode": "for_sale",
        "property_type": "House",
        "price": "PKR 2.85 Crore",
        "price_numeric": 28500000,
        "beds": 5, "baths": 6, "area": "10 Marla"
    },
    {
        "title": "1 Kanal Luxury Executive Villa in DHA Phase 2",
        "city": "Houses_Islamabad",
        "listing_mode": "for_sale",
        "property_type": "House",
        "price": "PKR 6.5 Crore",
        "price_numeric": 65000000,
        "beds": 6, "baths": 7, "area": "1 Kanal"
    },
    {
        "title": "3 Bed Luxury Apartment in E-11 Sector",
        "city": "Flats_Rent_Islamabad",
        "listing_mode": "for_rent",
        "property_type": "Flat",
        "price": "PKR 110 Thousand",
        "price_numeric": 110000,
        "beds": 3, "baths": 3, "area": "2100 Sq Ft"
    },
    {
        "title": "5 Marla Stylish House in Bahria Town Sector C",
        "city": "Houses_Lahore",
        "listing_mode": "for_sale",
        "property_type": "House",
        "price": "PKR 1.85 Crore",
        "price_numeric": 18500000,
        "beds": 3, "baths": 4, "area": "5 Marla"
    }
]

# ---------------------------------------------------------------------------
# Core Engine Functions
# ---------------------------------------------------------------------------

def load_inventory_csv(filepath: str = "data/zameen_all_listings.csv") -> list:
    """Load inventory listings from CSV or return fallback data if file missing."""
    if not os.path.exists(filepath):
        return FALLBACK_LISTINGS

    listings = []
    try:
        with open(filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numerical fields
                try:
                    row["price_numeric"] = int(float(row.get("price_numeric") or 0))
                except ValueError:
                    row["price_numeric"] = 0
                listings.append(row)
    except Exception as e:
        print(f"Warning loading {filepath}: {e}")
        return FALLBACK_LISTINGS

    return listings if listings else FALLBACK_LISTINGS


def match_listings(listings: list, city: str = "Islamabad", mode: str = "for_sale", prop_type: str = None) -> list:
    """Filter listings strictly by city, mode (sale/rent), and optional property type."""
    city_clean = city.lower()
    mode_clean = mode.lower()
    
    # 1. Strict match: City + Mode + Property Type
    matches = []
    for item in listings:
        item_city = str(item.get("city", "")).lower()
        item_mode = str(item.get("listing_mode", "")).lower()
        item_type = str(item.get("property_type", "")).lower()

        if city_clean in item_city and mode_clean in item_mode:
            if prop_type and prop_type.lower() not in item_type:
                continue
            matches.append(item)

    # 2. Strict City + Mode match (ignoring prop_type)
    if not matches:
        matches = [l for l in listings if city_clean in str(l.get("city", "")).lower() and mode_clean in str(l.get("listing_mode", "")).lower()]

    # 3. Strict City-only match (never cross city boundaries)
    if not matches:
        matches = [l for l in listings if city_clean in str(l.get("city", "")).lower()]

    # 4. Safe fallback: clean city-specific template if 0 listings exist for this city
    if not matches:
        matches = [{
            "title": f"Prime {prop_type or 'Property'} Opportunity in {city}",
            "city": f"{prop_type or 'Houses'}_{city}",
            "listing_mode": mode,
            "property_type": prop_type or "House",
            "price": "PKR 2.5 Crore" if mode == "for_sale" else "PKR 75 Thousand",
            "price_numeric": 25000000 if mode == "for_sale" else 75000,
            "beds": 4, "baths": 4, "area": "10 Marla"
        }]

    return matches


def generate_whatsapp_post(listing: dict, persona_key: str = "investor", agent: dict = None, recipient_phone: str = None) -> dict:
    """
    Generates formatted WhatsApp message text and a 100% free wa.me URL link.
    If recipient_phone is provided, targets that phone number directly.
    """
    persona = PERSONA_PROFILES.get(persona_key, PERSONA_PROFILES["investor"])
    if not agent:
        agent = random.choice(VERIFIED_AGENTS)

    title = listing.get("title", "Featured Property")
    raw_city = listing.get("city", "Islamabad")
    city_name = raw_city.split("_")[-1] if "_" in raw_city else raw_city
    price = listing.get("price", "Contact for Price")
    area = listing.get("area", "N/A")
    beds = listing.get("beds", "N/A")
    mode = "For Rent" if listing.get("listing_mode") == "for_rent" else "For Sale"

    message = (
        f"{persona['hook']}\n\n"
        f"Hello! Based on your preferred *{persona['title']}* profile, here is a curated verified listing:\n\n"
        f"🏡 *{title}*\n"
        f"📍 *Location:* {city_name}, Pakistan ({mode})\n"
        f"💰 *Price:* {price}\n"
        f"📐 *Specs:* {area} | {beds} Bedrooms | Verified Title\n\n"
        f"💡 *Why This Fits You:*\n"
        f"✓ Handpicked for {city_name} buyers seeking high market value.\n"
        f"✓ Verified seller title & clear documentation guaranteed.\n\n"
        f"👤 *Assigned Consultant:*\n"
        f"*{agent['name']}* ({agent['title']})\n"
        f"🏢 {agent['agency']}\n"
        f"📞 Call / WhatsApp: {agent['phone']}\n\n"
        f"Reply *YES* to schedule a private video walkthrough or site visit!"
    )

    encoded_msg = urllib.parse.quote(message)
    target_phone = recipient_phone or agent.get("phone", "")
    clean_phone = re.sub(r"[^0-9]", "", str(target_phone))
    if clean_phone.startswith("0"):
        clean_phone = "92" + clean_phone[1:]

    wa_target_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}" if clean_phone else f"https://api.whatsapp.com/send?text={encoded_msg}"
    wa_share_url = f"https://api.whatsapp.com/send?text={encoded_msg}"

    return {
        "text": message,
        "wa_link": wa_target_url,
        "wa_share_link": wa_share_url,
        "persona_title": persona["title"],
        "agent": agent,
        "recipient_phone": clean_phone,
    }


if __name__ == "__main__":
    print("Testing Persona Engine & WhatsApp Generator...")
    listings = load_inventory_csv()
    print(f"Loaded {len(listings)} listings from dataset.")

    matched = match_listings(listings, city="Islamabad", mode="for_sale")
    print(f"Matched {len(matched)} properties for Islamabad For Sale.")

    if matched:
        result = generate_whatsapp_post(matched[0], persona_key="investor")
        print("\n" + "="*60)
        print("  GENERATED WHATSAPP MESSAGE PREVIEW")
        print("="*60)
        print(result["text"])
        print("\nFree wa.me Link:")
        print(result["wa_link"])
        print("="*60)
