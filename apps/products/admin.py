from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline  # <── Unfold Imports
from .models import Product, BatchRecord

class BatchRecordInline(TabularInline):  # <── TabularInline
    model = BatchRecord
    extra = 1
    fields = ["batch_code", "quantity", "manufacturing_date", "expiry_date", "is_expired"]
    readonly_fields = ["is_expired"]

@admin.register(Product)
class ProductAdmin(ModelAdmin):  # <── ModelAdmin
    list_display = [
        "display_image", "name", "sku_code", "brand", 
        "category", "retail_price", "compliance_status", 
        "compliance_health_score", "is_active"
    ]
    list_filter = ["compliance_status", "category", "is_active", "brand"]
    search_fields = ["name", "sku_code", "barcode_ean"]
    list_editable = ["compliance_status", "is_active"]
    inlines = [BatchRecordInline]

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="40" height="40" style="border-radius:4px; object-fit:cover;" />', obj.image.url)
        return "No Image"
    display_image.short_description = "Img"

@admin.register(BatchRecord)
class BatchRecordAdmin(ModelAdmin):  # <── ModelAdmin
    list_display = ["batch_code", "product", "quantity", "manufacturing_date", "expiry_date", "is_expired"]
    search_fields = ["batch_code", "product__name"]