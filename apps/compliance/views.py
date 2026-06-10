from rest_framework import status
from rest_framework.generics import GenericAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsApprovedPartner
from .models import ComplianceDocument
from .serializers import (
    ComplianceDocumentListSerializer,
    ComplianceDocumentDetailSerializer,
    ComplianceDocumentUploadSerializer,
    ComplianceDocumentUpdateSerializer,
    VerifyDocumentSerializer,
    ComplianceScoreSerializer,
)
from .services import verify_document, reject_document, get_brand_compliance_summary


# ──────────────────────────────────────────────────
# DOCUMENT LIST + UPLOAD
# ──────────────────────────────────────────────────

class ComplianceDocumentListView(APIView):
    """
    GET  /api/v1/compliance/          → list all brand documents
    POST /api/v1/compliance/          → upload new document (multipart)

    Optional query params for GET:
      ?doc_type=coa|cpsr|msds|other
      ?status=pending|verified|failed
      ?product=<product_uuid>
    """
    permission_classes = [IsAuthenticated, IsApprovedPartner]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        brand = request.user.profile
        qs    = ComplianceDocument.objects.filter(brand=brand).select_related("product")

        # Filters
        doc_type = request.query_params.get("doc_type")
        status_f = request.query_params.get("status")
        product  = request.query_params.get("product")

        if doc_type:
            qs = qs.filter(doc_type=doc_type)
        if status_f:
            qs = qs.filter(verification_status=status_f)
        if product:
            qs = qs.filter(product__id=product)

        serializer = ComplianceDocumentListSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        serializer = ComplianceDocumentUploadSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        doc = serializer.save()

        return Response(
            ComplianceDocumentDetailSerializer(doc, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


# ──────────────────────────────────────────────────
# DOCUMENT DETAIL
# ──────────────────────────────────────────────────

class ComplianceDocumentDetailView(APIView):
    """
    GET    /api/v1/compliance/<id>/   → document detail
    PATCH  /api/v1/compliance/<id>/   → update title / notes
    DELETE /api/v1/compliance/<id>/   → delete document
    """
    permission_classes = [IsAuthenticated, IsApprovedPartner]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def _get_document(self, request, pk):
        try:
            return ComplianceDocument.objects.get(pk=pk, brand=request.user.profile)
        except ComplianceDocument.DoesNotExist:
            return None

    def get(self, request, pk):
        doc = self._get_document(request, pk)
        if not doc:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ComplianceDocumentDetailSerializer(doc, context={"request": request})
        return Response(serializer.data)

    def patch(self, request, pk):
        doc = self._get_document(request, pk)
        if not doc:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ComplianceDocumentUpdateSerializer(doc, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            ComplianceDocumentDetailSerializer(doc, context={"request": request}).data
        )

    def delete(self, request, pk):
        doc = self._get_document(request, pk)
        if not doc:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
        doc.file.delete(save=False)   # remove file from storage
        doc.delete()
        return Response({"message": "Document deleted."}, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────────
# VERIFY / REJECT  (Admin action)
# ──────────────────────────────────────────────────

class VerifyDocumentView(GenericAPIView):
    """
    POST /api/v1/compliance/<id>/verify/

    Body:
      { "action": "verify" }
      { "action": "reject", "reason": "Missing ingredient list" }

    Only staff / admin users can call this.
    Product compliance_status + brand health score recalculated automatically.
    """
    serializer_class   = VerifyDocumentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {"error": "Only admin users can verify documents."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            doc = ComplianceDocument.objects.get(pk=pk)
        except ComplianceDocument.DoesNotExist:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]
        reason = serializer.validated_data.get("reason", "")

        if action == "verify":
            verify_document(doc, request.user)
            msg = "Document verified successfully."
        else:
            reject_document(doc, request.user, reason)
            msg = "Document rejected."

        return Response(
            {
                "message": msg,
                "document_id": str(doc.id),
                "verification_status": doc.verification_status,
            },
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────────
# COMPLIANCE HEALTH SCORE
# ──────────────────────────────────────────────────

class ComplianceScoreView(APIView):
    """
    GET /api/v1/compliance/score/

    Returns brand-level compliance health score.
    Figma: My Products header — Compliance Health Score (60%).
    {
        "total_products": 5,
        "approved": 3,
        "pending": 1,
        "rejected": 1,
        "health_score": 60,
        "total_docs": 8,
        "verified_docs": 5,
        "pending_docs": 2,
        "failed_docs": 1
    }
    """
    permission_classes = [IsAuthenticated, IsApprovedPartner]

    def get(self, request):
        brand   = request.user.profile
        summary = get_brand_compliance_summary(brand)
        serializer = ComplianceScoreSerializer(summary)
        return Response(serializer.data)


# ──────────────────────────────────────────────────
# DOCUMENTS BY PRODUCT
# ──────────────────────────────────────────────────

class ProductDocumentsView(APIView):
    """
    GET /api/v1/compliance/product/<product_id>/

    All compliance documents linked to a specific product.
    Useful for the Product Detail modal — shows which docs are attached.
    """
    permission_classes = [IsAuthenticated, IsApprovedPartner]

    def get(self, request, product_id):
        brand = request.user.profile
        docs  = ComplianceDocument.objects.filter(
            brand=brand, product__id=product_id
        ).select_related("product")

        serializer = ComplianceDocumentListSerializer(
            docs, many=True, context={"request": request}
        )
        return Response(serializer.data)