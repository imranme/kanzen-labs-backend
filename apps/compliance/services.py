"""
Compliance business logic.
- Verify / reject a document
- Recalculate product compliance_status after document change
- Calculate brand-level compliance health score
"""
from django.utils import timezone
from apps.products.models import Product, ComplianceStatus


def verify_document(document, admin_user):
    """Mark a document as verified and update related product status."""
    document.verification_status = "verified"
    document.verified_at = timezone.now()
    document.verified_by = admin_user
    document.rejection_reason = ""
    document.save(update_fields=[
        "verification_status", "verified_at", "verified_by",
        "rejection_reason", "updated_at"
    ])
    if document.product:
        _recalculate_product_compliance(document.product)
    _recalculate_brand_score(document.brand)


def reject_document(document, admin_user, reason=""):
    """Mark a document as failed and update related product status."""
    document.verification_status = "failed"
    document.verified_at = timezone.now()
    document.verified_by = admin_user
    document.rejection_reason = reason
    document.save(update_fields=[
        "verification_status", "verified_at", "verified_by",
        "rejection_reason", "updated_at"
    ])
    if document.product:
        _recalculate_product_compliance(document.product)
    _recalculate_brand_score(document.brand)


def _recalculate_product_compliance(product):
    """
    Recalculates a single product's compliance_status based on its documents:
    - All verified   → approved
    - Any failed     → rejected
    - Otherwise      → pending
    """
    from .models import ComplianceDocument, VerificationStatus

    docs = ComplianceDocument.objects.filter(product=product)

    if not docs.exists():
        product.compliance_status = ComplianceStatus.PENDING
    elif docs.filter(verification_status=VerificationStatus.FAILED).exists():
        product.compliance_status = ComplianceStatus.REJECTED
    elif docs.filter(verification_status=VerificationStatus.PENDING).exists():
        product.compliance_status = ComplianceStatus.PENDING
    else:
        product.compliance_status = ComplianceStatus.APPROVED

    product.save(update_fields=["compliance_status", "updated_at"])


def _recalculate_brand_score(brand):
    """
    Recalculates and saves the compliance_health_score on every product
    in the brand, then returns the brand-wide percentage.

    Score = (approved_products / total_products) * 100
    """
    products = Product.objects.filter(brand=brand, is_active=True)
    total    = products.count()

    if total == 0:
        return 0

    approved = products.filter(compliance_status=ComplianceStatus.APPROVED).count()
    score    = int((approved / total) * 100)

    # Store per-product score too (same value for now, can be refined per doc coverage)
    products.update(compliance_health_score=score)

    return score


def get_brand_compliance_summary(brand):
    """
    Returns a dict used by ComplianceScoreView.
    {
        total_products, approved, pending, rejected,
        health_score,
        total_docs, verified_docs, pending_docs, failed_docs
    }
    """
    from .models import ComplianceDocument, VerificationStatus

    products = Product.objects.filter(brand=brand, is_active=True)
    total    = products.count()
    approved = products.filter(compliance_status=ComplianceStatus.APPROVED).count()
    pending  = products.filter(compliance_status=ComplianceStatus.PENDING).count()
    rejected = products.filter(compliance_status=ComplianceStatus.REJECTED).count()
    score    = int((approved / total) * 100) if total else 0

    docs          = ComplianceDocument.objects.filter(brand=brand)
    total_docs    = docs.count()
    verified_docs = docs.filter(verification_status=VerificationStatus.VERIFIED).count()
    pending_docs  = docs.filter(verification_status=VerificationStatus.PENDING).count()
    failed_docs   = docs.filter(verification_status=VerificationStatus.FAILED).count()

    return {
        "total_products":  total,
        "approved":        approved,
        "pending":         pending,
        "rejected":        rejected,
        "health_score":    score,
        "total_docs":      total_docs,
        "verified_docs":   verified_docs,
        "pending_docs":    pending_docs,
        "failed_docs":     failed_docs,
    }