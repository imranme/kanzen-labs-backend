from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin  # <── Unfold Import
from apps.growth.models import MarginCalculation, COGSimulation, SavedFormulation

@admin.register(MarginCalculation)
class MarginCalculationAdmin(ModelAdmin):  # <── ModelAdmin
    list_display  = ("brand_name", "product_name", "margin_badge",
                     "profit_per_unit", "retail_price", "created_at")
    list_filter   = ("created_at",)
    search_fields = ("brand__brand_name", "product__name")
    readonly_fields = ("total_cost", "profit_per_unit", "margin_pct", "created_at")

    def brand_name(self, obj):
        return obj.brand.brand_name
    brand_name.short_description = "Brand"

    def product_name(self, obj):
        return obj.product.name if obj.product else "—"
    product_name.short_description = "Product"

    def margin_badge(self, obj):
        m = float(obj.margin_pct)
        color = "#10B981" if m >= 50 else "#F59E0B" if m >= 30 else "#EF4444"
        label = "Healthy" if m >= 50 else "Average" if m >= 30 else "Low"
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:12px;">{} — {}%</span>',
            color, label, obj.margin_pct
        )
    margin_badge.short_description = "Margin"

@admin.register(COGSimulation)
class COGSimulationAdmin(ModelAdmin):  # <── ModelAdmin
    list_display  = ("brand_name", "product_name", "base_cost",
                     "retail_price", "created_at")
    search_fields = ("brand__brand_name", "product__name")
    readonly_fields = ("tiers", "created_at")

    def brand_name(self, obj):
        return obj.brand.brand_name
    brand_name.short_description = "Brand"

    def product_name(self, obj):
        return obj.product.name if obj.product else "—"
    product_name.short_description = "Product"

@admin.register(SavedFormulation)
class SavedFormulationAdmin(ModelAdmin):  # <── ModelAdmin
    list_display  = ("formula_name", "brand_name", "product_format",
                     "skin_type", "concern", "created_at")
    list_filter   = ("product_format",)
    search_fields = ("formula_name", "brand__brand_name", "skin_type", "concern")
    readonly_fields = ("base_formula", "active_stack", "key_benefits", "created_at")

    def brand_name(self, obj):
        return obj.brand.brand_name
    brand_name.short_description = "Brand"