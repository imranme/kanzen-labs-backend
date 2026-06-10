"""
Signal: when a ComplianceDocument is deleted,
recalculate the related product's compliance status.
"""
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import ComplianceDocument
from .services import _recalculate_product_compliance, _recalculate_brand_score


@receiver(post_delete, sender=ComplianceDocument)
def on_document_deleted(sender, instance, **kwargs):
    if instance.product:
        _recalculate_product_compliance(instance.product)
    _recalculate_brand_score(instance.brand)