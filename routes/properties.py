from flask import Blueprint, jsonify
from db import supabase

properties_bp = Blueprint('properties', __name__)

@properties_bp.route('/api/properties', methods=['GET'])
def get_properties():
    try:
        response = supabase.table('properties').select('*').execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
