from django import forms
from django.core.exceptions import ValidationError

from .models import Discount


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = [
            "recipient", "code", "description", "discount_type", "value",
            "min_spend", "max_uses", "is_active",
            "valid_from", "valid_until",
        ]
        widgets = {
            "valid_from": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M",
            ),
            "valid_until": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M",
            ),
            "description": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("valid_from", "valid_until"):
            self.fields[name].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"]

    def clean_code(self):
        code = (self.cleaned_data["code"] or "").strip().upper()
        if not code:
            raise ValidationError("Code is required.")
        qs = Discount.objects.filter(code__iexact=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A discount with this code already exists.")
        return code

    def clean_value(self):
        v = self.cleaned_data["value"]
        if v is None or v <= 0:
            raise ValidationError("Value must be greater than zero.")
        if self.cleaned_data.get("discount_type") == Discount.Type.PERCENT and v > 100:
            raise ValidationError("Percentage discount cannot exceed 100%.")
        return v