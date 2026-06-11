from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.users.permissions import IsApprovedPartner
from apps.products.models import Product
from .models import ChemistChatSession, ChemistMessage, ForecastRecord
from .serializers import (
    ChemistAskSerializer,
    ChemistResponseSerializer,
    ChemistSessionSerializer,
    ChemistMessageSerializer,
    ProductForecastDropdownSerializer,
    ForecastGenerateSerializer,
    ForecastRecordSerializer,
    ForecastListSerializer,
)

PERMS = [IsAuthenticated, IsApprovedPartner]


# ──────────────────────────────────────────────────
# CHEMIST BOT
# ──────────────────────────────────────────────────

class ChemistAskView(GenericAPIView):
    """
    POST /api/v1/ai/chemist/ask/

    Figma: Chemist Bot screen — send message, get response.

    Flow:
      1. Get or create a ChemistChatSession for this brand
      2. Load full message history from DB
      3. Call ai/chatbot.py → get_chemist_response(message, history)
      4. Save user message + bot response to DB
      5. Return both messages + suggestion chips

    AI Integration:
        from ai.chatbot import get_chemist_response, SUGGESTION_CHIPS
    """
    serializer_class   = ChemistAskSerializer
    permission_classes = PERMS

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        brand      = request.user.profile
        message    = serializer.validated_data["message"]
        session_id = serializer.validated_data.get("session_id")

        # ── Get or create session ──────────────────
        if session_id:
            try:
                session = ChemistChatSession.objects.get(id=session_id, brand=brand)
            except ChemistChatSession.DoesNotExist:
                session = ChemistChatSession.objects.create(brand=brand)
        else:
            session = ChemistChatSession.objects.create(brand=brand)

        # ── Build chat history for Gemini ──────────
        # ai/chatbot.py expects: [{"role": "user"/"model", "content": str}]
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in session.messages.all()
        ]

        # ── Call AI chatbot ────────────────────────
        try:
            from ai.chatbot import get_chemist_response, SUGGESTION_CHIPS
            bot_reply   = get_chemist_response(message, history)
            suggestions = SUGGESTION_CHIPS
        except ImportError:
            bot_reply   = "AI module is not connected yet. Please add ai/chatbot.py."
            suggestions = []
        except Exception as e:
            return Response(
                {"error": f"AI error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ── Save to DB ─────────────────────────────
        user_msg = ChemistMessage.objects.create(
            session=session, role="user", content=message
        )
        bot_msg = ChemistMessage.objects.create(
            session=session, role="model", content=bot_reply
        )

        return Response(
            {
                "session_id":   str(session.id),
                "user_message": ChemistMessageSerializer(user_msg).data,
                "bot_response": ChemistMessageSerializer(bot_msg).data,
                "suggestions":  suggestions,
            },
            status=status.HTTP_201_CREATED,
        )


class ChemistHistoryView(APIView):
    """
    GET /api/v1/ai/chemist/history/
    Returns the latest session's full chat history.
    Figma: Chemist Bot — previous conversation shown on open.
    """
    permission_classes = PERMS

    def get(self, request):
        brand = request.user.profile
        session = ChemistChatSession.objects.filter(brand=brand).first()
        if not session:
            return Response({"session_id": None, "messages": []})
        return Response(ChemistSessionSerializer(session).data)


class ChemistNewSessionView(APIView):
    """
    POST /api/v1/ai/chemist/new-session/
    Starts a fresh chat session.
    Figma: 'New Chat' or clear button.
    """
    permission_classes = PERMS

    def post(self, request):
        brand   = request.user.profile
        session = ChemistChatSession.objects.create(brand=brand)
        return Response(
            {"session_id": str(session.id), "message": "New session started."},
            status=status.HTTP_201_CREATED,
        )


# ──────────────────────────────────────────────────
# GENERATE FORECAST
# ──────────────────────────────────────────────────

class ForecastProductListView(APIView):
    """
    GET /api/v1/ai/forecast/products/
    Figma: Generate Forecast — Select Product dropdown.
    Returns brand's active products.
    """
    permission_classes = PERMS

    def get(self, request):
        products = Product.objects.filter(
            brand=request.user.profile, is_active=True
        )
        return Response(
            ProductForecastDropdownSerializer(products, many=True).data
        )


class ForecastGenerateView(GenericAPIView):
    """
    POST /api/v1/ai/forecast/generate/

    Figma: 'Generate AI Forecast' button →
           Shows: accuracy %, trend chart, risk indicators.

    Flow:
      1. Get product → fetch latest batch details
      2. Call ai/generate_forecast.py → generate_forecast()
      3. Save ForecastRecord to DB
      4. Return ForecastRecordSerializer

    AI Integration:
        from ai.generate_forecast import generate_forecast
    """
    serializer_class   = ForecastGenerateSerializer
    permission_classes = PERMS
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        product = serializer.context["product"]
        brand   = request.user.profile

        # ── Fetch batch data for AI ────────────────
        latest_batch = product.batches.order_by("-manufacturing_date").first()
        quantity     = latest_batch.quantity             if latest_batch else 500
        mfg_date     = str(latest_batch.manufacturing_date) if latest_batch else "2026-01-01"
        expiry_date  = str(latest_batch.expiry_date)     if latest_batch else "2028-01-01"
        retail_price = float(product.retail_price)       if product.retail_price else 10.0

        # ── Optional product image ─────────────────
        image_bytes = None
        image_mime  = "image/jpeg"
        if product.image:
            try:
                with product.image.open("rb") as f:
                    image_bytes = f.read()
                if product.image.name.endswith(".png"):
                    image_mime = "image/png"
            except Exception:
                pass

        # ── Call AI forecast engine ────────────────
        try:
            from ai.generate_forecast import generate_forecast

            result = generate_forecast(
                product_name = product.name,
                category     = product.get_category_display(),
                pack_size    = product.get_pack_size_display(),
                retail_price = retail_price,
                quantity     = quantity,
                mfg_date     = mfg_date,
                expiry_date  = expiry_date,
                image_bytes  = image_bytes,
                image_mime   = image_mime,
            )
        except ImportError:
            # Fallback if AI module not connected
            result = {
                "accuracy":          88.0,
                "quarter":           "Q3 2026",
                "trend_points":      [40,45,50,55,60,62,65,68,70,72],
                "inventory_risk":    "Low",
                "demand_volatility": "Medium",
                "supply_chain_risk": "Low",
                "summary":           "AI module not connected. Sample forecast data.",
            }
        except Exception as e:
            return Response(
                {"error": f"Forecast generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ── Save to DB ─────────────────────────────
        forecast = ForecastRecord.objects.create(
            brand             = brand,
            product           = product,
            accuracy          = result["accuracy"],
            quarter           = result["quarter"],
            trend_points      = result["trend_points"],
            inventory_risk    = result["inventory_risk"],
            demand_volatility = result["demand_volatility"],
            supply_chain_risk = result["supply_chain_risk"],
            summary           = result.get("summary", ""),
        )

        return Response(
            ForecastRecordSerializer(forecast).data,
            status=status.HTTP_201_CREATED,
        )


class ForecastListView(APIView):
    """
    GET /api/v1/ai/forecast/
    List all saved forecasts for the brand.
    Figma: Forecast history / saved forecasts.
    """
    permission_classes = PERMS

    def get(self, request):
        forecasts = ForecastRecord.objects.filter(brand=request.user.profile)
        return Response(ForecastListSerializer(forecasts, many=True).data)


class ForecastDetailView(APIView):
    """
    GET    /api/v1/ai/forecast/<uuid:pk>/   → full forecast detail
    DELETE /api/v1/ai/forecast/<uuid:pk>/   → delete forecast
    """
    permission_classes = PERMS

    def _get(self, request, pk):
        try:
            return ForecastRecord.objects.get(pk=pk, brand=request.user.profile)
        except ForecastRecord.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self._get(request, pk)
        if not obj:
            return Response({"error": "Forecast not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ForecastRecordSerializer(obj).data)

    def delete(self, request, pk):
        obj = self._get(request, pk)
        if not obj:
            return Response({"error": "Forecast not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({"message": "Forecast deleted."}, status=status.HTTP_200_OK)