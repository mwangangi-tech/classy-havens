from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.generic import TemplateView
from .models import NewsletterSubscriber
from .forms import ContactForm
from .models import ContactMessage
# --- Static Pages ---
class FAQView(TemplateView):
    template_name = "pages/faq.html"

class ShippingView(TemplateView):
    template_name = "pages/shipping.html"

class SizeGuideView(TemplateView):
    template_name = "pages/size_guide.html"

class PrivacyView(TemplateView):
    template_name = "pages/privacy.html"

class TermsView(TemplateView):
    template_name = "pages/terms.html"


def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactMessage.objects.create(
                name=form.cleaned_data["name"],
                email=form.cleaned_data["email"],
                subject=form.cleaned_data["subject"],
                message=form.cleaned_data["message"],
            )
            messages.success(request, "Thank you! Your message has been received. Our team will reply to your email shortly.")
            return redirect("pages:contact")
    else:
        form = ContactForm()
    
    return render(request, "pages/contact.html", {"form": form})

# --- Newsletter ---
def newsletter_subscribe(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if email:
            try:
                NewsletterSubscriber.objects.create(email=email)
                messages.success(request, "Welcome to the list! Check your inbox for your 10% discount code.")
            except Exception:
                # IntegrityError if email already exists
                messages.info(request, "You are already subscribed to our newsletter.")
        else:
            messages.error(request, "Please provide a valid email address.")
            
    # Redirect back to wherever the user came from
    referer = request.META.get("HTTP_REFERER", "/")
    return redirect(referer)