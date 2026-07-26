import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]
)

# Insert a test city
result = supabase.table("cities").insert({
    "name": "Islamabad",
    "slug": "islamabad",
    "province": "ICT"
}).execute()

print("Inserted:", result.data)

# Read it back
check = supabase.table("cities").select("*").execute()
print("All cities:", check.data)
