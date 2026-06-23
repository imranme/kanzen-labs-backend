from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin  # ── Unfold Import
from .models import GeneratedLogisticDoc

@admin.register(GeneratedLogisticDoc)
class GeneratedLogisticDocAdmin(ModelAdmin):  # ── ModelAdmin
    # ১. List View-এর জন্য (যা অলরেডি পারফেক্টলি লিখেছেন)
    list_display  = (
        "product_name", "document_type_badge",
        "destination_country", "file_size_text", "created_at"
    )
    list_filter   = ("document_type", "destination_country")
    search_fields = ("product__name", "product__sku_code")
    
    # ২. ডিটেইল পেজে কাস্টম মেথডগুলো দেখানোর জন্য readonly_fields-এ যোগ করুন
    readonly_fields = (
        "product_name", "document_type_badge", 
        "file_url", "created_at", "updated_at"
    )

    # ৩. ডিটেইল পেজে কোন কোন ফিল্ড কোন সিরিয়ালে দেখাবে তা ফিক্স করুন
    fields = (
        "product_name", 
        "document_type_badge", 
        "destination_country", 
        "file_size_text", 
        "file_url", 
        "created_at", 
        "updated_at"
    )

    # ── কাস্টম মেথডসমূহ ──
    def product_name(self, obj):
        if obj.product:
            return f"{obj.product.name} ({obj.product.sku_code})"
        return "-"
    product_name.short_description = "Product"

    def document_type_badge(self, obj):
        colors = {
            "commercial_invoice":     "#2563EB",
            "packing_list":           "#059669",
            "certificate_of_origin": "#D97706",
            "export_declaration":    "#7C3AED",
        }
        color = colors.get(obj.document_type, "#64748B")
        return format_html(
            '<span style="background:{};color:#fff;padding:4px 12px;'
            'border-radius:12px;font-size:12px;font-weight:500;">{}</span>',
            color,
            obj.get_document_type_display(),
        )
    document_type_badge.short_description = "Document Type"