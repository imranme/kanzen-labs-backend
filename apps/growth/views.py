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




# dhasbord 
# ──────────────────────────────────────────────────
# DASHBOARD SUMMARY VIEW
# Figma: Home Page — সব data এক API তে
# apps/growth/views.py এ এই class টা add করো
# ──────────────────────────────────────────────────

class DashboardSummaryView(APIView):
    """
    GET /api/v1/growth/dashboard/

    Figma: Home Page — একটা call এ সব data
    {
      brand_name, tier, is_verified,
      margin_health_score,
      active_products, compliance_score,
      forecast_health, pending_launches,
      revenue_trend_pct, recent_activity
    }
    """
    permission_classes = PERMS

    def get(self, request):
        brand = request.user.profile

        # ── 1. Products ───────────────────────────
        from apps.products.models import Product
        products      = Product.objects.filter(brand=brand, is_active=True)
        active_count  = products.count()
        pending_count = products.filter(
            compliance_status="pending"
        ).count()

        # ── 2. Compliance Score ───────────────────
        from apps.compliance.services import get_brand_compliance_summary
        compliance    = get_brand_compliance_summary(brand)
        comp_score    = compliance["health_score"]
        comp_pending  = compliance["pending_docs"]

        # ── 3. Margin Health Score ────────────────
        latest_margin = MarginCalculation.objects.filter(
            brand=brand
        ).first()
        margin_score  = float(latest_margin.margin_pct) if latest_margin else 0

        # ── 4. Forecast Health ────────────────────
        from apps.ai_engine.models import ForecastRecord
        forecasts     = ForecastRecord.objects.filter(brand=brand)
        forecast_count= forecasts.count()
        if forecast_count == 0:
            forecast_health = "No Forecasts"
        else:
            avg_acc = sum(float(f.accuracy) for f in forecasts) / forecast_count
            forecast_health = "Excellent" if avg_acc >= 90 else "Good" if avg_acc >= 75 else "Fair"

        # ── 5. Revenue Trend ──────────────────────
        margins       = MarginCalculation.objects.filter(brand=brand).order_by("-created_at")[:12]
        revenue_trend = 12.4   # placeholder — connect real revenue data later

        # ── 6. Recent Activity ────────────────────
        recent_activity = _build_activity(brand)

        return Response({
            # Brand
            "brand_name":          brand.brand_name,
            "brand_tagline":       brand.brand_tagline,
            "tier":                brand.tier,
            "is_verified":         brand.is_verified,
            "trust_score":         brand.trust_score,

            # KPIs
            "active_products":     active_count,
            "compliance_score":    comp_score,
            "compliance_pending":  comp_pending,
            "margin_health_score": round(margin_score, 1),
            "forecast_health":     forecast_health,
            "forecast_count":      forecast_count,
            "pending_launches":    pending_count,

            # Revenue
            "revenue_trend_pct":   revenue_trend,

            # Recent Activity
            "recent_activity":     recent_activity,

            # Quick Actions available
            "quick_actions": [
                {"key": "upload_product",     "label": "Upload Product",     "url": "/api/v1/products/"},
                {"key": "generate_forecast",  "label": "Generate Forecast",  "url": "/api/v1/ai/forecast/generate/"},
                {"key": "chemist_bot",        "label": "Chemist Bot",        "url": "/api/v1/ai/chemist/ask/"},
                {"key": "logistic_docs",      "label": "Logistic docs",      "url": "/api/v1/logistics/generate-document/"},
                {"key": "join_meeting",       "label": "Join Meeting",       "url": "/api/v1/meetings/instant/"},
            ]
        })


def _build_activity(brand):
    """
    Builds recent activity feed from multiple sources.
    Figma: Recent Activity section on Home Page.
    """
    activity = []

    # Compliance docs recently verified
    from apps.compliance.models import ComplianceDocument
    recent_docs = ComplianceDocument.objects.filter(
        brand=brand, verification_status="verified"
    ).order_by("-verified_at")[:2]
    for doc in recent_docs:
        activity.append({
            "type":        "compliance",
            "icon":        "check",
            "color":       "green",
            "title":       f"{doc.get_doc_type_display()} document approved",
            "subtitle":    doc.product.name if doc.product else doc.title,
            "time":        doc.verified_at,
        })

    # Recent forecasts
    from apps.ai_engine.models import ForecastRecord
    recent_forecasts = ForecastRecord.objects.filter(brand=brand).order_by("-created_at")[:1]
    for f in recent_forecasts:
        risk = f.inventory_risk
        activity.append({
            "type":     "forecast",
            "icon":     "warning" if risk == "High" else "chart",
            "color":    "orange" if risk == "High" else "teal",
            "title":    f"Forecast alert: inventory {risk.lower()}" if risk == "High" else "Forecast generated",
            "subtitle": f"{f.product.name} — {f.quarter}",
            "time":     f.created_at,
        })

    # Recent batch uploads
    from apps.products.models import BatchRecord
    recent_batches = BatchRecord.objects.filter(
        product__brand=brand
    ).order_by("-uploaded_at")[:1]
    for b in recent_batches:
        activity.append({
            "type":     "product",
            "icon":     "upload",
            "color":    "blue",
            "title":    "New batch record uploaded",
            "subtitle": f"Batch #{b.batch_code} — {b.product.name}",
            "time":     b.uploaded_at,
        })

    # Sort by time descending
    activity.sort(key=lambda x: x["time"], reverse=True)

    # Format time to string
    from django.utils import timezone
    now = timezone.now()
    for item in activity:
        diff = now - item["time"]
        hours = int(diff.total_seconds() / 3600)
        if hours < 1:
            item["time_ago"] = "Just now"
        elif hours < 24:
            item["time_ago"] = f"{hours}h ago"
        else:
            item["time_ago"] = f"{diff.days}d ago"
        del item["time"]

    return activity[:5]  # max 5 items