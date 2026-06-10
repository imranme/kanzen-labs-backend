from rest_framework import serializers
from apps.products.models import Product
from .models import GeneratedLogisticDoc, DestinationCountry, LogisticsDocType


# ── Product dropdown ──────────────────────────────

class ProductDropdownSerializer(serializers.ModelSerializer):
    """Figma: Select Product dropdown list."""
    class Meta:
        model  = Product
        fields = ["id", "name", "sku_code"]


# ── Generate request ──────────────────────────────

class GenerateDocumentSerializer(serializers.Serializer):
    """
    Figma: Global Logistics Partner popup input.
    product_id + destination_country + document_type → AI generates doc.
    """
    product_id = serializers.UUIDField()
    destination_country = serializers.ChoiceField(choices=DestinationCountry.choices)
    document_type       = serializers.ChoiceField(choices=LogisticsDocType.choices)

    def validate_product_id(self, value):
        brand = self.context["request"].user.profile
        try:
            product = Product.objects.get(id=value, brand=brand, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or does not belong to your brand.")
        self.context["product"] = product
        return value


# ── Document read ─────────────────────────────────

class GeneratedDocSerializer(serializers.ModelSerializer):
    """
    Figma: 'Documents Generated Successfully!' screen.
    Shows: doc type, file name, file size, download link.
    """
    document_type_label       = serializers.CharField(
        source="get_document_type_display", read_only=True
    )
    destination_country_label = serializers.CharField(
        source="get_destination_country_display", read_only=True
    )
    product_name = serializers.CharField(source="product.name",     read_only=True)
    product_sku  = serializers.CharField(source="product.sku_code", read_only=True)
    file_name    = serializers.CharField(read_only=True)

    class Meta:
        model  = GeneratedLogisticDoc
        fields = [
            "id",
            "product", "product_name", "product_sku",
            "destination_country", "destination_country_label",
            "document_type", "document_type_label",
            "file", "file_url", "file_name", "file_size_text",
            "created_at", "updated_at",
        ]


# ── Patch (edit before download) ──────────────────

class PatchDocumentSerializer(serializers.ModelSerializer):
    """
    PATCH before downloading — edit destination or doc type.
    Figma: edit fields on the generated doc screen.
    """
    class Meta:
        model  = GeneratedLogisticDoc
        fields = ["destination_country", "document_type"]