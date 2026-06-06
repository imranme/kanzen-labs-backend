from django.db import transaction  # 👈 ট্রানজেকশন সেফ রাখার জন্য যোগ করা হয়েছে
from django.db.models import Count, Avg, Q
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.filters import SearchFilter

from .models import Product, BatchRecord
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer,
    ProductUpdateSerializer,
    BatchRecordSerializer,
    BatchRecordCreateSerializer,
    ComplianceScoreSerializer,
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. PRODUCT MANAGEMENT VIEWS (My Products Listing & Creation)
# ─────────────────────────────────────────────────────────────────────────────

class ProductListCreateView(generics.ListCreateAPIView):
    """
    Handles listing a partner's products and creating a new product record.
    Figma: My Products list grid & Upload Product Step 1 Wizard.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [SearchFilter]
    
    # Searches by product name or explicit SKU code from Figma search bar
    search_fields = ["name", "sku_code"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductCreateSerializer
        return ProductListSerializer

    def get_queryset(self):
        # Tenant scoping: Filter inventory belonging only to the active brand
        brand = self.request.user.profile
        queryset = Product.objects.filter(brand=brand).prefetch_related('batches')

        # Dropdown filters from Figma UI
        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(category=category_filter.lower())

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(compliance_status=status_filter.lower())

        return queryset


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving full item specs, editing attributes, or deleting a product.
    Figma: Product Details modal, Edit Product modal + Wizard Step 2 All-in-One Data Update.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProductUpdateSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        brand = self.request.user.profile
        return Product.objects.filter(brand=brand).prefetch_related('batches')

    # 🔗 এখানে Step 2-এর অল-ইন-ওয়ান ডেটা (Product Update + Batch Create) মার্জ করা হয়েছে
    def perform_update(self, serializer):
        with transaction.atomic():  # ডেটাবেজ সেফটি নিশ্চিত করার জন্য
            # ১. প্রথমে প্রোডাক্টের নিজস্ব ডেটা (ক্যাটাগরি, সাইজ, রিটেইল প্রাইস) সেভ হবে
            product = serializer.save()
            
            # ২. রিকোয়েস্ট বডিতে "batch" অবজেক্ট আছে কিনা চেক করবে
            batch_data = self.request.data.get("batch")
            if batch_data:
                # ব্যাচ ক্রিয়েট সিরিয়ালাইজারে প্রোডাক্টের ইনস্ট্যান্স পাস করে ডেটা সেভ করা হচ্ছে
                batch_serializer = BatchRecordCreateSerializer(data=batch_data)
                batch_serializer.is_valid(raise_exception=True)
                batch_serializer.save(product=product)


# ─────────────────────────────────────────────────────────────────────────────
# 2. BATCH MANAGEMENT VIEWS (Upload Wizard Step 2 / Standalone Add Batch)
# ─────────────────────────────────────────────────────────────────────────────

class BatchCreateView(generics.CreateAPIView):
    """
    Appends a manufacturing batch record to an explicit product instance.
    Figma: Upload Product Step 2 Wizard & Add Batch modal.
    """
    serializer_class = BatchRecordCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        product_id = self.kwargs.get("product_id")
        
        try:
            product = Product.objects.get(pk=product_id, brand=request.user.profile)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found or unauthorized access."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        batch = serializer.save(product=product)
        
        response_serializer = BatchRecordSerializer(batch)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# 3. SCORECARD METRICS VIEWS (Header Metrics for Product Dashboard)
# ─────────────────────────────────────────────────────────────────────────────

class ComplianceDashboardMetricsView(APIView):
    """
    Aggregates product status counts and compliance health scores.
    Figma: My Products screen top header scorecard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        brand = request.user.profile
        
        # Optimize performance using a single aggregation query
        metrics = Product.objects.filter(brand=brand).aggregate(
            total_products=Count('id'),
            approved_count=Count('id', filter=Q(compliance_status='approved')),
            pending_count=Count('id', filter=Q(compliance_status='pending')),
            rejected_count=Count('id', filter=Q(compliance_status='rejected')),
            avg_health_score=Avg('compliance_health_score')
        )

        payload = {
            "total_products": metrics['total_products'] or 0,
            "approved": metrics['approved_count'] or 0,
            "pending": metrics['pending_count'] or 0,
            "rejected": metrics['rejected_count'] or 0,
            "health_score": round(metrics['avg_health_score']) if metrics['avg_health_score'] is not None else 0
        }

        serializer = ComplianceScoreSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)