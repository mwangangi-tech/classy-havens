from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        STAFF    = "staff",    "Staff"
        MANAGER  = "manager",  "Manager"
        ADMIN    = "admin",    "Admin"

    role = models.CharField(max_length=20, choices=Roles.choices,
                            default=Roles.CUSTOMER)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/", blank=True, null=True,
        help_text="Optional profile picture (JPEG, PNG, WebP).",
    )

    @property
    def is_customer(self):
        return self.role == self.Roles.CUSTOMER

    @property
    def is_staff_member(self):
        return (
            self.is_superuser
            or self.is_staff
            or self.role in (self.Roles.STAFF, self.Roles.MANAGER, self.Roles.ADMIN)
        )

    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, "url"):
            return self.avatar.url
        return ""

class StaffDocument(models.Model):
    class DocumentType(models.TextChoices):
        HIGH_SCHOOL = "high_school", "High School Certificate"
        UNIVERSITY  = "university",  "University Degree"
        NATIONAL_ID = "national_id", "National ID"
        PASSPORT    = "passport",    "International Passport"
        TAX_ID      = "tax_id",      "Tax Identification"
        OTHER       = "other",       "Other"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(max_length=30,
                                     choices=DocumentType.choices)
    title = models.CharField(max_length=200)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120)
    file_size = models.PositiveIntegerField()
    encrypted_data = models.BinaryField()
    salt = models.BinaryField()
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="uploaded_documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()}) → {self.user.username}"