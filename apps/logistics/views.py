import os
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from apps.users.permissions import IsApprovedPartner
from apps.products.models import Product
from .models import GeneratedLogisticDoc, DestinationCountry, LogisticsDocType
from .serializers import (
    ProductDropdownSerializer,
    GenerateDocumentSerializer,
    GeneratedDocSerializer,
    PatchDocumentSerializer,
)

PERMS = [IsAuthenticated, IsApprovedPartner]

# ── Destination country label map ──────────────────
DESTINATION_LABEL_MAP = {
    "eu":        "EU (Intra-EU)",
    "usa":       "USA",
    "uae":       "UAE",
    "singapore": "Singapore",
    "japan":     "Japan",
}

# ── Document type label map ────────────────────────
DOCTYPE_LABEL_MAP = {
    "commercial_invoice":    "Commercial Invoice",
    "packing_list":          "Packing List",
    "certificate_of_origin": "Certificate of Origin",
    "export_declaration":    "Export Declaration",
}


# ──────────────────────────────────────────────────
# PRODUCT DROPDOWN
# ──────────────────────────────────────────────────

class LogisticsProductListView(APIView):
    """
    GET /api/v1/logistics/products/
    Figma: Select Product dropdown in Global Logistics Partner popup.
    """
    permission_classes = PERMS

    def get(self, request):
        products = Product.objects.filter(
            brand=request.user.profile, is_active=True
        ).values("id", "name", "sku_code")
        return Response(list(products))


# ──────────────────────────────────────────────────
# GENERATE DOCUMENT
# ──────────────────────────────────────────────────

class GenerateDocumentView(GenericAPIView):
    """
    POST /api/v1/logistics/generate-document/

    Figma: 'Generate Document' button → 'Documents Generated Successfully!'

    Flow:
      1. Validate product + destination + doc_type
      2. Call ai/docs.py → generate_document() → returns document text
      3. Save text as .txt file in media/logistics/generated_docs/
      4. Return GeneratedDocSerializer
    """
    serializer_class   = GenerateDocumentSerializer
    permission_classes = PERMS

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        product     = serializer.context["product"]
        destination = serializer.validated_data["destination_country"]
        doc_type    = serializer.validated_data["document_type"]

        # ── Human-readable labels for AI prompt ───
        destination_label = DESTINATION_LABEL_MAP.get(destination, destination)
        doc_type_label    = DOCTYPE_LABEL_MAP.get(doc_type, doc_type)

        # ── Call AI docs.py ────────────────────────
        generated_file = None
        file_size_text = "PDF - 0 KB"

        try:
            from ai.docs import generate_document

            # Get latest batch for quantity info
            latest_batch = product.batches.order_by("-manufacturing_date").first()
            quantity     = latest_batch.quantity if latest_batch else 1000
            unit_price   = float(product.retail_price) if product.retail_price else 10.0

            # Call Gemini AI
            doc_text = generate_document(
                product_name        = product.name,
                sku                 = product.sku_code,
                destination_country = destination_label,
                document_type       = doc_type_label,
                quantity            = quantity,
                unit_price          = unit_price,
                product_format      = product.get_category_display(),
                exporter_name       = request.user.profile.brand_name,
                exporter_address    = request.user.profile.details.location
                                      if hasattr(request.user.profile, "details") else "",
            )

            # ── Save text file to media/ ───────────
            import uuid
            from django.core.files.base import ContentFile

            filename       = f"{doc_type}_{product.sku_code}_{uuid.uuid4().hex[:8]}.txt"
            file_content   = ContentFile(doc_text.encode("utf-8"))
            file_size_kb   = round(len(doc_text.encode("utf-8")) / 1024, 1)
            file_size_text = f"TXT - {file_size_kb} KB"

            # Save using Django's FileField
            doc_instance = GeneratedLogisticDoc(
                product             = product,
                destination_country = destination,
                document_type       = doc_type,
                file_size_text      = file_size_text,
            )
            doc_instance.file.save(filename, file_content, save=False)
            doc_instance.save()

        except ImportError:
            # AI module not connected yet — save record without file
            doc_instance = GeneratedLogisticDoc.objects.create(
                product             = product,
                destination_country = destination,
                document_type       = doc_type,
                file_size_text      = "Pending AI generation",
            )
        except Exception as e:
            return Response(
                {"error": f"AI generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            GeneratedDocSerializer(doc_instance, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


# ──────────────────────────────────────────────────
# DOCUMENT DETAIL + PATCH + DELETE
# ──────────────────────────────────────────────────

class DocumentDetailView(APIView):
    """
    GET    /api/v1/logistics/document/<uuid:pk>/
    PATCH  /api/v1/logistics/document/<uuid:pk>/
    DELETE /api/v1/logistics/document/<uuid:pk>/
    """
    permission_classes = PERMS

    def _get_doc(self, request, pk):
        try:
            return GeneratedLogisticDoc.objects.get(
                pk=pk, product__brand=request.user.profile
            )
        except GeneratedLogisticDoc.DoesNotExist:
            return None

    def get(self, request, pk):
        doc = self._get_doc(request, pk)
        if not doc:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(GeneratedDocSerializer(doc, context={"request": request}).data)

    def patch(self, request, pk):
        doc = self._get_doc(request, pk)
        if not doc:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PatchDocumentSerializer(doc, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(GeneratedDocSerializer(doc, context={"request": request}).data)

    def delete(self, request, pk):
        doc = self._get_doc(request, pk)
        if not doc:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
        if doc.file:
            doc.file.delete(save=False)
        doc.delete()
        return Response({"message": "Document deleted."}, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────────
# DOCUMENT LIST
# ──────────────────────────────────────────────────

class DocumentListView(APIView):
    """
    GET /api/v1/logistics/
    Optional: ?doc_type=commercial_invoice&destination=eu
    """
    permission_classes = PERMS

    def get(self, request):
        qs = GeneratedLogisticDoc.objects.filter(
            product__brand=request.user.profile
        ).select_related("product")

        doc_type    = request.query_params.get("doc_type")
        destination = request.query_params.get("destination")

        if doc_type:
            qs = qs.filter(document_type=doc_type)
        if destination:
            qs = qs.filter(destination_country=destination)

        return Response(
            GeneratedDocSerializer(qs, many=True, context={"request": request}).data
        )