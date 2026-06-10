from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import ComplianceDocument
from .services import verify_document, reject_document


@admin.register(ComplianceDocument)
class ComplianceDocumentAdmin(admin.ModelAdmin):
    list_display  = (
        "title", "doc_type", "brand_name", "product_name",
        "status_badge", "verified_at", "uploaded_at"
    )
    list_filter   = ("verification_status", "doc_type")
    search_fields = ("title", "brand__brand_name", "product__name")
    readonly_fields = ("uploaded_at", "updated_at", "verified_at", "verified_by")
    actions = ["approve_documents", "reject_documents"]

    def brand_name(self, obj):
        return obj.brand.brand_name
    brand_name.short_description = "Brand"

    def product_name(self, obj):
        return obj.product.name if obj.product else "—"
    product_name.short_description = "Product"

    def status_badge(self, obj):
        colors = {
            "pending":  "#F59E0B",
            "verified": "#10B981",
            "failed":   "#EF4444",
        }
        color = colors.get(obj.verification_status, "#64748B")
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:12px;">{}</span>',
            color,
            obj.get_verification_status_display(),
        )
    status_badge.short_description = "Status"

    @admin.action(description="✅ Verify selected documents")
    def approve_documents(self, request, queryset):
        count = 0
        for doc in queryset.filter(verification_status="pending"):
            verify_document(doc, request.user)
            count += 1
        self.message_user(request, f"{count} document(s) verified.")

    @admin.action(description="❌ Reject selected documents")
    def reject_documents(self, request, queryset):
        count = 0
        for doc in queryset.filter(verification_status="pending"):
            reject_document(doc, request.user, reason="Rejected by admin")
            count += 1
        self.message_user(request, f"{count} document(s) rejected.")