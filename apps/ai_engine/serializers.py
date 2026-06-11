import uuid
from rest_framework import serializers
from apps.products.models import Product
from .models import ChemistChatSession, ChemistMessage, ForecastRecord


# ──────────────────────────────────────────────────
# CHEMIST BOT SERIALIZERS
# ──────────────────────────────────────────────────

class ChemistMessageSerializer(serializers.ModelSerializer):
    """Single message in chat — shown as bubble in Figma."""
    class Meta:
        model  = ChemistMessage
        fields = ["id", "role", "content", "created_at"]


class ChemistSessionSerializer(serializers.ModelSerializer):
    """Full session with all messages — for loading chat history."""
    messages = ChemistMessageSerializer(many=True, read_only=True)

    class Meta:
        model  = ChemistChatSession
        fields = ["id", "messages", "created_at", "updated_at"]


class ChemistAskSerializer(serializers.Serializer):
    """
    Figma: 'Ask about formulation...' input + send button.
    session_id optional — handles empty strings or null cleanly.
    """
    message    = serializers.CharField(max_length=2000)
    # CharField হিসেবে নিয়ে ভ্যালিডেশন ডিফেন্সিভ করা হলো যেন ফ্রন্টএন্ড খালি স্ট্রিং "" পাঠালেও ক্র্যাশ না করে
    session_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate_session_id(self, value):
        if not value:
            return None
        try:
            return uuid.UUID(str(value))
        except ValueError:
            raise serializers.ValidationError("Invalid UUID format for session_id.")


class ChemistResponseSerializer(serializers.Serializer):
    """Response after asking Chemist Bot."""
    session_id    = serializers.UUIDField()
    user_message  = ChemistMessageSerializer()
    bot_response  = ChemistMessageSerializer()
    suggestions   = serializers.ListField(
        child=serializers.CharField(), read_only=True
    )


# ──────────────────────────────────────────────────
# FORECAST SERIALIZERS
# ──────────────────────────────────────────────────

class ProductForecastDropdownSerializer(serializers.ModelSerializer):
    """
    Figma: Generate Forecast — Select Product dropdown.
    Shows product name + SKU.
    """
    class Meta:
        model  = Product
        fields = ["id", "name", "sku_code", "category", "pack_size"]


class ForecastGenerateSerializer(serializers.Serializer):
    """
    Figma: Generate Forecast popup input.
    product_id → fetches product + latest batch details.
    """
    product_id = serializers.UUIDField()

    def validate_product_id(self, value):
        brand = self.context["request"].user.profile
        try:
            product = Product.objects.get(id=value, brand=brand, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError(
                "Product not found or does not belong to your brand."
            )
        self.context["product"] = product
        return value


class ForecastRecordSerializer(serializers.ModelSerializer):
    """
    Figma: Forecast result screen —
      accuracy badge, trend chart points, risk indicators.
    """
    product_name     = serializers.CharField(source="product.name",     read_only=True)
    product_sku      = serializers.CharField(source="product.sku_code", read_only=True)
    accuracy_display = serializers.SerializerMethodField()

    class Meta:
        model  = ForecastRecord
        fields = [
            "id",
            "product", "product_name", "product_sku",
            "accuracy", "accuracy_display",
            "quarter",
            "trend_points",
            "inventory_risk", "demand_volatility", "supply_chain_risk",
            "summary",
            "model_version",
            "created_at",
        ]

    def get_accuracy_display(self, obj):
        return f"{obj.accuracy}% acc."


class ForecastListSerializer(serializers.ModelSerializer):
    """Compact card for forecast history list."""
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model  = ForecastRecord
        fields = [
            "id", "product_name", "quarter",
            "accuracy", "inventory_risk",
            "demand_volatility", "supply_chain_risk",
            "created_at",
        ]