from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "title", "body"]
        widgets = {
            "rating": forms.Select(choices=[(i, f"{i} ★") for i in range(5, 0, -1)]),
            "body": forms.Textarea(attrs={"rows": 5}),
        }