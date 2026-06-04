from rest_framework import serializers
from .models import Product, BatchRecord

# ─────────────────────────────────────────────────────────────────────────────
# 1. BATCH RECORD SERIALIZERS
# ─────────────────────────────────────────────────────────────────────────────

class BatchRecordSerializer(serializers.ModelSerializer):
    """Full batch record details used across lists and modals."""
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = BatchRecord
        fields = [
            "id", "batch_code", "quantity",
            "manufacturing_date", "expiry_date",
            "is_expired", "uploaded_at",
        ]
        read_only_fields = ["id", "uploaded_at", "is_expired"]


class BatchRecordCreateSerializer(serializers.ModelSerializer):
    """Handles creating a batch under a specific product from URL parameters."""
    class Meta:
        model = BatchRecord
        fields = ["batch_code", "quantity", "manufacturing_date", "expiry_date"]

    def validate(self, attrs):
        if attrs["expiry_date"] <= attrs["manufacturing_date"]:
            raise serializers.ValidationError(
                {"expiry_date": "Expiry date must be after manufacturing date."}
            )
        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# 2. PRODUCT SERIALIZERS
# ─────────────────────────────────────────────────────────────────────────────

class ProductListSerializer(serializers.ModelSerializer):
    """
    Compact product metadata for My Products list screen (Figma grid).
    Includes real-time compliance status mappings and latest batch snapshot.
    """
    latest_batch = BatchRecordSerializer(read_only=True)
    compliance_label = serializers.CharField(source="get_compliance_status_display", read_only=True)
    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "sku_code", "category", "category_label",
            "pack_size", "retail_price", "image",
            "compliance_status", "compliance_label",
            "compliance_health_score", "batch_count",
            "latest_batch", "created_at",
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Exposes explicit configuration properties and full manufacturing trails.
    Figma: Product Details modal layout context.
    """
    batches = BatchRecordSerializer(many=True, read_only=True)
    compliance_label = serializers.CharField(source="get_compliance_status_display", read_only=True)
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    pack_size_label = serializers.CharField(source="get_pack_size_display", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "sku_code", "barcode_ean",
            "category", "category_label",
            "pack_size", "pack_size_label",
            "retail_price", "image",
            "compliance_status", "compliance_label",
            "compliance_health_score",
            "batch_count", "batches",
            "is_active", "created_at", "updated_at",
        ]


class ProductCreateSerializer(serializers.ModelSerializer):
    """Step 1 payload parser for Upload Product configuration sequence."""
    class Meta:
        model = Product
        fields = [
            "id", 
            "name", 
            "sku_code", 
            "barcode_ean",  
            "pack_size", 
            "retail_price", 
            "image",
        ]
        read_only_fields = ["id"]

    def validate_sku_code(self, value):
        brand = self.context["request"].user.profile
        if Product.objects.filter(brand=brand, sku_code=value).exists():
            raise serializers.ValidationError("A product with this SKU already exists.")
        return value

    def create(self, validated_data):
        brand = self.context["request"].user.profile
        return Product.objects.create(brand=brand, **validated_data)


class ProductUpdateSerializer(serializers.ModelSerializer):
    """Scoped property modification structure mapping onto Edit Product flows."""
    class Meta:
        model = Product
        fields = [
            "name", "sku_code", "barcode_ean",
            "category", "pack_size", "retail_price", "image",
        ]

    def validate_sku_code(self, value):
        brand = self.context["request"].user.profile
        product = self.instance
        qs = Product.objects.filter(brand=brand, sku_code=value).exclude(pk=product.pk)
        if qs.exists():
            raise serializers.ValidationError("A product with this SKU already exists.")
        return value


# ─────────────────────────────────────────────────────────────────────────────
# 3. METRICS SCORECARD SERIALIZER
# ─────────────────────────────────────────────────────────────────────────────

class ComplianceScoreSerializer(serializers.Serializer):
    """Encapsulates aggregated scorecard analytics for dashboard banners."""
    total_products = serializers.IntegerField()
    approved = serializers.IntegerField()
    pending = serializers.IntegerField()
    rejected = serializers.IntegerField()
    health_score = serializers.IntegerField()