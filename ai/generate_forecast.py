import os
import json
import base64
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def generate_forecast(
    product_name: str,
    category: str,
    pack_size: str,
    retail_price: float,
    quantity: int,
    mfg_date: str,
    expiry_date: str,
    image_bytes: bytes = None,
    image_mime: str = "image/jpeg",
) -> dict:
    """
    Call Gemini to generate a demand forecast for the given product.
    Optionally accepts a product image for visual analysis.

    Returns a dict with keys:
        accuracy          (float)   - model confidence %
        quarter           (str)     - forecast period e.g. "Q2 2026"
        trend_points      (list)    - 10 floats, demand index 0-100
        inventory_risk    (str)     - Low | Medium | High
        demand_volatility (str)     - Low | Medium | High
        supply_chain_risk (str)     - Low | Medium | High
        summary           (str)     - 2-3 sentence human-readable forecast
    """
    prompt = f"""
You are Kanzen Forecast v2.3, an AI demand-forecasting engine for beauty & wellness brands.
Analyse the product details below and return a JSON object with EXACTLY this schema
(no extra keys, no markdown fences):

{{
  "accuracy": <float 80-99, e.g. 94.3>,
  "quarter": "<e.g. Q2 2026>",
  "trend_points": [<10 floats representing relative demand index 0-100 over next 10 months>],
  "inventory_risk": "<Low | Medium | High>",
  "demand_volatility": "<Low | Medium | High>",
  "supply_chain_risk": "<Low | Medium | High>",
  "summary": "<2-3 sentence human-readable forecast summary>"
}}

Product details:
- Name: {product_name}
- Category: {category}
- Pack size: {pack_size}
- Retail price: ${retail_price}
- Current batch quantity: {quantity} units
- Manufacturing date: {mfg_date}
- Expiry date: {expiry_date}

{"An image of the product has been provided. Use visual cues (packaging quality, branding, label clarity) to refine your forecast and risk assessment." if image_bytes else ""}

Base your assessment on 18-month sales history patterns typical for {category} products,
seasonal beauty trends, and supply-chain risk factors for the region.
Return ONLY the raw JSON object — no markdown, no explanation.
"""

    # Build content parts — text always, image optional
    parts = [prompt]

    if image_bytes:
        parts.append(
            types.Part.from_bytes(data=image_bytes, mime_type=image_mime)
        )

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=parts,
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