from decimal import Decimal
from rest_framework import serializers
from apps.products.models import Product
from .models import MarginCalculation, COGSimulation, SavedFormulation

# ──────────────────────────────────────────────────
# MARGIN CALCULATOR
# ──────────────────────────────────────────────────
class MarginCalculateSerializer(serializers.Serializer):
    """
    Figma: Margin tab inputs —
      Production Cost, Packaging, Shipping, Marketing, Retail Price
    """
    product_id      = serializers.UUIDField(required=False, allow_null=True)
    production_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    packaging_cost  = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost   = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    marketing_cost  = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    retail_price    = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, attrs):
        if attrs["retail_price"] <= 0:
            raise serializers.ValidationError({"retail_price": "Retail price must be greater than 0."})
        return attrs


class MarginResultSerializer(serializers.ModelSerializer):
    """
    Figma: Margin tab result —
      62% margin badge, $26 profit/unit, Healthy label
    """
    health_label = serializers.SerializerMethodField()
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model  = MarginCalculation
        fields = [
            "id", "product", "product_name",
            "production_cost", "packaging_cost",
            "shipping_cost",   "marketing_cost",
            "retail_price",    "total_cost",
            "profit_per_unit", "margin_pct",
            "health_label",    "created_at",
        ]

    def get_health_label(self, obj):
        # Figma: Healthy / Average / Low
        m = float(obj.margin_pct)
        if m >= 50:
            return "Healthy"
        elif m >= 30:
            return "Average"
        return "Low"


# ──────────────────────────────────────────────────
# COG BREAKDOWN SIMULATOR
# ──────────────────────────────────────────────────
class COGSimulateSerializer(serializers.Serializer):
    """
    Figma: COG Sim tab inputs — base_cost + retail_price
    Calculates 3 tiers: 1k / 5k / 10k units
    """
    product_id   = serializers.UUIDField(required=False, allow_null=True)
    base_cost    = serializers.DecimalField(max_digits=10, decimal_places=2)
    retail_price = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, attrs):
        if attrs["retail_price"] <= 0:
            raise serializers.ValidationError({"retail_price": "Retail price must be greater than 0."})
        return attrs


class COGSimulationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model  = COGSimulation
        fields = [
            "id", "product", "product_name",
            "base_cost", "retail_price",
            "tiers", "created_at",
        ]


# ──────────────────────────────────────────────────
# FORMULATION LAB
# ──────────────────────────────────────────────────
class FormulationGenerateSerializer(serializers.Serializer):
    """
    Figma: Formulation Lab → Generator tab
    Inputs: Skin Type, Concern, Format
    Calls ai/formulation.py → generate_formulation()
    """
    skin_type      = serializers.CharField(max_length=100, required=False, allow_blank=True)
    concern        = serializers.CharField(max_length=100, required=False, allow_blank=True)
    product_format = serializers.CharField(max_length=50)


class SavedFormulationSerializer(serializers.ModelSerializer):
    """
    Figma: Formulation Lab → Saved tab card
    Shows: formula_name, format, base + active stack, MOQ, cost, retail
    """
    class Meta:
        model  = SavedFormulation
        fields = [
            "id", "formula_name",
            "skin_type", "concern", "product_format",
            "base_formula", "active_stack",
            "est_moq", "cost_per_unit", "retail_range",
            "key_benefits", "ph_range", "notes",
            "created_at",
        ]


class TrendingActiveSerializer(serializers.Serializer):
    """
    Figma: Formulation Lab home — Trending Q1 2026 section
    Bakuchiol +24%, Niacinamide +18%, etc.
    """
    name     = serializers.CharField()
    category = serializers.CharField()
    growth   = serializers.CharField()