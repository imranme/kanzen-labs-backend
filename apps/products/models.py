import uuid
from django.db import models
from apps.users.models import PartnerProfile

# ──────────────────────────────────────────────────
# CHOICES
# ──────────────────────────────────────────────────

class ProductCategory(models.TextChoices):
    SERUM       = "serum",       "Serum"
    MOISTURISER = "moisturiser", "Moisturiser"
    CLEANSER    = "cleanser",    "Cleanser"
    SPF         = "spf",         "SPF / Sun Care"
    EYE_CARE    = "eye_care",    "Eye Care"
    BODY_CARE   = "body_care",   "Body Care"
    MASK        = "mask",        "Mask"
    OTHER       = "other",       "Other"


class PackSize(models.TextChoices):
    ML_30   = "30ml",   "30 ml"
    ML_50   = "50ml",   "50 ml"
    ML_100  = "100ml",  "100 ml"
    ML_150  = "150ml",  "150 ml"
    ML_200  = "200ml",  "200 ml"
    CUSTOM  = "custom", "Custom"


class ComplianceStatus(models.TextChoices):
    APPROVED = "approved", "Approved"
    PENDING  = "pending",  "Pending"
    REJECTED = "rejected", "Rejected"


# ──────────────────────────────────────────────────
# PRODUCT
# ──────────────────────────────────────────────────

class Product(models.Model):
    """
    Core product record owned by a brand partner.
    Figma: My Products screen, Upload Product (3-step wizard),
           Product Details modal, Edit Product modal.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand       = models.ForeignKey(
        PartnerProfile, on_delete=models.CASCADE, related_name="products"
    )
    
    # ── Step 1 — Basic Info ──
    name        = models.CharField(max_length=255)
    sku_code    = models.CharField(max_length=100, unique=True)
    barcode_ean = models.CharField(max_length=100, blank=True)
    category    = models.CharField(
        max_length=30, choices=ProductCategory.choices, default=ProductCategory.SERUM
    )
    pack_size   = models.CharField(
        max_length=20, choices=PackSize.choices, default=PackSize.ML_50
    )
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image        = models.ImageField(upload_to="products/images/", null=True, blank=True)
    
    # ── Compliance ──
    compliance_status       = models.CharField(
        max_length=20, choices=ComplianceStatus.choices, default=ComplianceStatus.PENDING
    )
    compliance_health_score = models.PositiveSmallIntegerField(default=0)  # 0-100
    
    # ── Meta ──
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Expose choices for serializers / views
    Category         = ProductCategory
    PackSize         = PackSize
    ComplianceStatus = ComplianceStatus

    class Meta:
        db_table            = "products_product"
        ordering            = ["-created_at"]
        verbose_name        = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.name} ({self.sku_code})"

    @property
    def batch_count(self):
        return self.batches.count()

    @property
    def latest_batch(self):
        return self.batches.order_by("-manufacturing_date").first()


# ──────────────────────────────────────────────────
# BATCH RECORD
# ──────────────────────────────────────────────────

class BatchRecord(models.Model):
    """
    Manufacturing batch linked to a product.
    Figma: Upload Product Step 2 — Batch Code, Quantity, MFD, Expiry.
    """
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product             = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="batches"
    )
    batch_code          = models.CharField(max_length=100)
    quantity            = models.PositiveIntegerField()
    manufacturing_date  = models.DateField()
    expiry_date         = models.DateField()
    uploaded_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table            = "products_batch_record"
        ordering            = ["-manufacturing_date"]
        verbose_name        = "Batch Record"
        verbose_name_plural = "Batch Records"

    def __str__(self):
        return f"{self.product.name} — Batch {self.batch_code}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()

