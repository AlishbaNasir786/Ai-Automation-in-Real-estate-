from flask import Blueprint, request, jsonify
from db import supabase
from modules.persona_engine import generate_whatsapp_post

persona_bp = Blueprint('persona', __name__)

# Budget band → (min_price, max_price) in PKR
BUDGET_RANGES = {
    'mid':     (5_000_000,  15_000_000),
    'premium': (15_000_001, 40_000_000),
    'luxury':  (40_000_001, 9_999_999_999),
}

@persona_bp.route('/api/persona/match', methods=['POST'])
def match_persona():
    try:
        data        = request.json or {}
        persona_type = data.get('persona_type', 'investor')
        city_name    = (data.get('city') or 'Islamabad').strip()
        purpose      = data.get('purpose', 'sale')         # 'sale' or 'rent'
        budget_key   = data.get('budget', 'mid')

        listing_purpose = 'rent' if purpose == 'rent' else 'buy'
        budget_min, budget_max = BUDGET_RANGES.get(budget_key, (0, 9_999_999_999))

        # ── 1. Resolve city_id from city name ────────────────────────────
        city_res = supabase.table('cities').select('id').ilike('name', city_name).limit(1).execute()
        city_id  = city_res.data[0]['id'] if city_res.data else None

        # ── 2. Query same properties table used by home listing page ─────
        q = (
            supabase.table('properties')
            .select('id, title, city_id, listing_purpose, property_type, price_numeric, beds, baths, area_sqft, area_value, area_unit, address, featured')
            .eq('listing_purpose', listing_purpose)
            .gte('price_numeric', budget_min)
            .lte('price_numeric', budget_max)
        )
        if city_id:
            q = q.eq('city_id', city_id)

        q = q.order('featured', desc=True).order('price_numeric', desc=False).limit(100)
        db_res = q.execute()
        rows   = db_res.data or []

        # ── 3. If no strict match, relax budget constraint ────────────────
        if not rows and city_id:
            fallback = (
                supabase.table('properties')
                .select('id, title, city_id, listing_purpose, property_type, price_numeric, beds, baths, area_sqft, area_value, area_unit, address, featured')
                .eq('city_id', city_id)
                .eq('listing_purpose', listing_purpose)
                .order('featured', desc=True)
                .limit(100)
                .execute()
            )
            rows = fallback.data or []

        # ── 4. If still nothing, widen to any city ────────────────────────
        if not rows:
            any_city = (
                supabase.table('properties')
                .select('id, title, city_id, listing_purpose, property_type, price_numeric, beds, baths, area_sqft, area_value, area_unit, address, featured')
                .eq('listing_purpose', listing_purpose)
                .order('featured', desc=True)
                .limit(100)
                .execute()
            )
            rows = any_city.data or []

        if not rows:
            return jsonify({'success': False, 'error': 'No properties found in inventory.'}), 404

        # ── 5. Normalise rows for the frontend ────────────────────────────
        def normalise(row):
            area = (
                f"{row.get('area_value')} {row.get('area_unit')}"
                if row.get('area_value') else
                (f"{int(row['area_sqft'])} sqft" if row.get('area_sqft') else 'N/A')
            )
            mode = 'for_rent' if row.get('listing_purpose') == 'rent' else 'for_sale'
            return {
                'id':           row.get('id'),
                'title':        row.get('title', 'Property'),
                'city':         city_name,
                'listing_mode': mode,
                'mode':         mode,
                'property_type': row.get('property_type', ''),
                'price_numeric': row.get('price_numeric', 0),
                'beds':         row.get('beds') or 0,
                'baths':        row.get('baths') or 0,
                'area':         area,
                'area_sqft':    row.get('area_sqft'),
                'address':      row.get('address', ''),
                'featured':     row.get('featured', False),
            }

        normalised  = [normalise(r) for r in rows]
        best_match  = normalised[0]

        # ── 6. Generate WhatsApp post from real match ──────────────────────
        whatsapp_data = generate_whatsapp_post(best_match, persona_key=persona_type)

        # ── 7. Optionally log the lead (non-blocking) ─────────────────────
        try:
            supabase.table('leads').insert({'persona_type': persona_type}).execute()
        except Exception as lead_err:
            print(f'[leads insert skipped] {lead_err}')

        return jsonify({
            'success':    True,
            'property':   best_match,
            'properties': normalised,          # up to 10 results
            'whatsapp':   whatsapp_data,
            'total':      len(normalised),
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

