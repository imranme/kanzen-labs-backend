from rest_framework import serializers
from .models import ComplianceDocument, DocType, VerificationStatus
from apps.products.models import Product


class ComplianceDocumentListSerializer(serializers.ModelSerializer):
    """
    Compact card for the document list screen.
    Shows: type, title, status, file name, product name.
    """
    doc_type_label         = serializers.CharField(source="get_doc_type_display",            read_only=True)
    verification_label     = serializers.CharField(source="get_verification_status_display", read_only=True)
    product_name           = serializers.CharField(source="product.name",  read_only=True)
    product_sku            = serializers.CharField(source="product.sku_code", read_only=True)
    file_name              = serializers.CharField(read_only=True)
    file_size_kb           = serializers.FloatField(read_only=True)

    class Meta:
        model  = ComplianceDocument
        fields = [
            "id", "doc_type", "doc_type_label",
            "title", "file_name", "file_size_kb",
            "verification_status", "verification_label",
            "product_name", "product_sku",
            "uploaded_at",
        ]


class ComplianceDocumentDetailSerializer(serializers.ModelSerializer):
    """Full document detail — includes notes, verified_at, rejection_reason."""
    doc_type_label         = serializers.CharField(source="get_doc_type_display",            read_only=True)
    verification_label     = serializers.CharField(source="get_verification_status_display", read_only=True)
    product_name           = serializers.CharField(source="product.name",    read_only=True)
    product_sku            = serializers.CharField(source="product.sku_code", read_only=True)
    verified_by_email      = serializers.CharField(source="verified_by.email", read_only=True)
    file_name              = serializers.CharField(read_only=True)
    file_size_kb           = serializers.FloatField(read_only=True)

    class Meta:
        model  = ComplianceDocument
        fields = [
            "id", "doc_type", "doc_type_label",
            "title", "file", "file_name", "file_size_kb",
            "notes",
            "verification_status", "verification_label",
            "verified_at", "verified_by_email",
            "rejection_reason",
            "product", "product_name", "product_sku",
            "uploaded_at", "updated_at",
        ]


class ComplianceDocumentUploadSerializer(serializers.ModelSerializer):
    """
    Upload a new compliance document.
    Accepts multipart/form-data — file required.
    product field is optional (UUID).
    """
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        required=False, allow_null=True
    )

    class Meta:
        model  = ComplianceDocument
        fields = ["doc_type", "title", "file", "notes", "product"]

    def validate_product(self, product):
        """Ensure the product belongs to the requesting brand."""
        if product is None:
            return product
        brand = self.context["request"].user.profile
        if product.brand != brand:
            raise serializers.ValidationError("Product does not belong to your brand.")
        return product

    def create(self, validated_data):
        brand = self.context["request"].user.profile
        return ComplianceDocument.objects.create(brand=brand, **validated_data)


class ComplianceDocumentUpdateSerializer(serializers.ModelSerializer):
    """Update title / notes only — file and type are immutable after upload."""
    class Meta:
        model  = ComplianceDocument
        fields = ["title", "notes"]


class VerifyDocumentSerializer(serializers.Serializer):
    """
    Admin action — verify or reject a document.
    action: "verify" | "reject"
    reason: required only when action == "reject"
    """
    action = serializers.ChoiceField(choices=["verify", "reject"])
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["action"] == "reject" and not attrs.get("reason", "").strip():
            raise serializers.ValidationError(
                {"reason": "Rejection reason is required when rejecting a document."}
            )
        return attrs


class ComplianceScoreSerializer(serializers.Serializer):
    """
    Brand-level compliance summary.
    Figma: My Products screen — Compliance Health Score header (e.g. 60%).
    """
    total_products  = serializers.IntegerField()
    approved        = serializers.IntegerField()
    pending         = serializers.IntegerField()
    rejected        = serializers.IntegerField()
    health_score    = serializers.IntegerField()
    total_docs      = serializers.IntegerField()
    verified_docs   = serializers.IntegerField()
    pending_docs    = serializers.IntegerField()
    failed_docs     = serializers.IntegerField()