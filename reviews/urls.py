from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("submit/<slug:product_slug>/", views.submit_review, name="submit"),
]