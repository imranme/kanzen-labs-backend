import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

SYSTEM_PROMPT = """
You are an expert cosmetic formulation chemist with 20+ years of experience in skincare product development.
You specialise in creating safe, effective, and market-ready formulations for beauty brands.

When given a skin type, concern, and product format, you generate a complete professional formula including:
- Base formula with exact percentages
- Active ingredient stack with exact percentages
- Manufacturing cost estimates
- MOQ (Minimum Order Quantity) estimates
- Retail price range

Always ensure:
- Total percentages add up to 100%
- pH compatibility between ingredients
- Regulatory compliance (EU/US/ASEAN)
- Stability considerations
- Safety for the stated skin type

Return ONLY a raw JSON object with no markdown fences or extra text.
"""

# Trending actives data shown on the UI
TRENDING_ACTIVES = [
    {"name": "Bakuchiol",         "category": "Retinol Alt.",  "growth": "+24%"},
    {"name": "Niacinamide",       "category": "Brightening",   "growth": "+18%"},
    {"name": "Polyglutamic Acid", "category": "Hydration",     "growth": "+31%"},
    {"name": "Azelaic Acid",      "category": "Clarity",       "growth": "+12%"},
]


def generate_formulation(
    skin_type: str,
    concern: str,
    product_format: str,
) -> dict:
    """
    Generate a complete skincare formulation using Gemini AI.

    Args:
        skin_type:      e.g. "Oily / Combination"
        concern:        e.g. "Acne, Hyperpigmentation"
        product_format: e.g. "Serum"

    Returns a dict with keys:
        base_formula    (list of {"ingredient": str, "percentage": float})
        active_stack    (list of {"ingredient": str, "percentage": float})
        est_moq         (str)   - e.g. "2,000 units"
        cost_per_unit   (str)   - e.g. "£8.90"
        retail_range    (str)   - e.g. "£38-45"
        formula_name    (str)   - suggested product name
        key_benefits    (list)  - 3 key benefit strings
        ph_range        (str)   - e.g. "5.5 - 6.0"
        notes           (str)   - formulation notes / warnings
    """
    prompt = f"""
You are an expert cosmetic formulation chemist.
Generate a complete professional skincare formulation for the following:

- Skin Type: {skin_type}
- Concern: {concern}
- Product Format: {product_format}

Return ONLY this exact JSON schema (no markdown, no explanation):

{{
  "formula_name": "<suggested product name>",
  "base_formula": [
    {{"ingredient": "<name>", "percentage": <float>}},
    {{"ingredient": "<name>", "percentage": <float>}}
  ],
  "active_stack": [
    {{"ingredient": "<name>", "percentage": <float>}},
    {{"ingredient": "<name>", "percentage": <float>}}
  ],
  "est_moq": "<e.g. 2,000 units>",
  "cost_per_unit": "<e.g. £8.90>",
  "retail_range": "<e.g. £38-45>",
  "key_benefits": ["<benefit 1>", "<benefit 2>", "<benefit 3>"],
  "ph_range": "<e.g. 5.5 - 6.0>",
  "notes": "<important formulation notes, stability warnings, contraindications>"
}}

Rules:
- Base formula + active stack percentages must total exactly 100%
- All ingredients must be INCI named
- Choose ingredients appropriate for {skin_type} skin with {concern} concerns
- Format should match a {product_format} texture and viscosity
- Cost and MOQ should reflect realistic contract manufacturing estimates
"""

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.4,
        ),
    )

    raw = response.text.strip()

    # Strip accidental markdown fences
    if raw.startswith("```"):
        chunks = raw.split("```")
        raw = chunks[1] if len(chunks) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)