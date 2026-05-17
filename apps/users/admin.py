from django.contrib import admin
from .models import User, PartnerProfile, BrandDetails, SocialMedia

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('email', 'full_name')

@admin.register(PartnerProfile)
class PartnerProfileAdmin(admin.ModelAdmin):
    list_display = ('brand_name', 'user', 'status', 'tier', 'created_at')
    list_filter = ('status', 'tier')
    search_fields = ('brand_name', 'user__email')
    # এখান থেকেই আপনি status 'pending' থেকে 'approved' করতে পারবেন

admin.site.register(BrandDetails)
admin.site.register(SocialMedia)