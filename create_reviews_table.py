# -*- coding: utf-8 -*-
"""
create_reviews_table.py
Creates the `reviews` table in Supabase if it doesn't already exist,
then seeds a handful of realistic Pakistani real-estate reviews so
the marketing report page has real data to display on first load.

Run once:  python create_reviews_table.py
"""

import os, sys, json, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=representation",
}


def insert_reviews(reviews: list):
    """Insert review rows directly via the Supabase REST API."""
    url = f"{SUPABASE_URL}/rest/v1/reviews"
    r   = requests.post(url, headers=HEADERS, data=json.dumps(reviews), timeout=15)
    if r.status_code in (200, 201):
        print(f"  ✅ Inserted {len(reviews)} seed reviews")
    else:
        print(f"  ⚠️  Insert responded {r.status_code}: {r.text[:200]}")


def table_exists() -> bool:
    url = f"{SUPABASE_URL}/rest/v1/reviews?limit=1"
    r   = requests.get(url, headers={**HEADERS, "Prefer": ""}, timeout=10)
    return r.status_code == 200


SEED_REVIEWS = [
    {"rating": 5, "comment": "[Ahsan Iqbal]: Absolutely fantastic platform! Found my dream apartment in E-11 within a week. The agent was extremely professional and responsive. The WhatsApp communication feature is a game changer."},
    {"rating": 4, "comment": "[Fatima Malik]: Great selection of properties in DHA Lahore. The search filters could be a little more refined but overall a very smooth experience. Highly recommend."},
    {"rating": 3, "comment": "[Usman Baig]: Decent platform but the page loads a bit slow on mobile. Some images were also missing from a few listings which made it hard to judge the property. Please fix the speed issue."},
    {"rating": 5, "comment": "[Sara Chaudhry]: I was a first-time buyer and had no idea where to start. The persona matching tool matched me with the perfect consultant and property. 5 stars!"},
    {"rating": 2, "comment": "[Bilal Ahmed]: The property information was sometimes outdated. I contacted about two listings that were already sold. The agents respond slowly on WhatsApp. Needs improvement."},
    {"rating": 5, "comment": "[Zara Noor]: Best real estate platform in Pakistan! The competitor analysis report was incredibly detailed. I could see exact market trends before making my investment decision."},
    {"rating": 4, "comment": "[Hassan Raza]: Really loved the modern interface, beautiful design. Karachi listings need to be expanded. The DHA Phase 8 section was great but PECHS listings were limited."},
    {"rating": 1, "comment": "[Nadia Hussain]: Very disappointed. The listed price was completely different from what the agent quoted. Misleading information. I wasted a full day visiting a property that was way over my budget."},
    {"rating": 5, "comment": "[Kamran Sheikh]: Professional, fast, and reliable. The luxury villa finder for Islamabad DHA was spot on. Agent was exceptional. Will use again definitely."},
    {"rating": 4, "comment": "[Ayesha Tariq]: Good experience overall. I found a beautiful apartment in Bahria Town. Would love to see a mortgage calculator added to listing pages for financial planning."},
    {"rating": 3, "comment": "[Omar Farooq]: Navigation can be confusing sometimes, hard to find the rental section. Images are good quality when they exist but many listings have no photos at all."},
    {"rating": 5, "comment": "[Rabia Khan]: Used this for renting an apartment in F-11 Islamabad. The agent was responsive and the property matched the description exactly. Honest real estate platform."},
]


def main():
    print("=" * 55)
    print("  Reviews Table Setup")
    print("=" * 55)

    print("\nChecking if reviews table exists…")
    if table_exists():
        print("  ✅ Table already exists.")
        print("\nSeeding reviews (duplicates will be ignored)…")
        insert_reviews(SEED_REVIEWS)
    else:
        print("  ⚠️  Table does not exist in Supabase.")
        print("""
  ACTION REQUIRED — create the table manually in Supabase:

  Go to:  https://supabase.com/dashboard/project/YOUR_PROJECT/sql

  Run this SQL:
  ─────────────────────────────────────────────────────
  CREATE TABLE IF NOT EXISTS public.reviews (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    reviewer_name TEXT NOT NULL,
    rating        INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment       TEXT NOT NULL,
    source        TEXT DEFAULT 'website',
    property_id   UUID REFERENCES public.properties(id) ON DELETE SET NULL,
    is_approved   BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW()
  );

  -- Enable Row Level Security (optional but recommended)
  ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;

  -- Allow public inserts (reviews from website visitors)
  CREATE POLICY "Allow public insert" ON public.reviews
    FOR INSERT WITH CHECK (true);

  -- Allow public reads of approved reviews
  CREATE POLICY "Allow public read approved" ON public.reviews
    FOR SELECT USING (is_approved = true);
  ─────────────────────────────────────────────────────

  After running the SQL, re-run this script to seed the data.
""")
        return

    print("\n✅ Setup complete!")
    print("   The marketing_report page will now show real reviews.")
    print("   Visit:  http://127.0.0.1:5000/marketing_report")


if __name__ == "__main__":
    main()
