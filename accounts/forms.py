from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from PIL import Image

from .models import CustomUser, StaffDocument

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = CustomUser
        fields = ("username", "email", "phone", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
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
        widgets = {
            "avatar": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }

    def clean_avatar(self):
        # ... (keep your existing clean_avatar method exactly as it is) ...
        img = self.cleaned_data.get("avatar")
        if not img:
            return img
        if img.size > 5 * 1024 * 1024:
            raise ValidationError("Avatar must be smaller than 5 MB.")
        if getattr(img, "content_type", "") not in {"image/jpeg", "image/png", "image/webp"}:
            raise ValidationError("Avatar must be a JPEG, PNG, or WebP image.")
        try:
            Image.open(img).verify()
        except Exception:
            raise ValidationError("File is not a valid image.")
        return img

class StaffCreateForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", "phone", "role"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [
            (CustomUser.Roles.STAFF,   "Staff"),
            (CustomUser.Roles.MANAGER, "Manager"),
            (CustomUser.Roles.ADMIN,   "Admin"),
        ]
        self.fields["role"].initial = CustomUser.Roles.STAFF

    def clean_username(self):
        username = self.cleaned_data["username"]
        if CustomUser.objects.filter(username__iexact=username).exists():
            raise ValidationError("Username already taken.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").lower()
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email already in use.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        if p1:
            try:
                validate_password(p1)
            except ValidationError as exc:
                self.add_error("password1", exc.messages)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class StaffUpdateForm(forms.ModelForm):
    new_password = forms.CharField(
        widget=forms.PasswordInput, required=False,
        label="Reset password",
        help_text="Leave blank to keep the current password.",
    )

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email", "phone", "role", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [
            (CustomUser.Roles.STAFF,   "Staff"),
            (CustomUser.Roles.MANAGER, "Manager"),
            (CustomUser.Roles.ADMIN,   "Admin"),
        ]

    def clean_new_password(self):
        pwd = self.cleaned_data.get("new_password")
        if pwd:
            try:
                validate_password(pwd)
            except ValidationError as exc:
                raise ValidationError(exc.messages)
        return pwd

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get("new_password")
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user

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
    ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}

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