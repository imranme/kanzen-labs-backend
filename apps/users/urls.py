from django.urls import path
from .views import *

urlpatterns = [

    # auth
    path("auth/signup/", PartnerSignupView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("auth/forgot-password/", ForgotPasswordView.as_view()),
    path("auth/reset-password/", ResetPasswordView.as_view()),

    # onboarding
    path("onboarding/status/", OnboardingStatusView.as_view()),
    path("onboarding/brand-identity/", BrandIdentityView.as_view()),
    path("onboarding/brand-details/", BrandDetailsOnboardingView.as_view()),
    path("onboarding/social-media/", SocialMediaOnboardingView.as_view()),
    path("onboarding/upload-logo/", LogoUploadView.as_view()),

    # profile
    path("profile/", ProfileView.as_view()),
    path("profile/details/", ProfileDetailsView.as_view()),
    path("profile/social/", ProfileSocialView.as_view()),
    path("profile/delete/", DeleteAccountView.as_view()),
]