import os
import json
from flask import Blueprint, request, jsonify
from modules.persona_engine import generate_whatsapp_post
from routes.properties import get_home_inventory

persona_bp = Blueprint('persona', __name__)

IMAGES_MAP_PATH = os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'property_images.json')


def _get_image_map():
    try:
        if os.path.exists(IMAGES_MAP_PATH):
            with open(IMAGES_MAP_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


# ── Budget bands for PURCHASE (PKR total) ────────────────────────────────
BUDGET_RANGES_SALE = {
    'mid':     (5_000_000,   25_000_000),
    'premium': (25_000_001,  60_000_000),
    'luxury':  (60_000_001, 9_999_999_999),
}

# ── Budget bands for RENT (PKR per month) ────────────────────────────────
BUDGET_RANGES_RENT = {
    'mid':     (30_000,    120_000),
    'premium': (120_001,   300_000),
    'luxury':  (300_001, 9_999_999),
}


@persona_bp.route('/api/persona/match', methods=['POST'])
def match_persona():
    try:
        data         = request.json or {}
        persona_type = data.get('persona_type', 'investor')
        sector_name  = (data.get('city') or 'Islamabad').strip().lower()
        purpose      = data.get('purpose', 'sale')   # 'sale' or 'rent'
        budget_key   = data.get('budget', 'mid')

        is_rent = purpose in ('rent', 'for_rent')

        # Pick correct budget band based on purpose
        ranges = BUDGET_RANGES_RENT if is_rent else BUDGET_RANGES_SALE
        budget_min, budget_max = ranges.get(budget_key, (0, 9_999_999_999))

        # ── 1. Fetch exact home listing property inventory ───────────────
        all_properties = get_home_inventory()
        image_map = _get_image_map()

        clean_sector = sector_name.replace('sector', '').replace('&', '').strip().lower()

        # ── Sector matching helper ────────────────────────────────────────
        def matches_sector(prop):
            if not clean_sector or clean_sector == 'islamabad':
                return True
            title    = (prop.get('title')   or '').lower()
            address  = (prop.get('address') or prop.get('sector') or prop.get('location') or '').lower()
            p_sector = (prop.get('sector')  or '').lower()
            return clean_sector in address or clean_sector in title or clean_sector in p_sector

        # ── 2. HARD filter by purpose (rent vs sale) ─────────────────────
        # This guarantees no sale listing appears in rent results and vice versa.
        def purpose_matches(prop):
            status = (prop.get('status') or '').lower()
            title  = (prop.get('title')  or '').lower()
            if is_rent:
                return 'rent' in status or 'for rent' in title or 'rental' in title
            else:
                # For Sale: exclude anything that looks like rent
                return 'rent' not in status and 'for rent' not in title

        purpose_filtered = [p for p in all_properties if purpose_matches(p)]

        # Sector filter on purpose-filtered list
        sector_matched = [p for p in purpose_filtered if matches_sector(p)]

        # Fallback: if no match in exact sector, show all purpose-matching props
        target_props = sector_matched if sector_matched else purpose_filtered

        # ── 3. Score and rank ─────────────────────────────────────────────
        def calculate_persona_score(prop):
            score     = 0
            prop_type = (prop.get('property_type') or '').lower()
            price     = float(prop.get('price_numeric') or 0)
            beds      = int(prop.get('beds') or 0)

            if matches_sector(prop):
                score += 50

            if budget_min <= price <= budget_max:
                score += 25

            if persona_type == 'luxury' and (price >= 40_000_000 or 'villa' in prop_type or 'penthouse' in prop_type):
                score += 15
            elif persona_type == 'family' and (beds >= 3 or 'villa' in prop_type or 'house' in prop_type):
                score += 15
            elif persona_type == 'investor' and ('plot' in prop_type or 'noc' in str(prop.get('description', '')).lower()):
                score += 15
            elif persona_type == 'first_time' and (price <= 35_000_000 or 'apartment' in prop_type):
                score += 15

            return score

        scored_props  = sorted(
            [(calculate_persona_score(p), p) for p in target_props],
            key=lambda x: x[0], reverse=True
        )
        matched_props = [p for _, p in scored_props]

        # ── 4. Normalise rows for frontend response ───────────────────────
        def normalise(prop):
            pid           = str(prop.get('id', ''))
            price_numeric = prop.get('price_numeric') or 0
            price_display = prop.get('price') or (f"PKR {int(price_numeric):,}" if price_numeric else 'Contact for Price')
            area          = f"{int(prop['area_sqft'])} sqft" if prop.get('area_sqft') else 'N/A'
            status        = prop.get('status') or ('For Rent' if is_rent else 'For Sale')
            img_url       = image_map.get(pid) or prop.get('image_url') or '/static/images/default_property.png'

            return {
                'id':            pid,
                'title':         prop.get('title', 'Islamabad Property'),
                'city':          prop.get('address') or prop.get('sector') or 'Islamabad',
                'sector':        prop.get('sector') or prop.get('address') or 'Islamabad',
                'listing_mode':  'for_rent' if is_rent else 'for_sale',
                'mode':          'for_rent' if is_rent else 'for_sale',
                'status':        status,
                'property_type': prop.get('property_type', 'Residential'),
                'price':         price_display,
                'price_numeric': price_numeric,
                'beds':          prop.get('beds') or 0,
                'baths':         prop.get('baths') or 0,
                'area':          area,
                'area_sqft':     prop.get('area_sqft'),
                'address':       prop.get('address') or 'Islamabad',
                'description':   prop.get('description', ''),
                'amenities':     prop.get('amenities', []),
                'image_url':     img_url,
            }

        normalised = [normalise(p) for p in matched_props[:10]]
        best_match = normalised[0] if normalised else None

        # ── 5. Generate WhatsApp post for best match ──────────────────────
        whatsapp_data = generate_whatsapp_post(best_match, persona_key=persona_type) if best_match else {
            'text':  f"Hello! I am looking for {'rental ' if is_rent else ''}properties in {data.get('city', 'Islamabad')}. Please share available options.",
            'agent': {'name': 'Islamabad Property Desk', 'phone': '+923165756055', 'agency': 'RealEstate AI'}
        }

        return jsonify({
            'success':    True,
            'property':   best_match,
            'properties': normalised,
            'whatsapp':   whatsapp_data,
            'total':      len(normalised),
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
