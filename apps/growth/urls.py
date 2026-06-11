from django.urls import path
from apps.growth.views import (
    # Margin
    MarginCalculateView,
    MarginHistoryView,
    # COG
    COGSimulateView,
    # Forecasts tab
    ForecastsTabView,
    # Formulation Lab
    TrendingActivesView,
    FormulationGenerateView,
    FormulationSaveView,
    SavedFormulationListView,
    SavedFormulationDetailView,
)

# Mounted at: /api/v1/growth/

urlpatterns = [
    # ── Margin Calculator ─────────────────────────────────
    path("margin/",            MarginHistoryView.as_view(),     name="growth-margin-list"),
    path("margin/calculate/",  MarginCalculateView.as_view(),   name="growth-margin-calculate"),

    # ── COG Breakdown Simulator ───────────────────────────
    path("cog/simulate/",      COGSimulateView.as_view(),       name="growth-cog-simulate"),

    # ── Forecasts tab ─────────────────────────────────────
    path("forecasts/",         ForecastsTabView.as_view(),      name="growth-forecasts"),

    # ── Formulation Lab ───────────────────────────────────
    path("formulation/trending/",           TrendingActivesView.as_view(),        name="growth-trending"),
    path("formulation/generate/",           FormulationGenerateView.as_view(),    name="growth-formulation-generate"),
    path("formulation/save/",               FormulationSaveView.as_view(),        name="growth-formulation-save"),
    path("formulation/saved/",              SavedFormulationListView.as_view(),   name="growth-formulation-saved"),
    path("formulation/<uuid:pk>/",          SavedFormulationDetailView.as_view(), name="growth-formulation-detail"),
]