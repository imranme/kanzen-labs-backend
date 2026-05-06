import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


# ─────────────────────────────────────────────
# USER MANAGER
# ─────────────────────────────────────────────

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


# ─────────────────────────────────────────────
# USER MODEL
# ─────────────────────────────────────────────

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model — email-based login.
    Every user maps to exactly one PartnerProfile (brand).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)

    is_active = models.BooleanField(default=False)     # activated after admin review
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)   # email verified

    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users_user"
        verbose_name = "User"

    def __str__(self):
        return self.email


# ─────────────────────────────────────────────
# PARTNER PROFILE
# ─────────────────────────────────────────────

class PartnerProfile(models.Model):
    """
    Onboarding profile linked 1-to-1 with User.
    Created during the 'Apply as Partner' flow (Figma step 1-4).
    """

    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    # TIER_CHOICES = [
    #     ("free", "Free"),
    #     ("pro", "Pro TIER"),
    #     ("enterprise", "Enterprise"),
    # ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    brand_name = models.CharField(max_length=255)
    brand_tagline = models.CharField(max_length=255, blank=True)
    about_brand = models.TextField(blank=True)

    logo = models.ImageField(
        upload_to="brand/logos/",
        null=True,
        blank=True
    )

    cover_image = models.ImageField(
        upload_to="brand/covers/",
        null=True,
        blank=True
    )

    phone = models.CharField(max_length=30, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default="free"
    )

    trust_score = models.PositiveSmallIntegerField(default=0)  # 0-100
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users_partner_profile"

    def __str__(self):
        return f"{self.brand_name} ({self.status})"


# ─────────────────────────────────────────────
# BRAND DETAILS
# ─────────────────────────────────────────────

class BrandDetails(models.Model):
    """
    Business information for the brand (Figma: Brand Details step 3/4).
    """

    profile = models.OneToOneField(
        PartnerProfile,
        on_delete=models.CASCADE,
        related_name="details"
    )

    website = models.URLField(blank=True)
    founded_year = models.PositiveSmallIntegerField(null=True, blank=True)
    # contact_email = models.EmailField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    production_base = models.CharField(
        max_length=255,
        blank=True
    )  # e.g. "UK & EU-based manufacturers"

    class Meta:
        db_table = "users_brand_details"


# ─────────────────────────────────────────────
# SOCIAL MEDIA
# ─────────────────────────────────────────────

class SocialMedia(models.Model):
    """
    Optional social links for the brand (Figma: Social Media step 4/4).
    """

    profile = models.OneToOneField(
        PartnerProfile,
        on_delete=models.CASCADE,
        related_name="social"
    )

    instagram = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    Twitter = models.URLField(blank=True)

    class Meta:
        db_table = "users_social_media"
