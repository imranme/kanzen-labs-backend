import secrets
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, PartnerProfile, BrandDetails, SocialMedia, PasswordResetToken


# ───────── helper ─────────

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# ───────── auth ─────────

class PartnerSignupSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    brand_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value.lower()

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        phone = validated_data.pop("phone", "")
        brand_name = validated_data.pop("brand_name")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
            phone=phone,
            is_active=False,
        )

        profile = PartnerProfile.objects.create(user=user, brand_name=brand_name)
        BrandDetails.objects.create(profile=profile)
        SocialMedia.objects.create(profile=profile)

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email").lower()
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")

        profile = getattr(user, "profile", None)

        if not profile:
            raise serializers.ValidationError("Profile not found")

        if profile.status == "pending":
            raise serializers.ValidationError("Account under review")
        if profile.status == "rejected":
            raise serializers.ValidationError("Account rejected")
        if not user.is_active:
            raise serializers.ValidationError("Account inactive")

        attrs["user"] = user
        return attrs

    def get_response_data(self, user):
        tokens = get_tokens_for_user(user)
        profile = user.profile

        return {
            "tokens": tokens,
            "user_id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "brand_name": profile.brand_name,
            "onboarding_step": profile.onboarding_step,
            "is_onboarding_complete": profile.is_onboarding_complete,
        }


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data["email"].lower()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)

        token = secrets.token_urlsafe(48)

        PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        return token


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")

        try:
            reset = PasswordResetToken.objects.get(token=attrs["token"])
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token")

        if not reset.is_valid:
            raise serializers.ValidationError("Token expired")

        attrs["reset"] = reset
        return attrs

    def save(self):
        reset = self.validated_data["reset"]
        user = reset.user

        user.set_password(self.validated_data["password"])
        user.save()

        reset.is_used = True
        reset.save()

        return user


# ───────── onboarding ─────────

class BrandIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerProfile
        fields = ["brand_name", "brand_tagline", "about_brand"]


class BrandDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandDetails
        fields = ["website", "founded_year",  "location", "production_base"]


class BrandDetailsUpdateSerializer(serializers.ModelSerializer):
    details = BrandDetailsSerializer()

    class Meta:
        model = PartnerProfile
        fields = ["details"]

    def update(self, instance, validated_data):
        data = validated_data.get("details", {})
        obj, _ = BrandDetails.objects.get_or_create(profile=instance)

        for k, v in data.items():
            setattr(obj, k, v)
        obj.save()

        return instance


class SocialMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMedia
        fields = ["instagram", "linkedin", "twitter"]


class SocialMediaUpdateSerializer(serializers.ModelSerializer):
    social = SocialMediaSerializer()

    class Meta:
        model = PartnerProfile
        fields = ["social"]

    def update(self, instance, validated_data):
        data = validated_data.get("social", {})
        obj, _ = SocialMedia.objects.get_or_create(profile=instance)

        for k, v in data.items():
            setattr(obj, k, v)
        obj.save()

        return instance


class LogoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerProfile
        fields = ["logo", "cover_image"]


# ───────── profile ─────────

class ProfileReadSerializer(serializers.ModelSerializer):
    details = BrandDetailsSerializer(read_only=True)
    social = SocialMediaSerializer(read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = PartnerProfile
        fields = [
            "id", "brand_name", "brand_tagline", "about_brand",
            "logo", "cover_image",
            "status", "tier", "trust_score",
            "onboarding_step", "is_onboarding_complete",
            "email", "details", "social",
        ]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerProfile
        fields = ["brand_name", "brand_tagline", "about_brand", "logo", "cover_image"]


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Wrong password")
        return value