from django.urls import path
from .views import (
    ComplianceDocumentListView,
    ComplianceDocumentDetailView,
    VerifyDocumentView,
    ComplianceScoreView,
    ProductDocumentsView,
)

# Mounted at: /api/v1/compliance/

urlpatterns = [
    # ── Document CRUD ──────────────────────────────────────
    path("",                          ComplianceDocumentListView.as_view(),   name="compliance-list"),
    path("<uuid:pk>/",                ComplianceDocumentDetailView.as_view(), name="compliance-detail"),

    # ── Admin verify / reject ──────────────────────────────
    path("<uuid:pk>/verify/",         VerifyDocumentView.as_view(),           name="compliance-verify"),

    # ── Score & filters ────────────────────────────────────
    path("score/",                    ComplianceScoreView.as_view(),          name="compliance-score"),
    path("product/<uuid:product_id>/",ProductDocumentsView.as_view(),         name="compliance-by-product"),
]