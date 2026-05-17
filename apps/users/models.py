# import uuid
# from django.db import models
# from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
# from django.utils import timezone


# # ─────────────────────────────────────────────
# # USER MANAGER
# # ─────────────────────────────────────────────

# class UserManager(BaseUserManager):

#     def create_user(self, email, password=None, **extra_fields):
#         if not email:
#             raise ValueError("Email is required")

#         email = self.normalize_email(email)
#         user = self.model(email=email, **extra_fields)

#         user.set_password(password)
#         user.save(using=self._db)

#         return user

#     def create_superuser(self, email, password=None, **extra_fields):
#         extra_fields.setdefault("is_staff", True)
#         extra_fields.setdefault("is_superuser", True)

#         return self.create_user(email, password, **extra_fields)


# # ─────────────────────────────────────────────
# # USER MODEL
# # ─────────────────────────────────────────────

# class User(AbstractBaseUser, PermissionsMixin):
#     """
#     Custom user model — email-based login.
#     Every user maps to exactly one PartnerProfile (brand).
#     """

#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

#     email = models.EmailField(unique=True)
#     full_name = models.CharField(max_length=255)

#     is_active = models.BooleanField(default=False)     # activated after admin review
#     is_staff = models.BooleanField(default=False)
#     is_verified = models.BooleanField(default=False)   # email verified

#     date_joined = models.DateTimeField(default=timezone.now)

#     objects = UserManager()

#     USERNAME_FIELD = "email"
#     REQUIRED_FIELDS = ["full_name"]

#     class Meta:
#         db_table = "users_user"
#         verbose_name = "User"

#     def __str__(self):
#         return self.email


# # ─────────────────────────────────────────────
# # PARTNER PROFILE
# # ─────────────────────────────────────────────

# class PartnerProfile(models.Model):

#     STATUS_CHOICES = [
#         ("pending", "Pending Review"),
#         ("approved", "Approved"),
#         ("rejected", "Rejected"),
#     ]

#     # TIER_CHOICES = [
#     #     ("free", "Free"),
#     #     ("pro", "Pro TIER"),
#     #     ("enterprise", "Enterprise"),
#     # ]

#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         related_name="profile"
#     )

#     brand_name = models.CharField(max_length=255)
#     brand_tagline = models.CharField(max_length=255, blank=True)
#     about_brand = models.TextField(blank=True)

#     logo = models.ImageField(
#         upload_to="brand/logos/",
#         null=True,
#         blank=True
#     )

#     cover_image = models.ImageField(
#         upload_to="brand/covers/",
#         null=True,
#         blank=True
#     )

#     phone = models.CharField(max_length=30, blank=True)

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="pending"
#     )

#     tier = models.CharField(
#         max_length=20,
#         choices=TIER_CHOICES,
#         default="free"
#     )

#     trust_score = models.PositiveSmallIntegerField(default=0)  # 0-100
#     is_verified = models.BooleanField(default=False)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = "users_partner_profile"

#     def __str__(self):
#         return f"{self.brand_name} ({self.status})"


# # ─────────────────────────────────────────────
# # BRAND DETAILS
# # ─────────────────────────────────────────────

# class BrandDetails(models.Model):
#     """
#     Business information for the brand (Figma: Brand Details step 3/4).
#     """

#     profile = models.OneToOneField(
#         PartnerProfile,
#         on_delete=models.CASCADE,
#         related_name="details"
#     )

#     website = models.URLField(blank=True)
#     founded_year = models.PositiveSmallIntegerField(null=True, blank=True)
#     # contact_email = models.EmailField(blank=True)
#     location = models.CharField(max_length=255, blank=True)
#     production_base = models.CharField(
#         max_length=255,
#         blank=True
#     )  # e.g. "UK & EU-based manufacturers"

#     class Meta:
#         db_table = "users_brand_details"


# # ─────────────────────────────────────────────
# # SOCIAL MEDIA
# # ─────────────────────────────────────────────

# class SocialMedia(models.Model):
#     """
#     Optional social links for the brand (Figma: Social Media step 4/4).
#     """

#     profile = models.OneToOneField(
#         PartnerProfile,
#         on_delete=models.CASCADE,
#         related_name="social"
#     )

#     instagram = models.URLField(blank=True)
#     linkedin = models.URLField(blank=True)
#     Twitter = models.URLField(blank=True)

#     class Meta:
#         db_table = "users_social_media"




import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)
from django.utils import timezone


# ──────────────────────────────────────────────────
# USER MANAGER
# ──────────────────────────────────────────────────

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


