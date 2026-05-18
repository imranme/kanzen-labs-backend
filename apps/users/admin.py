from django.contrib import admin
from .models import User, PartnerProfile

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'is_active', 'is_staff')
    list_editable = ('is_active',) # এখান থেকেই সরাসরি একটিভ করা যাবে

@admin.register(PartnerProfile)
class PartnerProfileAdmin(admin.ModelAdmin):
    list_display = ('brand_name', 'status', 'user')
    list_filter = ('status',)