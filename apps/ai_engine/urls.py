from django.urls import path
from .views import (
    # Chemist Bot
    ChemistAskView,
    ChemistHistoryView,
    ChemistNewSessionView,
    # Forecast
    ForecastProductListView,
    ForecastGenerateView,
    ForecastListView,
    ForecastDetailView,
)

# Mounted at: /api/v1/ai/

urlpatterns = [

    # ── Chemist Bot ──────────────────────────────────────
    path("chemist/ask/",          ChemistAskView.as_view(),         name="ai-chemist-ask"),
    path("chemist/history/",      ChemistHistoryView.as_view(),     name="ai-chemist-history"),
    path("chemist/new-session/",  ChemistNewSessionView.as_view(),  name="ai-chemist-new-session"),

    # ── Generate Forecast ────────────────────────────────
    path("forecast/products/",    ForecastProductListView.as_view(),name="ai-forecast-products"),
    path("forecast/generate/",    ForecastGenerateView.as_view(),   name="ai-forecast-generate"),
    path("forecast/",             ForecastListView.as_view(),       name="ai-forecast-list"),
    path("forecast/<uuid:pk>/",   ForecastDetailView.as_view(),     name="ai-forecast-detail"),
]