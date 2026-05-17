from rest_framework.permissions import BasePermission
from .models import PartnerProfile


class IsApprovedPartner(BasePermission):
    """
    Only allows access if the user has an approved PartnerProfile.
    Used on all protected views.
    """
    message = "Your account is pending review or has not been approved."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return request.user.profile.status == PartnerProfile.Status.APPROVED
        except PartnerProfile.DoesNotExist:
            return False


class IsOnboardingComplete(BasePermission):
    """
    Full feature access only after onboarding is complete.
    """
    message = "Please complete your brand profile first."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return request.user.profile.is_onboarding_complete
        except PartnerProfile.DoesNotExist:
            return False