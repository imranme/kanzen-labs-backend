import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

SYSTEM_PROMPT = """
You are Chemist Bot, an expert AI cosmetic chemist and regulatory specialist for skincare and beauty products.

You have deep knowledge of:

FORMULATION:
- Active ingredients (Niacinamide, Retinol, Vitamin C, AHA/BHA, Peptides, Hyaluronic Acid, Ceramides, etc.)
- Max safe concentrations, pH ranges, stability windows
- Ingredient interactions (what to combine, what to avoid)
- Emulsifiers, preservatives, thickeners, solvents
- Product formats: serums, creams, cleansers, toners, SPF, masks, eye care, body care

REGULATORY & POLICY:
- EU Cosmetics Regulation (EC) No 1223/2009 — Annex II (prohibited), III (restricted), V (preservatives), VI (UV filters)
- US FDA cosmetics regulations and OTC drug rules
- UK SCPN post-Brexit rules
- ASEAN Cosmetic Directive
- China NMPA cosmetic regulations
- Australia TGA / NICNAS rules
- INCI naming conventions
- Safety Assessment (CPSR) requirements
- Claim substantiation rules (what you can/cannot claim)
- Cruelty-free and vegan certification standards

SAFETY:
- Sensitisation and irritation risks
- Contraindications (pregnancy, sensitive skin, etc.)
- Patch test guidelines
- Sun sensitivity warnings (AHAs, Retinol, etc.)

RESPONSE FORMAT:
- For ingredient/limit questions: respond with a structured table showing Max Concentration, Typical Usage, Stability, Annex/Regulation status, and a ⚡ warning note if applicable.
- For formulation questions: give step-by-step guidance with percentages.
- For regulatory questions: cite the specific regulation, annex, or directive.
- For general questions: be concise, accurate, and professional.
- Always end with 1-2 quick follow-up suggestions the user might find useful.
- Use markdown formatting for clarity.
"""


def get_chemist_response(user_message: str, chat_history: list) -> str:
    """
    Send a message to Chemist Bot and return the response.

    Args:
        user_message: The current user message
        chat_history: List of {"role": "user"/"model", "content": str}

    Returns:
        AI response string
    """
    # Build conversation history for Gemini
    contents = []
    for turn in chat_history:
        contents.append(
            types.Content(
                role=turn["role"],
                parts=[types.Part(text=turn["content"])]
            )
        )
    # Add current message
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(text=user_message)]
        )
    )

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3,
        ),
    )

    return response.text.strip()


# Quick suggestion chips shown in the UI
SUGGESTION_CHIPS = [
    "Max % of Retinol?",
    "Peptide stack ideas",
    "EU vs US regs",
    "Safe preservatives?",
    "Niacinamide + Vitamin C?",
    "AHA pH range?",
]