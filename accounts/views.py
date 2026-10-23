import logging
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import RegisterForm, LoginForm ,ProfileForm

security_logger = logging.getLogger("security")


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("catalog:product_list")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(self.request, "Welcome to Classy Havens!")
        return redirect(self.success_url)


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        security_logger.info(
            "Login success user=%s role=%s superuser=%s ip=%s",
            user.username, user.role, user.is_superuser,
            self.request.META.get("REMOTE_ADDR"),
        )

        # Respect an explicit ?next= (e.g. /admin/ or a protected page)
        next_url = self.get_redirect_url()
        if next_url:
            return redirect(next_url)

        # Staff / superusers default to the dashboard
        if user.is_staff_member:
            return redirect("dashboard:index")

        return response

    def form_invalid(self, form):
        security_logger.warning(
            "Login failed user=%s ip=%s",
            form.cleaned_data.get("username"),
            self.request.META.get("REMOTE_ADDR"),
        )
        return super().form_invalid(form)


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("catalog:product_list")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})