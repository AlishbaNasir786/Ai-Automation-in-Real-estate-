from flask import Blueprint, request, jsonify
from db import supabase
from modules.persona_engine import match_listings, generate_whatsapp_post, load_inventory_csv

persona_bp = Blueprint('persona', __name__)

@persona_bp.route('/api/persona/match', methods=['POST'])
def match_persona():
    try:
        data = request.json
        
        # Expecting fields like: purpose, persona_type, city, budget
        persona_type = data.get('persona_type', 'investor')
        city = data.get('city', 'Islamabad')
        mode = "for_rent" if data.get('purpose') == "rent" else "for_sale"
        
        # Load inventory from Supabase
        inventory = load_inventory_csv()
        
        # Match listings based on criteria
        matched = match_listings(inventory, city=city, mode=mode)
        
        if not matched:
            return jsonify({"error": "No matching listings found."}), 404
            
        best_match = matched[0]
        
        # Generate WhatsApp post and channel rankings
        whatsapp_data = generate_whatsapp_post(best_match, persona_key=persona_type)
        
        # Try to save lead — wrapped so schema mismatches never block the response
        try:
            supabase.table('leads').insert({"persona_type": persona_type}).execute()
        except Exception as lead_err:
            print(f"[leads insert skipped] {lead_err}")
        
        # Return response expected by frontend
        return jsonify({
            "success": True,
            "property": best_match,
            "whatsapp": whatsapp_data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
