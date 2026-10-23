from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
from PIL import Image  # for verification only
from accounts.models import StaffDocument

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = CustomUser
        fields = ("username", "email", "phone", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.phone = self.cleaned_data.get("phone", "")
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"autofocus": True}))


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email", "phone", "avatar"]

    def clean_avatar(self):
        img = self.cleaned_data.get("avatar")
        if not img:
            return img
        if img.size > 5 * 1024 * 1024:
            raise ValidationError("Avatar must be smaller than 5 MB.")
        if getattr(img, "content_type", "") not in {
            "image/jpeg", "image/png", "image/webp",
        }:
            raise ValidationError("Avatar must be a JPEG, PNG, or WebP image.")
        # Sanity-check that the file really is an image
        try:
            Image.open(img).verify()
        except Exception:
            raise ValidationError("File is not a valid image.")
        return img


class StaffDocumentForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(
            role__in=[CustomUser.Roles.STAFF,
                      CustomUser.Roles.MANAGER,
                      CustomUser.Roles.ADMIN],
        ),
        label="Staff member",
    )
    document_type = forms.ChoiceField(choices=StaffDocument.DocumentType.choices)
    title = forms.CharField(max_length=200)
    file = forms.FileField()

    MAX_SIZE = 10 * 1024 * 1024
    ALLOWED_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    def clean_file(self):
        f = self.cleaned_data["file"]
        if f.size > self.MAX_SIZE:
            raise ValidationError("File is larger than 10 MB.")
        if f.content_type not in self.ALLOWED_TYPES:
            raise ValidationError(
                f"Unsupported file type '{f.content_type}'. "
                "Only PDF, JPEG, PNG, and WebP are accepted."
            )
        return f