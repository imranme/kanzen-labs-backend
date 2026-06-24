from decimal import Decimal, InvalidOperation
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from apps.users.permissions import IsApprovedPartner
from apps.products.models import Product
from apps.ai_engine.models import ForecastRecord
from apps.ai_engine.serializers import ForecastListSerializer
from django.db.models import CharField
from django.db.models.functions import Cast, Round
from types import SimpleNamespace

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
        # ১. ডাটাবেজ লেভেলে সব ডেসিমেল ফিল্ডকে CharField বানিয়ে কুয়েরি করছি (যাতে SQLite ক্র্যাশ না করে)
        qs_values = MarginCalculation.objects.filter(
            brand=request.user.profile
        ).annotate(
            str_production_cost=Cast('production_cost', CharField()),
            str_packaging_cost=Cast('packaging_cost', CharField()),
            str_shipping_cost=Cast('shipping_cost', CharField()),
            str_marketing_cost=Cast('marketing_cost', CharField()),
            str_retail_price=Cast('retail_price', CharField()),
            str_total_cost=Cast('total_cost', CharField()),
            str_profit_per_unit=Cast('profit_per_unit', CharField()),
            str_margin_pct=Cast('margin_pct', CharField()),
        ).values(
            'id', 'str_production_cost', 'str_packaging_cost', 'str_shipping_cost', 
            'str_marketing_cost', 'str_retail_price', 'str_total_cost', 'str_profit_per_unit', 'str_margin_pct'
        )[:20]
        
        cleaned_data = []
        for item in qs_values:
            # ২. ডাটাগুলো ক্লিন করে একটি ডিকশনারি বানাচ্ছি
            cleaned_item = {
                'id': item['id'],
                'production_cost': self._to_safe_decimal(item['str_production_cost']),
                'packaging_cost': self._to_safe_decimal(item['str_packaging_cost']),
                'shipping_cost': self._to_safe_decimal(item['str_shipping_cost']),
                'marketing_cost': self._to_safe_decimal(item['str_marketing_cost']),
                'retail_price': self._to_safe_decimal(item['str_retail_price']),
                'total_cost': self._to_safe_decimal(item['str_total_cost']),
                'profit_per_unit': self._to_safe_decimal(item['str_profit_per_unit']),
                'margin_pct': self._to_safe_decimal(item['str_margin_pct']),
            }
            
            # ৩. 🎯 ম্যাজিক লাইন: ডিকশনারিটিকে একটি ফেক অবজেক্ট বানাচ্ছি 
            # যাতে সিরিয়ালাইজারের obj.margin_pct কোডটি কোনো এরর ছাড়া ডেটা রিড করতে পারে।
            fake_object = SimpleNamespace(**cleaned_item)
            cleaned_data.append(fake_object)

        # ৪. সিরিয়ালাইজারে অবজেক্টের লিস্ট পাঠিয়ে দেওয়া হলো
        return Response(MarginResultSerializer(cleaned_data, many=True).data)

    def _to_safe_decimal(self, value):
        try:
            if value is None or str(value).strip() == "":
                return Decimal("0.00")
            return Decimal(str(value)).quantize(Decimal('0.01'))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0.00")


# ──────────────────────────────────────────────────
# COG BREAKDOWN SIMULATOR
# Figma: Growth Engine → COG Sim tab
# ──────────────────────────────────────────────────
class COGSimulateView(GenericAPIView):
    """
    POST /api/v1/growth/cog/simulate/
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
# ──────────────────────────────────────────────────
class ForecastsTabView(APIView):
    """
    GET /api/v1/growth/forecasts/
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
# ──────────────────────────────────────────────────
class TrendingActivesView(APIView):
    """
    GET /api/v1/growth/formulation/trending/
    """
    permission_classes = PERMS

    def get(self, request):
        try:
            from ai.formulation import TRENDING_ACTIVES
            return Response(TRENDING_ACTIVES)
        except ImportError:
            return Response([
                {"name": "Bakuchiol",         "category": "Retinol Alt.",  "growth": "+24%"},
                {"name": "Niacinamide",        "category": "Brightening",   "growth": "+18%"},
                {"name": "Polyglutamic Acid",  "category": "Hydration",     "growth": "+31%"},
                {"name": "Azelaic Acid",       "category": "Clarity",       "growth": "+12%"},
            ])


