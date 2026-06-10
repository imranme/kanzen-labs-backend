from django.urls import path
from .views import (
    LogisticsProductListView,
    GenerateDocumentView,
    DocumentDetailView,
    DocumentListView,
)

# Mounted at: /api/v1/logistics/

urlpatterns = [
    # ── Document list ──────────────────────────────
    path("",                          DocumentListView.as_view(),          name="logistics-list"),

    # ── Product dropdown ───────────────────────────
    path("products/",                 LogisticsProductListView.as_view(),  name="logistics-products"),

    # ── Generate document ──────────────────────────
    path("generate-document/", GenerateDocumentView.as_view(), name="logistics-generate"),

    # ── Document detail / patch / delete ──────────
    path("document/<uuid:pk>/",       DocumentDetailView.as_view(),        name="logistics-detail"),
]