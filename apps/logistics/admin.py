from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin  # <── Unfold Import
from .models import GeneratedLogisticDoc

@admin.register(GeneratedLogisticDoc)
class GeneratedLogisticDocAdmin(ModelAdmin):  # <── ModelAdmin
    list_display  = (
        "product_name", "document_type_badge",
        "destination_country", "file_size_text", "created_at"
    )
    list_filter   = ("document_type", "destination_country")
    search_fields = ("product__name", "product__sku_code")
    readonly_fields = ("created_at", "updated_at", "file_url")

    def product_name(self, obj):
        return f"{obj.product.name} ({obj.product.sku_code})"
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
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:12px;">{}</span>',
            color,
            obj.get_document_type_display(),
        )
    document_type_badge.short_description = "Document Type"