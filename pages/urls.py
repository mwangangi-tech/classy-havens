from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [
    path("faq/", views.FAQView.as_view(), name="faq"),
    path("shipping/", views.ShippingView.as_view(), name="shipping"),
    path("size-guide/", views.SizeGuideView.as_view(), name="size_guide"),
    path("privacy/", views.PrivacyView.as_view(), name="privacy"),
    path("terms/", views.TermsView.as_view(), name="terms"),
    path("contact/", views.contact_view, name="contact"),
    path("newsletter/", views.newsletter_subscribe, name="newsletter"),
]