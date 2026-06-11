from decimal import Decimal
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from apps.users.permissions import IsApprovedPartner
from apps.products.models import Product
from apps.ai_engine.models import ForecastRecord
from apps.ai_engine.serializers import ForecastListSerializer

# ইম্পোর্ট এরর ফিক্স করার জন্য ফুল পাথ ব্যবহার করা হলো ভাই
from apps.growth.models import MarginCalculation, COGSimulation, SavedFormulation
from apps.growth.serializers import (
    MarginCalculateSerializer,
    MarginResultSerializer,
    COGSimulateSerializer,
    COGSimulationSerializer,
    FormulationGenerateSerializer,
    SavedFormulationSerializer,
    TrendingActiveSerializer,
)
from apps.growth.services import calculate_margin, simulate_cog_tiers

PERMS = [IsAuthenticated, IsApprovedPartner]


# ──────────────────────────────────────────────────
# MARGIN CALCULATOR
# Figma: Growth Engine → Margin tab
# ──────────────────────────────────────────────────
class MarginCalculateView(GenericAPIView):
    """
    POST /api/v1/growth/margin/calculate/
    Figma: Enter costs → see 62% margin + $26 profit/unit + Healthy
    """
    serializer_class   = MarginCalculateSerializer
    permission_classes = PERMS

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        # Optional product link
        product = None
        if d.get("product_id"):
            try:
                product = Product.objects.get(
                    id=d["product_id"], brand=request.user.profile
                )
            except Product.DoesNotExist:
                pass

        result = calculate_margin(
            production = d["production_cost"],
            packaging  = d["packaging_cost"],
            shipping   = d["shipping_cost"],
            marketing  = d["marketing_cost"],
            retail     = d["retail_price"],
        )

        calc = MarginCalculation.objects.create(
            brand           = request.user.profile,
            product         = product,
            production_cost = d["production_cost"],
            packaging_cost  = d["packaging_cost"],
            shipping_cost   = d["shipping_cost"],
            marketing_cost  = d["marketing_cost"],
            retail_price    = d["retail_price"],
            total_cost      = result["total_cost"],
            profit_per_unit = result["profit_per_unit"],
            margin_pct      = result["margin_pct"],
        )

        return Response(
            MarginResultSerializer(calc).data,
            status=status.HTTP_201_CREATED,
        )


class MarginHistoryView(APIView):
    """
    GET /api/v1/growth/margin/
    List past margin calculations for the brand.
    """
    permission_classes = PERMS

    def get(self, request):
        qs = MarginCalculation.objects.filter(brand=request.user.profile)[:20]
        return Response(MarginResultSerializer(qs, many=True).data)


# ──────────────────────────────────────────────────
# COG BREAKDOWN SIMULATOR
# Figma: Growth Engine → COG Sim tab
# ──────────────────────────────────────────────────
class COGSimulateView(GenericAPIView):
    """
    POST /api/v1/growth/cog/simulate/
    Figma: COG Sim tab →
      1k units £12,500 | 5k units £50,000 | 10k units £87,500
      Breakeven at X units
    """
    serializer_class   = COGSimulateSerializer
    permission_classes = PERMS

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        product = None
        if d.get("product_id"):
            try:
                product = Product.objects.get(
                    id=d["product_id"], brand=request.user.profile
                )
            except Product.DoesNotExist:
                pass

        tiers = simulate_cog_tiers(d["base_cost"], d["retail_price"])

        sim = COGSimulation.objects.create(
            brand        = request.user.profile,
            product      = product,
            base_cost    = d["base_cost"],
            retail_price = d["retail_price"],
            tiers        = tiers,
        )

        return Response(
            COGSimulationSerializer(sim).data,
            status=status.HTTP_201_CREATED,
        )


# ──────────────────────────────────────────────────
# FORECASTS TAB
# Figma: Growth Engine → Forecasts tab
# ──────────────────────────────────────────────────
class ForecastsTabView(APIView):
    """
    GET /api/v1/growth/forecasts/
    Figma: Growth Engine → Forecasts tab
    Shows saved forecasts: Lumina Vitamin C Serum 94.3% acc.
    Links to ai_engine.ForecastRecord.
    """
    permission_classes = PERMS

    def get(self, request):
        brand     = request.user.profile
        forecasts = ForecastRecord.objects.filter(brand=brand)

        if not forecasts.exists():
            return Response({
                "message": "No Forecasts Yet",
                "detail":  "Use Generate Forecast from the Dashboard quick actions.",
                "forecasts": [],
            })

        return Response({
            "forecasts": ForecastListSerializer(forecasts, many=True).data
        })


