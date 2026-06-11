import uuid
from django.db import models
from apps.users.models import PartnerProfile
from apps.products.models import Product


# ──────────────────────────────────────────────────
# CHEMIST BOT — Chat History
# ──────────────────────────────────────────────────

class ChemistChatSession(models.Model):
    """
    One chat session per brand.
    Figma: Chemist Bot screen — conversation thread.
    Stores full history so Gemini gets context each turn.
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand      = models.ForeignKey(
        PartnerProfile, on_delete=models.CASCADE, related_name="chemist_sessions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "ai_engine"
        db_table = "ai_chemist_session"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Session {self.id} — {self.brand.brand_name}"


class ChemistMessage(models.Model):
    """
    One message turn inside a ChemistChatSession.
    role = "user" or "model"  (Gemini API format)
    """
    ROLE_CHOICES = [("user", "User"), ("model", "Model")]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session    = models.ForeignKey(
        ChemistChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role       = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_chemist_message"
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"


# ──────────────────────────────────────────────────
# GENERATE FORECAST
# ──────────────────────────────────────────────────

class ForecastRecord(models.Model):
    """
    AI-generated demand forecast for a product.
    Figma: Generate Forecast screen —
      - product dropdown
      - accuracy % badge (e.g. 94.3% acc.)
      - trend chart (10 points)
      - Risk Indicator: Inventory / Demand Volatility / Supply Chain
      - Save Forecast button
    """

    RISK_CHOICES = [
        ("Low",    "Low"),
        ("Medium", "Medium"),
        ("High",   "High"),
    ]

    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand   = models.ForeignKey(
        PartnerProfile, on_delete=models.CASCADE, related_name="forecasts"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="forecasts"
    )

    # ── AI Output ─────────────────────────────────
    accuracy          = models.DecimalField(max_digits=5, decimal_places=2)   # e.g. 94.3
    quarter           = models.CharField(max_length=20)                        # e.g. "Q2 2026"
    trend_points      = models.JSONField(default=list)                         # 10 floats
    inventory_risk    = models.CharField(max_length=10, choices=RISK_CHOICES, default="Low")
    demand_volatility = models.CharField(max_length=10, choices=RISK_CHOICES, default="Low")
    supply_chain_risk = models.CharField(max_length=10, choices=RISK_CHOICES, default="Low")
    summary           = models.TextField(blank=True)

    # ── Meta ──────────────────────────────────────
    model_version = models.CharField(max_length=50, default="Kanzen Forecast v2.3")
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_forecast_record"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} — {self.quarter} ({self.accuracy}% acc.)"