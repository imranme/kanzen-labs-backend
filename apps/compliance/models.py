import uuid
from django.db import models
from apps.users.models import PartnerProfile
from apps.products.models import Product


# ──────────────────────────────────────────────────
# CHOICES
# ──────────────────────────────────────────────────

class DocType(models.TextChoices):
    COA   = "coa",   "Certificate of Analysis"
    CPSR  = "cpsr",  "Cosmetic Product Safety Report"
    MSDS  = "msds",  "Material Safety Data Sheet"
    OTHER = "other", "Other"


class VerificationStatus(models.TextChoices):
    PENDING  = "pending",  "Pending"
    VERIFIED = "verified", "Verified"
    FAILED   = "failed",   "Failed"


# ──────────────────────────────────────────────────
# COMPLIANCE DOCUMENT
# ──────────────────────────────────────────────────

class ComplianceDocument(models.Model):
    """
    Regulatory document vault.
    Figma: Compliance Vault — upload COA, CPSR, MSDS.
    Each document is linked to a brand and optionally a product.
    Admin verifies from Django admin panel.
    After verification → product compliance_status updated automatically via signal.
    """

    DocType            = DocType
    VerificationStatus = VerificationStatus

    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand   = models.ForeignKey(
        PartnerProfile, on_delete=models.CASCADE, related_name="documents"
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="documents"
    )

    # Document info
    doc_type = models.CharField(max_length=10, choices=DocType.choices)
    title    = models.CharField(max_length=255)
    file     = models.FileField(upload_to="compliance/docs/")
    notes    = models.TextField(blank=True)

    # Verification
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        "users.User", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="verified_documents"
    )
    rejection_reason = models.TextField(blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = "compliance_document"
        ordering            = ["-uploaded_at"]
        verbose_name        = "Compliance Document"
        verbose_name_plural = "Compliance Documents"

    def __str__(self):
        return f"{self.get_doc_type_display()} — {self.title} [{self.verification_status}]"

    @property
    def is_verified(self):
        return self.verification_status == VerificationStatus.VERIFIED

    @property
    def file_name(self):
        return self.file.name.split("/")[-1] if self.file else ""

    @property
    def file_size_kb(self):
        try:
            return round(self.file.size / 1024, 1)
        except Exception:
            return None