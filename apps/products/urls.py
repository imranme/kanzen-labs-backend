# from django.urls import path
# from .views import (
#     ProductListCreateView, 
#     ProductDetailView, 
#     BatchCreateView, 
#     ComplianceDashboardMetricsView
# )

# urlpatterns = [
#     # 1. My Products Dashboard List & Step 1 Product Creation
#     # GET  /api/v1/products/          -> List all products (Supports ?search=, ?category=, ?status=)
#     # POST /api/v1/products/          -> Upload new product (Step 1 Wizard)
#     path("", ProductListCreateView.as_view(), name="product-list-create"),

#     # 2. Top Header Scorecard Metrics
#     # GET  /api/v1/products/metrics/  -> Get approved, pending, rejected counts & avg health score
#     path("metrics/", ComplianceDashboardMetricsView.as_view(), name="product-metrics"),

#     # 3. Product Details & Edit/Delete Modals
#     # GET    /api/v1/products/<uuid>/ -> Retrieve single product specs with all batches
#     # PUT    /api/v1/products/<uuid>/ -> Update product attributes (Edit Product Modal)
#     # DELETE /api/v1/products/<uuid>/ -> Delete product record
#     path("<uuid:pk>/", ProductDetailView.as_view(), name="product-detail"),

#     # 4. Batch Ingestion
#     # POST /api/v1/products/<uuid>/batches/ -> Append a manufacturing batch (Step 2 Wizard)
#     path("<uuid:product_id>/batches/", BatchCreateView.as_view(), name="batch-create"),
# ]  

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