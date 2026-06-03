from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    PartnerSignupView,
    LoginView,
    LogoutView,
    ForgotPasswordView,
    ResetPasswordView,
    OnboardingStatusView,
    BrandOnboardingView,
    ProfileView,
    DeleteAccountView,
)

urlpatterns = [
    # ── AUTHENTICATION ──────────────────────────────
    path("auth/signup/",           PartnerSignupView.as_view()),
    path("auth/login/",            LoginView.as_view()),
    path("auth/logout/",           LogoutView.as_view()),
    path("auth/token/refresh/",    TokenRefreshView.as_view()),
    path("auth/forgot-password/",  ForgotPasswordView.as_view()),
    path("auth/reset-password/",   ResetPasswordView.as_view()),

    # ── ONBOARDING ──────────────────────────────────
    # Unified endpoint — pass "step": "1", "2", "3", or "4" in the request body
    path("onboarding/status/",    OnboardingStatusView.as_view()),
    path("onboarding/",           BrandOnboardingView.as_view()),

    # ── PROFILE MANAGEMENT ──────────────────────────
    path("profile/",              ProfileView.as_view()),
    path("profile/delete/",       DeleteAccountView.as_view()),
]

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION COMPLETE
# All onboarding logic is handled dynamically via the /onboarding/ route.
# ─────────────────────────────────────────────────────────────────────────────