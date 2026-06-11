"""
Growth Engine business logic.
- Margin calculation
- COG tier simulation
"""
from decimal import Decimal, ROUND_HALF_UP


def calculate_margin(production, packaging, shipping, marketing, retail):
    """
    Calculates margin % and profit/unit.
    Figma: Margin tab — 62% badge, $26 profit/unit
    """
    total_cost      = production + packaging + shipping + marketing
    profit_per_unit = retail - total_cost
    margin_pct      = (profit_per_unit / retail * 100).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return {
        "total_cost":      total_cost,
        "profit_per_unit": profit_per_unit,
        "margin_pct":      margin_pct,
    }


def simulate_cog_tiers(base_cost, retail_price):
    """
    Simulates COG breakdown at 1k / 5k / 10k units.
    Figma: COG Sim tab — 1k units £12,500 | 5k units £50,000 etc.
    Bulk discount applied: 5% at 5k, 12% at 10k.
    """
    tiers = []
    configs = [
        {"units": 1000,  "discount": Decimal("0.00")},
        {"units": 5000,  "discount": Decimal("0.05")},
        {"units": 10000, "discount": Decimal("0.12")},
    ]
    for cfg in configs:
        unit_cost     = base_cost * (1 - cfg["discount"])
        total_cost    = unit_cost * cfg["units"]
        profit        = retail_price - unit_cost
        margin        = (profit / retail_price * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        breakeven     = int(total_cost / profit) if profit > 0 else 0
        tiers.append({
            "units":      cfg["units"],
            "unit_cost":  float(unit_cost.quantize(Decimal("0.01"))),
            "total_cost": float(total_cost.quantize(Decimal("0.01"))),
            "margin_pct": float(margin),
            "breakeven":  breakeven,
        })
    return tiers