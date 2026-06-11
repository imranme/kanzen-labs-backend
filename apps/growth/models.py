import uuid
from django.db import models
from apps.users.models import PartnerProfile
from apps.products.models import Product


# ──────────────────────────────────────────────────
# MARGIN CALCULATOR
# Figma: Growth Engine → Margin tab
# ──────────────────────────────────────────────────
class MarginCalculation(models.Model):
    """
    Stores each margin calculation result.
    """
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand            = models.ForeignKey(
        PartnerProfile, on_delete=models.CASCADE, related_name="margin_calculations"
    )
    product          = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="margin_calculations"
    )

    # ── Inputs ──
    production_cost  = models.DecimalField(max_digits=10, decimal_places=2)
    packaging_cost   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    marketing_cost   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    retail_price     = models.DecimalField(max_digits=10, decimal_places=2)

    # ── Calculated Output ──
    total_cost       = models.DecimalField(max_digits=10, decimal_places=2)
    profit_per_unit  = models.DecimalField(max_digits=10, decimal_places=2)
    margin_pct       = models.DecimalField(max_digits=5,  decimal_places=2)

    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "growth"  # 👈 'apps.growth' বদলে শুধু 'growth' করা হলো ভাই
        db_table  = "growth_margin_calculation"
        ordering  = ["-created_at"]

    def __str__(self):
        return f"{self.brand.brand_name} — {self.margin_pct}% margin"


# ──────────────────────────────────────────────────
# COG BREAKDOWN SIMULATOR
# Figma: Growth Engine → COG Sim tab
# ──────────────────────────────────────────────────
class COGSimulation(models.Model):
    """
    Simulates Cost of Goods at different MOQ tiers.
    """
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand           = models.ForeignKey(
        PartnerProfile, on_delete=models.CASCADE, related_name="cog_simulations"
    )
    product         = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="cog_simulations"
    )

    # ── Inputs ──
    base_cost       = models.DecimalField(max_digits=10, decimal_places=2)
    retail_price    = models.DecimalField(max_digits=10, decimal_places=2)

    # ── Tiers output (JSON) ──
    tiers           = models.JSONField(default=list)

    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "growth"  # 👈 জ্যাঙ্গো ট্র্যাকিং সলিড করার জন্য ফিক্স করা হলো
        db_table  = "growth_cog_simulation"
        ordering  = ["-created_at"]

    def __str__(self):
        return f"{self.brand.brand_name} — COG Simulation"


# ──────────────────────────────────────────────────
# FORMULATION LAB — Saved Formulas
# ──────────────────────────────────────────────────
class SavedFormulation(models.Model):
    """
    Stores AI-generated formulations from Formulation Lab.
    """
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand           = models.ForeignKey(
        PartnerProfile, on_delete=models.CASCADE, related_name="saved_formulations"
    )

    # ── AI Inputs ──
    skin_type       = models.CharField(max_length=100, blank=True)
    concern         = models.CharField(max_length=100, blank=True)
    product_format  = models.CharField(max_length=50, blank=True)

    # ── AI Output ──
    formula_name    = models.CharField(max_length=255)
    base_formula    = models.JSONField(default=list)
    active_stack    = models.JSONField(default=list)
    est_moq         = models.CharField(max_length=50,  blank=True)
    cost_per_unit   = models.CharField(max_length=50,  blank=True)
    retail_range    = models.CharField(max_length=50,  blank=True)
    key_benefits    = models.JSONField(default=list)
    ph_range        = models.CharField(max_length=20,  blank=True)
    notes           = models.TextField(blank=True)

    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "growth"  # 👈 ডুপ্লিকেট কেটে একদম ক্লিন ফিক্সড ভাই
        db_table  = "growth_saved_formulation"
        ordering  = ["-created_at"]

    def __str__(self):
        return f"{self.brand.brand_name} — {self.formula_name}"