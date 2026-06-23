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

# ─────────────────────────────────────────────────────────────────────────────
# 1. AUTHENTICATION SECTION
# ─────────────────────────────────────────────────────────────────────────────

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

        # Extracted clean and validated email from serializer
        clean_email = serializer.validated_data.get('email')

        # Terminal Print for Testing
        print("\n" + "="*60)
        print(f"RESET TOKEN: {token}")
        print(f"RESET LINK: http://127.0.0.1:8000/api/v1/auth/reset-password/?token={token}")
        print("="*60 + "\n")

        send_mail(
            'Password Reset',
            f'Your reset link: http://127.0.0.1:8000/api/v1/auth/reset-password/?token={token}',
            'noreply@kanzenlabs.com',
            [clean_email],
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


# ─────────────────────────────────────────────────────────────────────────────
# 2. ONBOARDING SECTION
# ─────────────────────────────────────────────────────────────────────────────

class OnboardingStatusView(APIView):
    """
    Retrieves the active user's current onboarding progress and completion status.
    Essential for client-side navigation logic.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        return Response({
            "onboarding_step": profile.onboarding_step,
            "is_onboarding_complete": profile.is_onboarding_complete,
            "brand_name": profile.brand_name,
        })


class BrandOnboardingView(GenericAPIView):
    """
    Unified ingestion endpoint for all onboarding sequences. Switches serializers
    dynamically based on the incoming request context.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_object(self):
        return self.request.user.profile

    def get_serializer_class(self):
        raw_step = self.request.data.get('step') or self.request.data.get('step-1')
        step = str(raw_step).replace('step-', '').strip() if raw_step else '1'
        
        if step == '1': 
            return LogoUploadSerializer
        elif step == '2': 
            return BrandIdentitySerializer
        elif step == '3': 
            return BrandDetailsUpdateSerializer
        elif step == '4': 
            return SocialMediaUpdateSerializer
            
        return LogoUploadSerializer

    def post(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        profile = self.get_object()
        
        raw_step = request.data.get('step') or request.data.get('step-1')
        try:
            if raw_step and 'step-' in str(raw_step):
                current_step = int(str(raw_step).replace('step-', ''))
            elif raw_step:
                current_step = int(raw_step)
            else:
                step_key = [k for k in request.data.keys() if 'step-' in k]
                current_step = int(step_key[0].replace('step-', '')) if step_key else 1
        except (ValueError, IndexError):
            current_step = 1

        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if current_step >= profile.onboarding_step and profile.onboarding_step < 4:
            profile.onboarding_step = current_step + 1
        
        if current_step == 4:
            profile.onboarding_step = 4
            
        profile.save()
        profile.refresh_from_db()

        return Response({
            "message": f"Step {current_step} completed.",
            "onboarding_step": profile.onboarding_step,
            "is_onboarding_complete": profile.is_onboarding_complete,
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# 3. PROFILE MANAGEMENT SECTION
# ─────────────────────────────────────────────────────────────────────────────

class ProfileView(APIView):
    """
    Handles reading and updating partner profiles including nested relation attributes.
    """
    permission_classes = [IsAuthenticated]
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

        if hasattr(profile, '_details_cache'): del profile._details_cache
        if hasattr(profile, '_social_cache'): del profile._social_cache

        fresh_profile = PartnerProfile.objects.get(pk=profile.pk)
        read_serializer = ProfileReadSerializer(fresh_profile, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_200_OK)


class DeleteAccountView(GenericAPIView):
    serializer_class = DeleteAccountSerializer
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response({"message": "Account deactivated."}, status=status.HTTP_200_OK)