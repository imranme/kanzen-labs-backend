import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

SYSTEM_PROMPT = """
You are an expert international trade compliance officer and logistics documentation specialist
with 20+ years of experience in cosmetics and beauty product exports.

You generate legally compliant, professional export and customs documents for skincare/beauty brands.
Your documents follow international trade standards and destination country regulations.

Always:
- Use correct HS codes for cosmetic products (Chapter 33 of the Harmonized System)
- Apply destination-country specific requirements
- Include all mandatory fields for each document type
- Use professional trade document language and formatting
- Reference correct regulatory frameworks (EU Customs Code, US CBP, UAE Customs, etc.)

Return ONLY the document text — properly formatted, ready to use.
No JSON, no markdown fences, just the clean document content.
"""

# Options shown in the UI
DESTINATION_COUNTRIES = ["EU (Intra-EU)", "USA", "UAE", "Singapore", "Japan"]

DOCUMENT_TYPES = [
    "Commercial Invoice",
    "Packing List",
    "Certificate of Origin",
    "Export Declaration",
]

# HS codes for common cosmetic formats
HS_CODES = {
    "Serum":       "3304.99",
    "Moisturiser": "3304.99",
    "Cleanser":    "3401.30",
    "SPF":         "3304.99",
    "Eye Care":    "3304.99",
    "Body Care":   "3304.99",
    "Mask":        "3304.99",
    "Default":     "3304.99",
}


def generate_document(
    product_name: str,
    sku: str,
    destination_country: str,
    document_type: str,
    quantity: int = 1000,
    unit_price: float = 10.0,
    product_format: str = "Serum",
    exporter_name: str = "Lumina Beauty Ltd",
    exporter_address: str = "123 Beauty Lane, London, UK",
    consignee_name: str = "",
    consignee_address: str = "",
) -> str:
    """
    Generate a trade/export document using Gemini AI.

    Args:
        product_name:        Full product name
        sku:                 Product SKU / batch code
        destination_country: e.g. "EU (Intra-EU)", "USA", "UAE"
        document_type:       "Commercial Invoice" | "Packing List" |
                             "Certificate of Origin" | "Export Declaration"
        quantity:            Number of units
        unit_price:          Price per unit in GBP/USD
        product_format:      Product category for HS code lookup
        exporter_name:       Exporter company name
        exporter_address:    Exporter address
        consignee_name:      Buyer/consignee name
        consignee_address:   Buyer/consignee address

    Returns:
        str — fully formatted document text ready to use/print
    """
    hs_code = HS_CODES.get(product_format, HS_CODES["Default"])
    total_value = quantity * unit_price
    consignee = consignee_name or f"[Consignee Name — {destination_country}]"
    consignee_addr = consignee_address or f"[Consignee Address — {destination_country}]"

    prompt = f"""
Generate a complete, professional, and legally compliant {document_type} for the following shipment:

SHIPMENT DETAILS:
- Product Name: {product_name}
- SKU / Batch Code: {sku}
- Product Format: {product_format}
- HS Code: {hs_code}
- Quantity: {quantity} units
- Unit Price: £{unit_price:.2f}
- Total Value: £{total_value:,.2f}
- Destination Country / Region: {destination_country}

PARTIES:
- Exporter / Seller: {exporter_name}, {exporter_address}
- Consignee / Buyer: {consignee}, {consignee_addr}

DOCUMENT TYPE: {document_type}

Requirements based on document type:

{_get_document_requirements(document_type, destination_country)}

Generate the full {document_type} document text now.
Format it cleanly with proper headers, sections, and all mandatory fields.
Use today's date as the document date.
Return ONLY the document text — no explanations, no markdown fences.
"""

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
        ),
    )

    return response.text.strip()


def _get_document_requirements(document_type: str, destination: str) -> str:
    """Return specific requirements based on document type and destination."""

    base = {
        "Commercial Invoice": """
- Invoice number and date
- Seller and buyer full details
- Detailed product description with HS code
- Quantity, unit price, and total value
- Currency (GBP or USD)
- Terms of payment (e.g. T/T 30 days)
- Incoterms (e.g. CIF, FOB, DAP)
- Country of origin
- Shipping marks and package count
- Declaration statement
""",
        "Packing List": """
- Packing list number and date
- Seller and buyer full details
- Item-by-item breakdown: product, SKU, quantity per carton, number of cartons
- Gross weight and net weight per carton
- Dimensions of each carton (L x W x H in cm)
- Total gross weight, net weight, and total cartons
- Shipping marks
""",
        "Certificate of Origin": """
- Certificate number and date
- Exporter details (name, address, country)
- Consignee details
- Transport details (port of loading, port of discharge)
- Product description with HS code
- Origin criteria (wholly obtained / substantial transformation)
- Quantity and weight
- Declaration and authorised signature block
- Certifying body statement
""",
        "Export Declaration": """
- Declaration reference number
- Exporter EORI number (if EU) or EIN (if USA)
- Declarant details
- Procedure code
- Product description and HS commodity code
- Statistical value and currency
- Country of destination
- Means of transport
- Package type, count, and marks
- Net and gross mass
- Additional information codes if applicable
- Signatory declaration
""",
    }

    dest_notes = {
        "EU (Intra-EU)": "Apply EU Customs Union rules. Reference EU Regulation (EU) No 952/2013 (Union Customs Code). Include EORI numbers.",
        "USA":           "Apply US CBP requirements. Include FDA cosmetic registration if applicable. Use USD currency. Reference HTS code equivalent.",
        "UAE":           "Apply UAE Federal Customs Authority requirements. Include HS code per GCC Common Customs Law. Note halal certification if applicable.",
        "Singapore":     "Apply Singapore Customs TradeNet requirements. Include CDS (Customs Documentation System) reference fields.",
        "Japan":         "Apply Japan Customs requirements. Note JETRO import procedures. Include Japanese Cosmetics Standards reference if applicable.",
    }

    req = base.get(document_type, "Generate a professional trade document with all standard fields.")
    dest = dest_notes.get(destination, "Follow standard international trade document requirements.")

    return f"{req}\nDestination-specific requirements:\n{dest}"