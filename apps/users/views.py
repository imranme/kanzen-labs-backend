from django.utils import timezone
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication

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

# ──────────────────────────────────────────────────
# 1. AUTHENTICATION SECTION
# ──────────────────────────────────────────────────

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
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)


class ForgotPasswordView(GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.save() 

        # Terminal Print for Testing
        print("\n" + "="*60)
        print(f"RESET TOKEN: {token}")
        print(f"RESET LINK: http://127.0.0.1:8000/api/v1/auth/reset-password/?token={token}")
        print("="*60 + "\n")

        send_mail(
            'Password Reset',
            f'Your reset link: http://127.0.0.1:8000/api/v1/auth/reset-password/?token={token}',
            'noreply@kanzenlabs.com',
            [request.data.get('email')],
            fail_silently=False,
        )
        return Response({"message": "Reset link sent if email exists."}, status=status.HTTP_200_OK)


class ResetPasswordView(GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────────
# 2. ONBOARDING SECTION (Dynamic Handler)
# ──────────────────────────────────────────────────

class OnboardingStatusView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        profile = request.user.profile
        return Response({
            "onboarding_step": profile.onboarding_step,
            "is_onboarding_complete": profile.is_onboarding_complete,
            "brand_name": profile.brand_name,
        })


class BrandOnboardingView(GenericAPIView):
    """
    Handles Step 1 to 4 of the onboarding flow based on the 'step' parameter.
    """
    permission_classes = [IsAuthenticated,]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_object(self):
        return self.request.user.profile

    def get_serializer_class(self):
        step = str(self.request.data.get('step', '1'))
        if step == '1': return LogoUploadSerializer
        elif step == '2': return BrandIdentitySerializer
        elif step == '3': return BrandDetailsUpdateSerializer
        elif step == '4': return SocialMediaUpdateSerializer
        return LogoUploadSerializer

    def post(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": f"Step {request.data.get('step', '1')} completed.",
            "onboarding_step": profile.onboarding_step,
            "is_onboarding_complete": profile.is_onboarding_complete,
        })


# ──────────────────────────────────────────────────
# 3. PROFILE MANAGEMENT SECTION
# ──────────────────────────────────────────────────

class ProfileView(APIView):
    permission_classes = [IsAuthenticated, ]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        profile = request.user.profile
        serializer = ProfileReadSerializer(profile, context={"request": request})
        return Response(serializer.data)

    def put(self, request):
        profile = request.user.profile
        serializer = ProfileUpdateSerializer(
            profile, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        read_serializer = ProfileReadSerializer(profile, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_200_OK)


class DeleteAccountView(GenericAPIView):
    serializer_class = DeleteAccountSerializer
    permission_classes = [IsAuthenticated,]

    def delete(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response({"message": "Account deactivated."}, status=status.HTTP_200_OK)

# ─────────────────────────────────────────────────────────────────────────────
# FINAL MERGE COMPLETE: All onboarding steps and auth flows are now unified.
# Happy Coding with Kanzen Labs Backend! 🚀
# ─────────────────────────────────────────────────────────────────────────────

