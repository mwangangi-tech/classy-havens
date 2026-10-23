from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.utils.text import slugify

from accounts.models import CustomUser, StaffDocument
from catalog.models import Product, ProductVariant, Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "description", "image", "sort_order"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        qs = Category.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A category with this name already exists.")
        return name

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip()
        if not slug:
            slug = slugify(self.cleaned_data.get("name", ""))
        if not slug:
            raise ValidationError("Could not build a slug — please enter one manually.")
        qs = Category.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A category with this slug already exists.")
        return slug


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["category", "name", "slug", "description",
                  "base_price", "image", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip()
        if not slug:
            slug = slugify(self.cleaned_data["name"])
        if not slug:
            raise ValidationError("Could not build a slug — please enter one manually.")
        qs = Product.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A product with this slug already exists.")
        return slug

    def clean_base_price(self):
        price = self.cleaned_data["base_price"]
        if price < 0:
            raise ValidationError("Price cannot be negative.")
        return price


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ["size", "color", "sku", "stock", "price_override"]


ProductVariantFormSet = forms.inlineformset_factory(
    Product, ProductVariant,
    form=ProductVariantForm,
    extra=1, can_delete=True,
    min_num=1, validate_min=True,
)


class InventoryForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ["stock", "price_override"]


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