# ──────────────────────────────────────────────────
# USER MODEL
# ──────────────────────────────────────────────────

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom email-based user.
    is_active = False until admin approves the partner application.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email       = models.EmailField(unique=True)
    full_name   = models.CharField(max_length=255)
    phone       = models.CharField(max_length=30, blank=True)

    is_active   = models.BooleanField(default=False)
    is_staff    = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table            = "users_user"
        verbose_name        = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    @property
    def brand_name(self):
        try:
            return self.profile.brand_name
        except Exception:
            return ""


# ──────────────────────────────────────────────────
# CHOICES  (defined OUTSIDE the class — no NameError)
# ──────────────────────────────────────────────────

class ProfileStatus(models.TextChoices):
    PENDING  = "pending",  "Pending Review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class ProfileTier(models.TextChoices):
    FREE       = "free",       "Free"
    PRO        = "pro",        "Pro TIER"
    ENTERPRISE = "enterprise", "Enterprise"


class OnboardingStep(models.IntegerChoices):
    SIGNUP        = 1, "Signup Complete"
    BRAND_DETAILS = 2, "Brand Details Filled"
    SOCIAL        = 3, "Social Media Added"
    COMPLETE      = 4, "Onboarding Complete"


# ──────────────────────────────────────────────────
# PARTNER PROFILE
# ──────────────────────────────────────────────────

class PartnerProfile(models.Model):
    """
    Created during 'Apply as Partner' signup.
    status drives the whole onboarding gate:
      pending  → application submitted, waiting for admin review
      approved → user activated, full access granted
      rejected → user blocked
    """

    # expose choices as class attributes so views/serializers can reference them
    Status         = ProfileStatus
    Tier           = ProfileTier
    OnboardingStep = OnboardingStep

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user         = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # Core brand identity
    brand_name    = models.CharField(max_length=255)
    brand_tagline = models.CharField(max_length=255, blank=True)
    about_brand   = models.TextField(blank=True)
    logo          = models.ImageField(upload_to="brand/logos/",  null=True, blank=True)
    cover_image   = models.ImageField(upload_to="brand/covers/", null=True, blank=True)

    # Status & tier
    status       = models.CharField(
        max_length=20,
        choices=ProfileStatus.choices,
        default=ProfileStatus.PENDING,
    )
    tier         = models.CharField(
        max_length=20,
        choices=ProfileTier.choices,
        default=ProfileTier.FREE,
    )
    trust_score  = models.PositiveSmallIntegerField(default=0)
    is_verified  = models.BooleanField(default=False)

    # Onboarding progress
    onboarding_step = models.PositiveSmallIntegerField(
        choices=OnboardingStep.choices,
        default=OnboardingStep.SIGNUP,
    )

    # Admin fields
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_profiles",
    )
    reviewed_at      = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = "users_partner_profile"
        verbose_name        = "Partner Profile"
        verbose_name_plural = "Partner Profiles"

    def __str__(self):
        return f"{self.brand_name} [{self.status}]"

    @property
    def is_onboarding_complete(self):
        return self.onboarding_step >= OnboardingStep.COMPLETE


# ──────────────────────────────────────────────────
# BRAND DETAILS  (Step 3 of 4 in Figma)
# ──────────────────────────────────────────────────

class BrandDetails(models.Model):
    """
    Business / operational info filled in during onboarding step 3.
    """
    profile         = models.OneToOneField(
        PartnerProfile, on_delete=models.CASCADE, related_name="details"
    )
    website         = models.URLField(blank=True)
    founded_year    = models.PositiveSmallIntegerField(null=True, blank=True)
    contact_email   = models.EmailField(blank=True)
    location        = models.CharField(max_length=255, blank=True)
    production_base = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "users_brand_details"

    def __str__(self):
        return f"Details → {self.profile.brand_name}"


# ──────────────────────────────────────────────────
# SOCIAL MEDIA  (Step 4 of 4 in Figma)
# ──────────────────────────────────────────────────

class SocialMedia(models.Model):
    """
    Optional social links added during the last onboarding step.
    """
    profile   = models.OneToOneField(
        PartnerProfile, on_delete=models.CASCADE, related_name="social"
    )
    instagram = models.URLField(blank=True)
    linkedin  = models.URLField(blank=True)
    tiktok    = models.URLField(blank=True)

    class Meta:
        db_table = "users_social_media"

    def __str__(self):
        return f"Social → {self.profile.brand_name}"


# ──────────────────────────────────────────────────
# PASSWORD RESET TOKEN
# ──────────────────────────────────────────────────

class PasswordResetToken(models.Model):
    """
    One-time token for the 'Forgot Password' flow.
    Expires after 1 hour.
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_tokens")
    token      = models.CharField(max_length=64, unique=True)
    is_used    = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_password_reset_token"

    def __str__(self):
        return f"Reset token for {self.user.email}"

    @property
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at