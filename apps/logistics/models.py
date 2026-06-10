import uuid
from django.db import models
from apps.products.models import Product


class DestinationCountry(models.TextChoices):
    EU        = "eu",        "EU (Intra-EU)"
    USA       = "usa",       "USA"
    UAE       = "uae",       "UAE"
    SINGAPORE = "singapore", "Singapore"
    JAPAN     = "japan",     "Japan"


class LogisticsDocType(models.TextChoices):
    COMMERCIAL_INVOICE    = "commercial_invoice",    "Commercial Invoice"
    PACKING_LIST          = "packing_list",          "Packing List"
    CERTIFICATE_OF_ORIGIN = "certificate_of_origin", "Certificate of Origin"
    EXPORT_DECLARATION    = "export_declaration",    "Export Declaration"


class GeneratedLogisticDoc(models.Model):
    """
    Figma: Global Logistics Partner popup → Generate Document
           Documents Generated Successfully! screen
    """
    DestinationCountry = DestinationCountry
    DocType            = LogisticsDocType

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product             = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="logistic_documents"
    )
    destination_country = models.CharField(max_length=50, choices=DestinationCountry.choices)
    document_type       = models.CharField(max_length=50, choices=LogisticsDocType.choices)
    file                = models.FileField(upload_to="logistics/generated_docs/", null=True, blank=True)
    file_url            = models.URLField(max_length=500, blank=True)
    file_size_text      = models.CharField(max_length=50, default="PDF - 124 KB")
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        app_label           = "logistics"
        db_table            = "logistics_generated_document"
        ordering            = ["-created_at"]
        verbose_name        = "Global Logistics Partner Doc"
        verbose_name_plural = "Global Logistics Partner Docs"

    def __str__(self):
        return f"{self.product.name} — {self.get_document_type_display()} [{self.destination_country.upper()}]"

    @property
    def file_name(self):
        if self.file:
            return self.file.name.split("/")[-1]
        return f"{self.get_document_type_display()}.pdf"