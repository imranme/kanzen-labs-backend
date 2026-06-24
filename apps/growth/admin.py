from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from apps.growth.models import MarginCalculation, COGSimulation, SavedFormulation
from django.db.models import Value, CharField
from decimal import Decimal, InvalidOperation

@admin.register(MarginCalculation)
class MarginCalculationAdmin(ModelAdmin):
    # এখানে আমরা ডাটাবেজের অরিজিনাল ফিল্ডগুলো সরাসরি list_display-তে রাখব না, 
    # তার বদলে কাস্টম মেথড দিয়ে সেফলি দেখাব।
    list_display  = ("brand_name", "product_name", "margin_badge",
                     "safe_profit_per_unit", "safe_retail_price", "created_at")
    list_filter   = ("created_at",)
    search_fields = ("brand__brand_name", "product__name")
    
    # এরর এড়াতে অরিজিনাল ডেসিমেল ফিল্ডগুলো অ্যাডমিন চেঞ্জলিস্টের কুয়েরি থেকে ডিফার (Defer) করে দিচ্ছি
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # এই ফিল্ডগুলো জ্যাঙ্গোকে রিড করতে মানা করছি যাতেOperations.py ক্র্যাশ না করে
        return qs.defer("margin_pct", "profit_per_unit", "total_cost", "retail_price")

    def brand_name(self, obj):
        return obj.brand.brand_name if obj.brand else "—"
    brand_name.short_description = "Brand"

    def product_name(self, obj):
        return obj.product.name if obj.product else "—"
    product_name.short_description = "Product"

    # ডাটাবেজ থেকে অরিজিনাল ভ্যালু সরাসরি পাইথনে তুলে ট্রাই-ক্যাচ দিয়ে হ্যান্ডেল করছি
    def _get_cleaned_decimal(self, instance, field_name):
        try:
            # ডিফার করার পর ভ্যালু রিড করতে গেলে জ্যাঙ্গো প্রতি অবজেক্টের জন্য কাস্টম কুয়েরি করবে
            # এবং আমরা কাঁচা ভ্যালুটাকে স্ট্রিং হিসেবে ধরে নিয়ে পাইথনে কনভার্ট করব
            raw_val = getattr(instance, field_name)
            if raw_val is None:
                return Decimal("0.00")
            return Decimal(str(raw_val))
        except (InvalidOperation, ValueError, TypeError, Exception):
            return Decimal("0.00")

    def safe_profit_per_unit(self, obj):
        return f"${self._get_cleaned_decimal(obj, 'profit_per_unit'):.2f}"
    safe_profit_per_unit.short_description = "Profit / Unit"

    def safe_retail_price(self, obj):
        return f"${self._get_cleaned_decimal(obj, 'retail_price'):.2f}"
    safe_retail_price.short_description = "Retail Price"

    def margin_badge(self, obj):
        margin_val = self._get_cleaned_decimal(obj, 'margin_pct')
        m_round = float(margin_val)
            
        color = "#10B981" if m_round >= 50 else "#F59E0B" if m_round >= 30 else "#EF4444"
        label = "Healthy" if m_round >= 50 else "Average" if m_round >= 30 else "Low"
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:12px;">{} — {}%</span>',
            color, label, f"{m_round:.2f}"
        )
    margin_badge.short_description = "Margin"


@admin.register(COGSimulation)
class COGSimulationAdmin(ModelAdmin):
    list_display  = ("brand_name", "product_name", "safe_base_cost",
                     "safe_retail_price", "created_at")
    search_fields = ("brand__brand_name", "product__name")

    def get_queryset(self, request):
        return super().get_queryset(request).defer("base_cost", "retail_price")

    def brand_name(self, obj):
        return obj.brand.brand_name if obj.brand else "—"
    brand_name.short_description = "Brand"

    def product_name(self, obj):
        return obj.product.name if obj.product else "—"
    product_name.short_description = "Product"

    def safe_base_cost(self, obj):
        try:
            return f"${Decimal(str(obj.base_cost)):.2f}"
        except:
            return "$0.00"
    safe_base_cost.short_description = "Base Cost"

    def safe_retail_price(self, obj):
        try:
            return f"${Decimal(str(obj.retail_price)):.2f}"
        except:
            return "$0.00"
    safe_retail_price.short_description = "Retail Price"


@admin.register(SavedFormulation)
class SavedFormulationAdmin(ModelAdmin):
    list_display  = ("formula_name", "brand_name", "product_format",
                     "skin_type", "concern", "created_at")
    list_filter   = ("product_format",)
    search_fields = ("formula_name", "brand__brand_name", "skin_type", "concern")
    readonly_fields = ("base_formula", "active_stack", "key_benefits", "created_at")

    def brand_name(self, obj):
        return obj.brand.brand_name if obj.brand else "—"
    brand_name.short_description = "Brand"