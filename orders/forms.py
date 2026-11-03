from django import forms
from .countries import COUNTRY_CHOICES
from .models import ShippingAddress


class ShippingAddressForm(forms.ModelForm):
    discount_code = forms.CharField(
        required=False,
        label="Discount code (optional)",
        widget=forms.TextInput(attrs={"placeholder": "e.g. LOYAL10"}),
        help_text="Enter a discount code issued by the store.",
    )

    class Meta:
        model = ShippingAddress
        fields = [
            "full_name", "phone", "country",
            "street", "city", "state", "postal_code",
        ]
        widgets = {
            "country": forms.Select(choices=COUNTRY_CHOICES, attrs={"required": "required"}),
            "street": forms.TextInput(attrs={"placeholder": "Street address"}),
            "postal_code": forms.TextInput(attrs={"placeholder": "Optional"}),
        }

    def clean_country(self):
        country = self.cleaned_data.get("country")
        if not country:
            raise forms.ValidationError("Please choose your country so we can calculate shipping.")
        return country