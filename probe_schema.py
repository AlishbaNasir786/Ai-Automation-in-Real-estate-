import os, requests
from dotenv import load_dotenv
load_dotenv()

url = os.environ['SUPABASE_URL']
key = os.environ['SUPABASE_SERVICE_KEY']
headers = {'apikey': key, 'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
city_id = 'fda76289-8a14-47ea-bddc-2aaf0fe853e6'  # Islamabad from last seed

cat_vals = ['residential', 'Residential', 'RESIDENTIAL', 'commercial', 'Commercial',
            'house', 'flat', 'apartment', 'plot', 'land', 'villa', 'home']

print("Probing property_category with listing_purpose='buy'...")
for cat in cat_vals:
    r = requests.post(url + '/rest/v1/properties',
        headers={**headers, 'Prefer': 'return=representation'},
        json={
            'slug': f'test-probe-{cat}',
            'title': 'Test',
            'property_category': cat,
            'listing_purpose': 'buy',
            'status': 'active',
            'price_numeric': 100,
            'currency': 'PKR',
            'city_id': city_id
        })
    if r.status_code in (200, 201):
        pid = r.json()[0]['id'] if r.json() else None
        print(f'  VALID category: "{cat}"')
        # cleanup
        if pid:
            requests.delete(url + f'/rest/v1/properties?id=eq.{pid}', headers=headers)
    else:
        msg = r.json().get('message','') if r.content else str(r.status_code)
        constraint = 'LP_check' if 'listing_purpose' in msg else 'CAT_check' if 'category' in msg else msg[:60]
        print(f'  INVALID "{cat}": {constraint}')

print("\nProbing status values...")
for st in ['active', 'Active', 'pending', 'sold', 'rented', 'available', 'inactive', 'draft']:
    r = requests.post(url + '/rest/v1/properties',
        headers={**headers, 'Prefer': 'return=representation'},
        json={
            'slug': f'test-probe-status-{st}',
            'title': 'Test',
            'property_category': 'residential',
            'listing_purpose': 'buy',
            'status': st,
            'price_numeric': 100,
            'currency': 'PKR',
            'city_id': city_id
        })
    if r.status_code in (200, 201):
        pid = r.json()[0]['id'] if r.json() else None
        print(f'  VALID status: "{st}"')
        if pid:
            requests.delete(url + f'/rest/v1/properties?id=eq.{pid}', headers=headers)
    else:
        msg = r.json().get('message','') if r.content else str(r.status_code)
        constraint = 'status_check' if 'status' in msg else 'category_check' if 'category' in msg else msg[:60]
        print(f'  INVALID status "{st}": {constraint}')
