from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from unfold.admin import ModelAdmin, TabularInline  # <── Unfold Imports
from .models import ChemistChatSession, ChemistMessage, ForecastRecord

class ChemistMessageInline(TabularInline):  # <── TabularInline
    model           = ChemistMessage
    extra           = 0
    readonly_fields = ("role", "content", "created_at")
    can_delete      = False

@admin.register(ChemistChatSession)
class ChemistChatSessionAdmin(ModelAdmin):  # <── ModelAdmin
    list_select_related = ("brand",)
    list_display        = ("id", "brand_name", "message_count_display", "updated_at")
    search_fields       = ("brand__brand_name",)
    readonly_fields     = ("created_at", "updated_at")
    inlines             = [ChemistMessageInline]

    def brand_name(self, obj):
        return obj.brand.brand_name
    brand_name.short_description = "Brand"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(messages_count=Count("messages"))

    def message_count_display(self, obj):
        return obj.messages_count
    message_count_display.short_description = "Messages"
    message_count_display.admin_order_field = "messages_count"

@admin.register(ForecastRecord)
class ForecastRecordAdmin(ModelAdmin):
    list_select_related = ("brand", "product")
    list_display        = (
        "product_name", "brand_name", "quarter",
        "accuracy", "risk_summary", "created_at"
    )
    list_filter         = ("inventory_risk", "demand_volatility", "supply_chain_risk")
    search_fields       = ("product__name", "brand__brand_name")
    readonly_fields     = ("trend_points", "created_at")

    def product_name(self, obj):
        return obj.product.name

    def brand_name(self, obj):
        return obj.brand.brand_name
    brand_name.short_description = "Brand"

    def risk_summary(self, obj):
        colors = {"Low": "#10B981", "Medium": "#F59E0B", "High": "#EF4444"}
        
        def make_badge(label, risk_type):
            return format_html(
                '<span style="background:{};color:#fff;padding:2px 7px;'
                'border-radius:8px;font-size:11px;margin-right:4px" title="{}">{}</span>',
                colors.get(label, "#64748B"),
                risk_type,
                label
            )
            
        return (
            make_badge(obj.inventory_risk, "Inventory") +
            make_badge(obj.demand_volatility, "Demand Volatility") +
            make_badge(obj.supply_chain_risk, "Supply Chain")
        )
    risk_summary.short_description = "Risks (Inv / Dmd / Spl)"