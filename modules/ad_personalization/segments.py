"""
segments.py — Customer Persona & Target Audience Definitions
Defines buyer segments, their key priorities, pain points, tone,
and marketing hooks for hyper-personalized real estate ad generation.
"""

SEGMENTS = {
    "family": {
        "id": "family",
        "label": "Family & Parent",
        "icon": "👨‍👩‍👧‍👦",
        "tagline": "Safety, Schools & Spacious Living",
        "focus": ["Safety & Gated Security", "Nearby Top Schools", "Parks & Play Areas", "Spacious Bedrooms", "Family Neighborhood"],
        "pain_points": ["Safety concerns", "Long school commute for kids", "Cramped living space", "Lack of green parks"],
        "tone": "Warm, reassuring, practical, family-centric",
        "hooks": [
            "Give your children the neighborhood they deserve",
            "Safe gated living with top schools just 5 minutes away",
            "Spacious family home designed for lifelong memories"
        ],
        "primary_cta": "Schedule a Family Visit",
        "platforms": ["Meta (FB & IG)", "WhatsApp Broadcast", "Google Search"]
    },
    "investor": {
        "id": "investor",
        "label": "Investor & High ROI",
        "icon": "📈",
        "tagline": "Rental Yields, Capital Growth & Market Value",
        "focus": ["Rental Yield (8-12%)", "Capital Appreciation", "Price per Sq. Ft.", "High Demand Location", "Guaranteed Occupancy"],
        "pain_points": ["Low market transparency", "Low rental yields", "Unverified projects", "Slow appreciation"],
        "tone": "Confident, precise, data-driven, strategic",
        "hooks": [
            "Maximize your portfolio with up to 12% rental yield",
            "High-growth location poised for 25%+ appreciation",
            "Data-backed real estate asset in prime commercial belt"
        ],
        "primary_cta": "Request Investor Prospectus",
        "platforms": ["LinkedIn Professional", "Google Search", "Meta (FB & IG)"]
    },
    "overseas": {
        "id": "overseas",
        "label": "Overseas Pakistani",
        "icon": "✈️",
        "tagline": "100% Legal Verification, Trust & Virtual Tours",
        "focus": ["NOC / Legal Clearance", "Virtual Video Walkthroughs", "USD/PKR Exchange Advantage", "Property Management", "Secure Foreign Transfer"],
        "pain_points": ["Fear of property fraud", "Unable to physically visit", "Complicated documentation", "Management hassle"],
        "tone": "Trustworthy, transparent, patriotic, comforting",
        "hooks": [
            "Invest back home with 100% verified legal clearance",
            "Complete HD virtual tour & hassle-free remote ownership",
            "Leverage foreign currency strength for prime Pakistani real estate"
        ],
        "primary_cta": "Book HD Virtual Tour",
        "platforms": ["WhatsApp Broadcast", "Meta (FB & IG)", "Google Search"]
    },
    "luxury": {
        "id": "luxury",
        "label": "Luxury Seeker",
        "icon": "👑",
        "tagline": "Exclusivity, Smart Homes & Premium Amenities",
        "focus": ["Private Pool / Penthouse", "Smart Home Automation", "Italian Marble & Designer Kitchens", "VIP Concierge & Valet", "Prime Sector Address"],
        "pain_points": ["Ordinary build quality", "Lack of exclusivity", "No privacy", "Standard fittings"],
        "tone": "Sophisticated, exclusive, refined, aspirational",
        "hooks": [
            "Experience uncompromised luxury in Islamabad's most coveted sector",
            "Architectural masterpiece equipped with full smart automation",
            "Private penthouse with panoramic skyline vistas"
        ],
        "primary_cta": "Request VIP Private Showing",
        "platforms": ["Instagram Showcase", "LinkedIn Professional", "Meta (FB & IG)"]
    },
    "budget": {
        "id": "budget",
        "label": "Budget & First-Time Buyer",
        "icon": "💡",
        "tagline": "Flexible Installment Plans & Affordable Ownership",
        "focus": ["Low Down Payment (10-15%)", "3-Year Easy Installment Plan", "Affordable Monthly EMI", "No Hidden Charges", "Possession on 50%"],
        "pain_points": ["High upfront capital requirement", "Hidden costs", "Unaffordable monthly plans", "Delayed possession"],
        "tone": "Encouraging, accessible, practical, value-oriented",
        "hooks": [
            "Own your dream home with just 15% down payment",
            "Stop paying rent — flexible 3-year easy installment plan available",
            "Affordable luxury made accessible for first-time buyers"
        ],
        "primary_cta": "Calculate Monthly Installment",
        "platforms": ["WhatsApp Broadcast", "Meta (FB & IG)", "Google Search"]
    },
    "tenant": {
        "id": "tenant",
        "label": "Young Professional / Student",
        "icon": "🎓",
        "tagline": "Proximity to Metro, Universities & Vibrant Hubs",
        "focus": ["High-Speed Fiber Ready", "Near Metro & Bus Stops", "1-Bed / Studio Layout", "Vibrant Food & Shopping Street", "Low Maintenance Fee"],
        "pain_points": ["Long commute times", "Slow internet connectivity", "Overpriced rent", "High maintenance cost"],
        "tone": "Casual, energetic, modern, direct",
        "hooks": [
            "Modern studio apartment just 2 mins from Metro Station",
            "High-speed fiber-ready space tailored for young professionals",
            "Live in the center of food, shopping, and commercial hubs"
        ],
        "primary_cta": "Check Availability Now",
        "platforms": ["Meta (IG & FB)", "WhatsApp Broadcast"]
    }
}


def get_segment(segment_key: str) -> dict:
    """Return segment dictionary or default to 'family' if not found."""
    return SEGMENTS.get(segment_key.lower(), SEGMENTS["family"])


def get_all_segments() -> list:
    """Return list of all segments for UI display."""
    return list(SEGMENTS.values())
