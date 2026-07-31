"""
insights_engine.py — AI Insights Engine
Converts the merged review + website data into structured, actionable
recommendations.

Two modes:
  1. Rule-based (default, always works, zero cost):
     Pattern-matches thresholds and known issue signatures to produce
     recommendations — same approach used by the competitor engine.

  2. Gemini LLM mode (optional, activated by GEMINI_API_KEY in .env):
     Passes the aggregated data to Google Gemini and forces structured
     JSON output for richer, more nuanced suggestions.
"""

import os
import json
import re
from datetime import datetime


# ---------------------------------------------------------------------------
# Severity + priority constants
# ---------------------------------------------------------------------------

HIGH   = "high"
MEDIUM = "medium"
LOW    = "low"


# ---------------------------------------------------------------------------
# Rule-based insights (zero API cost)
# ---------------------------------------------------------------------------

def _rule_based_insights(data: dict) -> dict:
    """
    Generates structured insights purely from thresholds and pattern matching.
    Works without any API key.
    """
    reviews = data.get("reviews", {})
    website = data.get("website", {})
    summary = data.get("summary", {})
    health  = summary.get("overall_health", {})

    weak_points      = []
    recommendations  = []
    strengths        = []

    avg_rating   = reviews.get("avg_rating",   0.0)
    total_reviews= reviews.get("total",        0)
    avg_sentiment= reviews.get("avg_sentiment",0.0)
    complaints   = reviews.get("complaints",   [])
    praises      = reviews.get("praises",      [])
    keywords     = reviews.get("top_keywords", [])
    kw_words     = [kw[0] for kw in keywords]

    all_issues   = website.get("all_issues",   [])
    avg_load     = website.get("avg_load_time_ms")
    missing_alt  = website.get("images_missing_alt", 0)
    pages_no_meta= website.get("pages_without_meta",  0)

    # ── Review-based weak points ─────────────────────────────────────────────

    if total_reviews == 0:
        weak_points.append({
            "category":    "Social Proof",
            "severity":    HIGH,
            "issue":       "No reviews collected yet",
            "detail":      "Your platform has zero customer reviews. Reviews are the #1 trust signal for property buyers.",
            "action":      "Add a review prompt to the property listing page and follow-up WhatsApp messages.",
            "impact":      "Reviews increase buyer trust and conversion by up to 270%",
        })
    elif avg_rating < 3.5:
        weak_points.append({
            "category":    "Customer Satisfaction",
            "severity":    HIGH,
            "issue":       f"Low average rating: {avg_rating}/5.0",
            "detail":      f"Based on {total_reviews} reviews. Common complaints: {'; '.join(complaints[:3])}",
            "action":      "Identify root cause from complaints below, prioritise service/UX fixes.",
            "impact":      "Every 0.5 star improvement increases inquiries by ~15%",
        })
    elif avg_rating < 4.0:
        weak_points.append({
            "category":    "Customer Satisfaction",
            "severity":    MEDIUM,
            "issue":       f"Below-target rating: {avg_rating}/5.0",
            "detail":      "Aim for 4.0+ to be competitive in the Pakistani real estate market.",
            "action":      "Address specific complaints and implement a post-visit feedback loop.",
            "impact":      "4.0+ rating unlocks better placement in portal search results",
        })
    else:
        strengths.append(f"Strong customer satisfaction: {avg_rating}/5.0 ({total_reviews} reviews)")

    if avg_sentiment < 0:
        weak_points.append({
            "category":    "Sentiment",
            "severity":    HIGH,
            "issue":       "Overall negative review sentiment",
            "detail":      f"Sentiment score: {avg_sentiment} (negative = below 0). Customers are more often using negative language than positive.",
            "action":      "Respond to all negative reviews publicly. Train agents on soft skills.",
            "impact":      "Public responses to complaints improve trust by 45%",
        })

    # Keyword-based complaint themes
    if any(w in kw_words for w in ["slow", "wait", "delay", "late", "time"]):
        weak_points.append({
            "category":    "Response Time",
            "severity":    HIGH,
            "issue":       "Customers complain about slow responses",
            "detail":      "Keywords like 'slow', 'wait', 'delay' appear frequently in reviews.",
            "action":      "Implement a 2-hour response SLA. Add WhatsApp quick-reply templates for agents.",
            "impact":      "Fast response time is the top factor in lead conversion",
        })

    if any(w in kw_words for w in ["price", "expensive", "cost", "overpriced"]):
        weak_points.append({
            "category":    "Pricing Transparency",
            "severity":    MEDIUM,
            "issue":       "Pricing concerns in reviews",
            "detail":      "Customers mention pricing issues — either prices are unclear or feel high.",
            "action":      "Add a price comparison widget and installment plan calculator to listings.",
            "impact":      "Pricing transparency reduces drop-off by 30%",
        })

    if any(w in kw_words for w in ["find", "navigate", "confus", "lost", "search"]):
        weak_points.append({
            "category":    "UX / Navigation",
            "severity":    MEDIUM,
            "issue":       "Navigation difficulty flagged in reviews",
            "detail":      "Buyers say the platform is hard to navigate or find specific properties.",
            "action":      "Add a sticky search bar with city/type/budget filters on the home page.",
            "impact":      "Better navigation increases time-on-site and leads by 20%",
        })

    # ── Website-based weak points ─────────────────────────────────────────────

    for issue_dict in all_issues:
        issue_text = issue_dict.get("issue", "")
        page_label = issue_dict.get("page", "")

        if "meta description" in issue_text.lower():
            weak_points.append({
                "category":    "Search Visibility",
                "severity":    HIGH,
                "issue":       f"Missing Search Summary on '{page_label}'",
                "detail":      "Google does not have a summary snippet to show prospective buyers in search results.",
                "action":      f"Write a clear 2-sentence overview of your services for the {page_label} page.",
                "impact":      "Attracts 15% more visitors from Google search results",
            })

        elif "h1" in issue_text.lower():
            weak_points.append({
                "category":    "Search Ranking",
                "severity":    MEDIUM,
                "issue":       f"Unclear Main Headline on '{page_label}'",
                "detail":      "Search engines cannot clearly identify the primary offering of this page.",
                "action":      f"State your main real estate offering prominently at the top of the {page_label} page.",
                "impact":      "Improves keyword ranking for local property searches",
            })

        elif "alt text" in issue_text.lower() or "missing alt" in issue_text.lower():
            weak_points.append({
                "category":    "Image Discovery",
                "severity":    MEDIUM,
                "issue":       f"Property Photos Missing Search Labels on '{page_label}'",
                "detail":      f"Multiple images on '{page_label}' lack descriptive text, hiding them from Google Image Search.",
                "action":      "Add brief text labels describing what each property photo displays.",
                "impact":      "Drives additional buyer traffic through Google Image Search",
            })

        elif "thin content" in issue_text.lower() or "word" in issue_text.lower():
            weak_points.append({
                "category":    "Customer Engagement",
                "severity":    MEDIUM,
                "issue":       f"Limited Information on '{page_label}'",
                "detail":      "Page contains minimal details, which may cause buyers to leave without making an inquiry.",
                "action":      "Add neighborhood guides, pricing insights, or property FAQs.",
                "impact":      "Keeps buyers engaged longer and increases client inquiries",
            })

        elif "slow" in issue_text.lower() or "load" in issue_text.lower():
            weak_points.append({
                "category":    "User Experience",
                "severity":    HIGH if "slow" in issue_text.lower() else MEDIUM,
                "issue":       f"Slow Mobile Loading on '{page_label}'",
                "detail":      f"Page load time ({avg_load}ms) is higher than recommended for mobile users.",
                "action":      "Compress high-resolution property photos for fast opening on mobile networks.",
                "impact":      "Retains up to 10% more interested leads on mobile devices",
            })

    # De-duplicate weak points by (category + issue prefix)
    seen  = set()
    deduped = []
    for wp in weak_points:
        key = (wp["category"], wp["issue"][:50])
        if key not in seen:
            seen.add(key)
            deduped.append(wp)
    weak_points = deduped[:12]   # cap at 12 to keep the report focused

    # ── Recommendations ───────────────────────────────────────────────────────

    if missing_alt > 0:
        recommendations.append(
            f"Add descriptive labels to {missing_alt} property images so buyers can discover them via Google Image Search."
        )
    if pages_no_meta > 0:
        recommendations.append(
            f"Add search engine summaries for {pages_no_meta} key page(s) to convert more Google searches into website visitors."
        )
    if avg_load and avg_load > 1000:
        recommendations.append(
            f"Optimize property photos to reduce load times from {avg_load}ms to under 1000ms for mobile clients."
        )
    if total_reviews < 10:
        recommendations.append(
            "Launch a WhatsApp review request initiative to gather feedback from recent satisfied buyers."
        )
    if avg_rating >= 4.0 and total_reviews >= 5:
        recommendations.append(
            f"Highlight your top-rated {avg_rating}/5 customer satisfaction rating as a prominent badge on your home page."
        )
        strengths.append(f"Strong customer trust with a {avg_rating}/5 rating across verified buyer reviews")

    recommendations += [
        "Include clear neighbourhood map links and price range filters for easier buyer browsing.",
        "Add a dedicated 'Pakistani Real Estate Market Guide' section to answer frequent buyer questions.",
        "Maintain an easy-to-use WhatsApp quick contact button on every page for immediate client inquiries.",
    ]

    # Strengths from praises
    if praises:
        strengths.append(f"Clients appreciate: '{praises[0][:100]}…'" if len(praises[0]) > 100 else f"Clients appreciate: '{praises[0]}'")

    if health.get("seo", 100) >= 80:
        strengths.append("Strong organic search presence with well-structured page titles")
    if health.get("performance", 100) >= 80:
        strengths.append(f"Fast mobile page loading (average {avg_load}ms) providing a seamless buyer experience")

    return {
        "weak_points":      weak_points,
        "recommendations":  recommendations[:8],
        "strengths":        strengths[:5],
        "generated_by":     "rule_engine",
        "generated_at":     datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Gemini LLM mode (optional)
# ---------------------------------------------------------------------------

def _gemini_insights(data: dict) -> dict:
    """
    Calls the Google Gemini API with the aggregated data to generate
    richer insights. Falls back to rule-based on any failure.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None

    try:
        import urllib.request

        # Prepare a concise summary payload (trim to keep tokens low)
        reviews = data.get("reviews", {})
        website = data.get("website", {})
        payload_summary = {
            "avg_rating":       reviews.get("avg_rating"),
            "total_reviews":    reviews.get("total"),
            "avg_sentiment":    reviews.get("avg_sentiment"),
            "top_keywords":     reviews.get("top_keywords", [])[:10],
            "complaints":       reviews.get("complaints", [])[:5],
            "praises":          reviews.get("praises", [])[:3],
            "total_site_issues":website.get("total_issues"),
            "avg_load_ms":      website.get("avg_load_time_ms"),
            "images_missing_alt":website.get("images_missing_alt"),
            "pages_without_meta":website.get("pages_without_meta"),
            "site_issues_sample":[d.get("issue") for d in website.get("all_issues", [])[:8]],
        }

        prompt = f"""You are a senior real estate business consultant analyzing a Pakistani property platform for its owner.

Here is the aggregated performance & review data:
{json.dumps(payload_summary, indent=2)}

Analyse this data and respond ONLY with valid JSON matching exactly this schema:
{{
  "weak_points": [
    {{
      "category": "string (business area e.g. Customer Satisfaction, Search Visibility, User Experience)",
      "severity": "high|medium|low",
      "issue": "string (owner-friendly description, < 80 chars)",
      "detail": "string (clear business explanation, < 200 chars)",
      "action": "string (practical business advice/fix, < 150 chars)",
      "impact": "string (expected business outcome, < 100 chars)"
    }}
  ],
  "recommendations": ["string (business action item)", "string", "string"],
  "strengths": ["string (business strength)"],
  "generated_by": "gemini"
}}

Rules:
- Write for a real estate business owner, NOT a technical web developer. Avoid jargon like 'H1 tags', 'alt text', 'meta descriptions'. Use 'Page Headline', 'Image Search Labels', 'Google Search Summary' instead.
- weak_points: list 4–8 items, most critical business issues first
- recommendations: list 5–7 practical business recommendations
- strengths: list 2–4 genuine business achievements
- Do NOT include markdown, explanation, or text outside the JSON object.
"""

        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1500}
        }).encode()

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={api_key}"
        )
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())

        raw_text = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        # Strip any markdown code fences
        raw_text = re.sub(r"```(?:json)?", "", raw_text).strip()
        parsed = json.loads(raw_text)
        parsed["generated_at"] = datetime.now().isoformat()
        return parsed

    except Exception as e:
        print(f"[insights] Gemini call failed: {e} — falling back to rule engine")
        return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_insights(data: dict) -> dict:
    """
    Main entry point — tries Gemini first, falls back to rule-based engine.
    `data` is the dict returned by aggregator.run_full_analysis().
    """
    gemini_result = _gemini_insights(data)
    if gemini_result:
        return gemini_result
    return _rule_based_insights(data)
