from django.utils import timezone
from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import PartnerProfile
from .permissions import IsApprovedPartner
from .serializers import (
    PartnerSignupSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    BrandIdentitySerializer,
    BrandDetailsUpdateSerializer,
    SocialMediaUpdateSerializer,
    LogoUploadSerializer,
    ProfileReadSerializer,
    ProfileUpdateSerializer,
    DeleteAccountSerializer,
)


# ─────────────────────────────
# AUTH
# ─────────────────────────────

class PartnerSignupView(GenericAPIView):
    serializer_class = PartnerSignupSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "Application submitted successfully!",
                "detail": "Your application is under review. You will receive an email within 24-48 hours.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        data = serializer.get_response_data(user)
        return Response(data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass

        return Response(
            {"message": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )


class ForgotPasswordView(GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "If this email is registered, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Password has been reset successfully. You can now log in."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────
# ONBOARDING
# ─────────────────────────────

class OnboardingStatusView(APIView):
    permission_classes = [IsAuthenticated, IsApprovedPartner]

    def get(self, request):
        profile = request.user.profile

        return Response({
            "onboarding_step": profile.onboarding_step,
            "is_onboarding_complete": profile.is_onboarding_complete,
            "brand_name": profile.brand_name,
        })


class BrandIdentityView(GenericAPIView):
    serializer_class = BrandIdentitySerializer
    permission_classes = [IsAuthenticated, IsApprovedPartner]

    def put(self, request):
        profile = request.user.profile
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Brand identity saved.",
            "onboarding_step": profile.onboarding_step
        })


class BrandDetailsOnboardingView(GenericAPIView):
    serializer_class = BrandDetailsUpdateSerializer
    permission_classes = [IsAuthenticated, IsApprovedPartner]

    def put(self, request):
        profile = request.user.profile
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Brand details saved.",
            "onboarding_step": profile.onboarding_step
        })


class SocialMediaOnboardingView(GenericAPIView):
    serializer_class = SocialMediaUpdateSerializer
    permission_classes = [IsAuthenticated, IsApprovedPartner]

    def put(self, request):
        profile = request.user.profile
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Onboarding complete! Welcome to Kanzen Labs.",
            "onboarding_step": profile.onboarding_step,
            "is_onboarding_complete": profile.is_onboarding_complete,
        })

class LogoUploadView(GenericAPIView):
    serializer_class = LogoUploadSerializer
    permission_classes = [IsAuthenticated, IsApprovedPartner]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        profile = request.user.profile
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Logo uploaded successfully.",
            "logo": str(profile.logo)
        })

# ─────────────────────────────
# PROFILE
# ─────────────────────────────

class ProfileView(APIView):
    permission_classes = [IsAuthenticated, IsApprovedPartner]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        profile = request.user.profile
        serializer = ProfileReadSerializer(profile, context={"request": request})
        return Response(serializer.data)

    def put(self, request):
        profile = request.user.profile
        serializer = ProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        read_serializer = ProfileReadSerializer(profile, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_200_OK)


class ProfileDetailsView(GenericAPIView):
    serializer_class = BrandDetailsUpdateSerializer
    permission_classes = [IsAuthenticated, IsApprovedPartner]

    def put(self, request):
        profile = request.user.profile
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Brand details updated."})


class ProfileSocialView(GenericAPIView):
    serializer_class = SocialMediaUpdateSerializer
    permission_classes = [IsAuthenticated, IsApprovedPartner]

    def put(self, request):
        profile = request.user.profile
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Social media links updated."})


class DeleteAccountView(GenericAPIView):
    serializer_class = DeleteAccountSerializer
    permission_classes = [IsAuthenticated, IsApprovedPartner]

    def delete(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])

        return Response(
            {"message": "Account has been deactivated successfully."},
            status=status.HTTP_200_OK,
        )