# ──────────────────────────────────────────────────
# FORMULATION LAB
# Figma: Formulation Lab screen
# ──────────────────────────────────────────────────
class TrendingActivesView(APIView):
    """
    GET /api/v1/growth/formulation/trending/
    Figma: Formulation Lab home — Trending Q1 2026
    Bakuchiol +24%, Niacinamide +18%, etc.
    Reads directly from ai/formulation.py TRENDING_ACTIVES.
    """
    permission_classes = PERMS

    def get(self, request):
        try:
            from ai.formulation import TRENDING_ACTIVES
            return Response(TRENDING_ACTIVES)
        except ImportError:
            # Fallback data if AI module not connected
            return Response([
                {"name": "Bakuchiol",         "category": "Retinol Alt.",  "growth": "+24%"},
                {"name": "Niacinamide",        "category": "Brightening",   "growth": "+18%"},
                {"name": "Polyglutamic Acid",  "category": "Hydration",     "growth": "+31%"},
                {"name": "Azelaic Acid",       "category": "Clarity",       "growth": "+12%"},
            ])


class FormulationGenerateView(GenericAPIView):
    """
    POST /api/v1/growth/formulation/generate/
    Figma: Formulation Lab → Generator tab → 'Generate AI Formula' button
    Calls ai/formulation.py → generate_formulation()
    Returns: BASE FORMULA + ACTIVE STACK + MOQ + Cost + Retail
    """
    serializer_class   = FormulationGenerateSerializer
    permission_classes = PERMS

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        skin_type      = d.get("skin_type", "")
        concern        = d.get("concern", "")
        product_format = d["product_format"]

        try:
            from ai.formulation import generate_formulation
            result = generate_formulation(
                skin_type      = skin_type,
                concern        = concern,
                product_format = product_format,
            )
        except ImportError:
            result = {
                "formula_name":  f"Sample {product_format} Formula",
                "base_formula":  [
                    {"ingredient": "Aqua", "percentage": 73.0},
                    {"ingredient": "Hyaluronic Acid", "percentage": 2.0},
                    {"ingredient": "Niacinamide", "percentage": 10.0},
                    {"ingredient": "Glycerin", "percentage": 5.0},
                ],
                "active_stack":  [
                    {"ingredient": "Bakuchiol", "percentage": 0.5},
                    {"ingredient": "Azelaic Acid", "percentage": 5.0},
                ],
                "est_moq":       "2,000 units",
                "cost_per_unit": "£8.90",
                "retail_range":  "£38-45",
                "key_benefits":  ["Brightening", "Hydration", "Anti-ageing"],
                "ph_range":      "5.5 - 6.0",
                "notes":         "AI module not connected. Sample data.",
            }
        except Exception as e:
            return Response(
                {"error": f"Formulation generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(result, status=status.HTTP_200_OK)


class FormulationSaveView(GenericAPIView):
    """
    POST /api/v1/growth/formulation/save/
    Figma: AI Formula Result modal → 'Save to Lab' button
    Saves generated formula to DB.
    """
    serializer_class   = SavedFormulationSerializer
    permission_classes = PERMS

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        formula = serializer.save(brand=request.user.profile)
        return Response(
            SavedFormulationSerializer(formula).data,
            status=status.HTTP_201_CREATED,
        )


class SavedFormulationListView(APIView):
    """
    GET /api/v1/growth/formulation/saved/
    Figma: Formulation Lab → Saved tab
    Shows saved formula cards: Ance Serum, formula details.
    """
    permission_classes = PERMS

    def get(self, request):
        brand = request.user.profile
        qs    = SavedFormulation.objects.filter(brand=brand)

        if not qs.exists():
            return Response({
                "message":    "No Saved Formulas",
                "detail":     "Open Generator to create and save your first formula.",
                "formulas":   [],
            })

        return Response({
            "formulas": SavedFormulationSerializer(qs, many=True).data
        })


class SavedFormulationDetailView(APIView):
    """
    GET    /api/v1/growth/formulation/<uuid:pk>/  → detail
    DELETE /api/v1/growth/formulation/<uuid:pk>/  → delete
    """
    permission_classes = PERMS

    def _get(self, request, pk):
        try:
            return SavedFormulation.objects.get(pk=pk, brand=request.user.profile)
        except SavedFormulation.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self._get(request, pk)
        if not obj:
            return Response({"error": "Formula not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(SavedFormulationSerializer(obj).data)

    def delete(self, request, pk):
        obj = self._get(request, pk)
        if not obj:
            return Response({"error": "Formula not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({"message": "Formula deleted."}, status=status.HTTP_200_OK)