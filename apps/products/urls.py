
from django.urls import path
from .views import (
    ProductListCreateView, ProductDetailView, 
    BatchCreateView, ComplianceDashboardMetricsView
)

urlpatterns = [
    path("", ProductListCreateView.as_view(), name="product-list-create"),
    path("metrics/", ComplianceDashboardMetricsView.as_view(), name="product-metrics"),
    path("<uuid:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("<uuid:product_id>/batches/", BatchCreateView.as_view(), name="batch-create"),
]