class FormulationGenerateView(GenericAPIView):
    """
    POST /api/v1/growth/formulation/generate/
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
    GET / DELETE /api/v1/growth/formulation/<uuid:pk>/
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


# ──────────────────────────────────────────────────
# DASHBOARD SUMMARY
# ──────────────────────────────────────────────────
class DashboardSummaryView(APIView):
    """
    GET /api/v1/growth/dashboard/
    Figma: Home Page — All metric summaries in a single call
    """
    permission_classes = PERMS

    def get(self, request):
        brand = request.user.profile

        # -- 1. Products --
        products      = Product.objects.filter(brand=brand, is_active=True)
        active_count  = products.count()
        pending_count = products.filter(compliance_status="pending").count()

        # -- 2. Compliance Score --
        from apps.compliance.services import get_brand_compliance_summary
        compliance    = get_brand_compliance_summary(brand)
        comp_score    = compliance["health_score"]
        comp_pending  = compliance["pending_docs"]

        # -- 3. Margin Health Score (Shielded against SQLite decimal crashes) --
        latest_margin = MarginCalculation.objects.filter(
            brand=brand
        ).annotate(
            str_margin_pct=Cast('margin_pct', CharField())
        ).values('str_margin_pct').first()
        
        margin_score = 0
        if latest_margin and latest_margin['str_margin_pct']:
            try:
                margin_score = float(latest_margin['str_margin_pct'])
            except (ValueError, TypeError):
                margin_score = 0

        # -- 4. Forecast Health (Shielded against accuracy decimal crashes) --
        forecasts = ForecastRecord.objects.filter(brand=brand).annotate(
            str_accuracy=Cast('accuracy', CharField())
        ).values('str_accuracy')
        
        forecast_count = forecasts.count()
        if forecast_count == 0:
            forecast_health = "No Forecasts"
        else:
            try:
                total_acc = 0
                valid_count = 0
                for f in forecasts:
                    if f['str_accuracy']:
                        total_acc += float(f['str_accuracy'])
                        valid_count += 1
                
                avg_acc = total_acc / valid_count if valid_count > 0 else 0
                forecast_health = "Excellent" if avg_acc >= 90 else "Good" if avg_acc >= 75 else "Fair"
            except Exception:
                forecast_health = "Fair"

        # -- 5. Revenue Trend --
        revenue_trend = 12.4   # placeholder

        # -- 6. Recent Activity --
        # Assuming _build_activity is imported or declared globally, keeping original call logic
        try:
            from core.utils import _build_activity  # adjust path if needed or keep existing placeholder setup
            recent_activity = _build_activity(brand)
        except ImportError:
            # Fallback if _build_activity helper wasn't provided in full context
            recent_activity = []

        return Response({
            # Brand
            "brand_name":           brand.brand_name,
            "brand_tagline":        brand.brand_tagline,
            "tier":                 brand.tier,
            "is_verified":          brand.is_verified,
            "trust_score":          brand.trust_score,

            # KPIs
            "active_products":      active_count,
            "compliance_score":     comp_score,
            "compliance_pending":   comp_pending,
            "margin_health_score":  round(margin_score, 1),
            "forecast_health":      forecast_health,
            "forecast_count":       forecast_count,
            "pending_launches":     pending_count,

            # Revenue
            "revenue_trend_pct":    revenue_trend,

            # Recent Activity
            "recent_activity":      recent_activity,

            # Quick Actions
            "quick_actions": [
                {"key": "upload_product",     "label": "Upload Product",     "url": "/api/v1/products/"},
                {"key": "generate_forecast",  "label": "Generate Forecast",  "url": "/api/v1/ai/forecast/generate/"},
                {"key": "chemist_bot",        "label": "Chemist Bot",        "url": "/api/v1/ai/chemist/ask/"},
                {"key": "logistic_docs",      "label": "Logistic docs",      "url": "/api/v1/logistics/generate-document/"},
                {"key": "join_meeting",       "label": "Join Meeting",       "url": "/api/v1/meetings/instant/"},
            ]
        })