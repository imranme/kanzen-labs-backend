from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import User, PartnerProfile

@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('email', 'full_name', 'is_active', 'is_staff')
    list_editable = ('is_active',)


@admin.register(PartnerProfile)
class PartnerProfileAdmin(ModelAdmin):
    list_display = ('brand_name', 'status', 'onboarding_step', 'check_onboarding', 'user')
    list_editable = ('status', 'onboarding_step')  
    list_filter = ('status', 'onboarding_step')
    search_fields = ('brand_name', 'user__email', 'user__full_name')

    @admin.display(description="Is Onboarding Complete?", boolean=True)
    def check_onboarding(self, obj):
        return obj.is_onboarding_complete