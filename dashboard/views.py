import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models import ProtectedError
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    TemplateView, ListView, UpdateView, CreateView, DeleteView,
)

from accounts.crypto import encrypt_document, decrypt_document
from accounts.forms import StaffDocumentForm
from accounts.models import CustomUser, StaffDocument
from catalog.models import Category, Product, ProductVariant
from orders.models import Order, OrderItem
from reviews.models import Review

from .forms import (
    CategoryForm, ProductForm, ProductVariantFormSet, InventoryForm,
    StaffCreateForm, StaffUpdateForm,
)

logger = logging.getLogger("security")


class StaffRequiredMixin(LoginRequiredMixin):
    """
    Grants access only to staff members: superusers, is_staff users,
    or roles staff/manager/admin. Does NOT itself require a model
    permission — individual views may add PermissionRequiredMixin.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not request.user.is_staff_member:
            messages.error(request, "Staff access required.")
            return redirect("catalog:product_list")
        return super().dispatch(request, *args, **kwargs)


# ============================================================
# Overview
# ============================================================
class DashboardIndex(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        paid = Order.objects.filter(
            status__in=[Order.Status.PAID, Order.Status.SHIPPED, Order.Status.DELIVERED],
        )
        ctx["order_count"]     = Order.objects.count()
        ctx["pending_orders"]  = Order.objects.filter(status=Order.Status.PENDING).count()
        ctx["product_count"]   = Product.objects.filter(is_active=True).count()
        ctx["pending_reviews"] = Review.objects.filter(is_approved=False).count()
        ctx["revenue"]         = paid.aggregate(s=Sum("total"))["s"] or 0
        ctx["recent_orders"]   = Order.objects.select_related("user").order_by("-created_at")[:10]
        return ctx


# ============================================================
# Orders
# ============================================================
class OrderManagementView(StaffRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "orders.view_order"
    model = Order
    template_name = "dashboard/orders.html"
    context_object_name = "orders"
    paginate_by = 50

    def get_queryset(self):
        qs = Order.objects.select_related("user").order_by("-created_at")
        status = self.request.GET.get("status")
        if status in dict(Order.Status.choices):
            qs = qs.filter(status=status)
        return qs


class OrderStatusUpdateView(StaffRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "orders.change_order"
    model = Order
    fields = ["status"]
    template_name = "dashboard/order_update.html"
    success_url = reverse_lazy("dashboard:orders")

    def form_valid(self, form):
        messages.success(self.request, "Order status updated.")
        return super().form_valid(form)


# ============================================================
# Categories
# ============================================================
class CategoryListView(StaffRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "catalog.view_category"
    model = Category
    template_name = "dashboard/category_list.html"
    context_object_name = "categories"
    paginate_by = 50

    def get_queryset(self):
        return Category.objects.annotate(
            product_count=Count("products"),
        ).order_by("sort_order", "name")


class CategoryCreateView(StaffRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "catalog.add_category"
    model = Category
    form_class = CategoryForm
    template_name = "dashboard/category_form.html"
    success_url = reverse_lazy("dashboard:categories")

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(
            "category_created id=%s name=%r user=%s",
            self.object.pk, self.object.name, self.request.user.username,
        )
        messages.success(self.request, f"Category '{self.object.name}' created.")
        return response


class CategoryUpdateView(StaffRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "catalog.change_category"
    model = Category
    form_class = CategoryForm
    template_name = "dashboard/category_form.html"
    success_url = reverse_lazy("dashboard:categories")

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(
            "category_updated id=%s name=%r user=%s",
            self.object.pk, self.object.name, self.request.user.username,
        )
        messages.success(self.request, f"Category '{self.object.name}' updated.")
        return response


class CategoryDeleteView(StaffRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "catalog.delete_category"
    model = Category
    template_name = "dashboard/category_confirm_delete.html"
    success_url = reverse_lazy("dashboard:categories")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product_count"] = self.object.products.count()
        return ctx

    def form_valid(self, form):
        name = self.object.name
        try:
            response = super().form_valid(form)
        except ProtectedError:
            count = self.object.products.count()
            logger.warning(
                "category_delete_protected id=%s products=%s user=%s",
                self.object.pk, count, self.request.user.username,
            )
            messages.error(
                self.request,
                f"Cannot delete '{name}' — {count} product(s) still use it. "
                "Reassign those products to another category first.",
            )
            return redirect("dashboard:categories")
        logger.info(
            "category_deleted name=%r user=%s",
            name, self.request.user.username,
        )
        messages.success(self.request, f"Category '{name}' deleted.")
        return response


# ============================================================
# Products
# ============================================================
class ProductManagementView(StaffRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "catalog.view_product"
    model = Product
    template_name = "dashboard/products.html"
    context_object_name = "products"
    paginate_by = 50

    def get_queryset(self):
        qs = Product.objects.select_related("category").order_by("-created_at")
        category_id = self.request.GET.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["all_categories"] = Category.objects.all()
        ctx["selected_category"] = self.request.GET.get("category", "")
        return ctx


class ProductCreateView(StaffRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "catalog.add_product"
    model = Product
    form_class = ProductForm
    template_name = "dashboard/product_form.html"
    success_url = reverse_lazy("dashboard:products")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["has_categories"] = Category.objects.exists()
        if self.request.POST:
            ctx["formset"] = ProductVariantFormSet(
                self.request.POST, self.request.FILES, prefix="variants",
            )
        else:
            ctx["formset"] = ProductVariantFormSet(prefix="variants")
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        formset = ctx["formset"]
        if not formset.is_valid():
            logger.warning(
                "product_create_formset_invalid user=%s errors=%s",
                self.request.user.username, formset.errors,
            )
            messages.error(
                self.request,
                "Please fix the variant rows — every row must have a Size, "
                "Colour, SKU and Stock value.",
            )
            return self.render_to_response(ctx)
        try:
            with transaction.atomic():
                self.object = form.save()
                formset.instance = self.object
                formset.save()
        except Exception as exc:
            logger.exception(
                "product_create_save_error user=%s exc=%s",
                self.request.user.username, exc,
            )
            messages.error(self.request, f"Could not save product: {exc}")
            return self.render_to_response(ctx)
        logger.info(
            "product_created id=%s name=%r user=%s",
            self.object.pk, self.object.name, self.request.user.username,
        )
        messages.success(self.request, f"Product '{self.object.name}' created.")
        return redirect(self.success_url)


class ProductUpdateView(StaffRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "catalog.change_product"
    model = Product
    form_class = ProductForm
    template_name = "dashboard/product_form.html"
    success_url = reverse_lazy("dashboard:products")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["has_categories"] = Category.objects.exists()
        if self.request.POST:
            ctx["formset"] = ProductVariantFormSet(
                self.request.POST, self.request.FILES,
                instance=self.object, prefix="variants",
            )
        else:
            ctx["formset"] = ProductVariantFormSet(
                instance=self.object, prefix="variants",
            )
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        formset = ctx["formset"]
        if not formset.is_valid():
            logger.warning(
                "product_update_formset_invalid id=%s errors=%s",
                self.object.pk, formset.errors,
            )
            messages.error(self.request, "Please fix the variant rows.")
            return self.render_to_response(ctx)
        try:
            with transaction.atomic():
                self.object = form.save()
                formset.instance = self.object
                formset.save()
        except Exception as exc:
            logger.exception(
                "product_update_save_error id=%s exc=%s", self.object.pk, exc,
            )
            messages.error(self.request, f"Could not save product: {exc}")
            return self.render_to_response(ctx)
        logger.info(
            "product_updated id=%s user=%s",
            self.object.pk, self.request.user.username,
        )
        messages.success(self.request, f"Product '{self.object.name}' updated.")
        return redirect(self.success_url)


class ProductDeleteView(StaffRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "catalog.delete_product"
    model = Product
    template_name = "dashboard/product_confirm_delete.html"
    success_url = reverse_lazy("dashboard:products")

    def form_valid(self, form):
        messages.success(self.request, "Product deleted.")
        return super().form_valid(form)


# ============================================================
# Reviews
# ============================================================
class ReviewModerationView(StaffRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "reviews.view_review"
    model = Review
    template_name = "dashboard/reviews.html"
    context_object_name = "reviews"
    paginate_by = 50

    def get_queryset(self):
        qs = Review.objects.select_related("product", "user").order_by("-created_at")
        approved = self.request.GET.get("approved")
        if approved == "yes":
            qs = qs.filter(is_approved=True)
        elif approved == "no":
            qs = qs.filter(is_approved=False)
        return qs


class ReviewApproveToggleView(StaffRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "reviews.change_review"

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        review.is_approved = not review.is_approved
        review.save(update_fields=["is_approved"])
        messages.success(
            request,
            f"Review {'approved' if review.is_approved else 'unapproved'}.",
        )
        return redirect("dashboard:reviews")


class ReviewDeleteView(StaffRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "reviews.delete_review"

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        review.delete()
        messages.success(request, "Review deleted.")
        return redirect("dashboard:reviews")


# ============================================================
# Sales
# ============================================================
class SalesOverviewView(StaffRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "orders.view_order"
    template_name = "dashboard/sales.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        paid_statuses = [Order.Status.PAID, Order.Status.SHIPPED, Order.Status.DELIVERED]
        paid = Order.objects.filter(status__in=paid_statuses)
        now = timezone.now()
        today = now.date()

        ctx["total_revenue"] = paid.aggregate(s=Sum("total"))["s"] or 0
        ctx["today_revenue"] = (
            paid.filter(paid_at__date=today).aggregate(s=Sum("total"))["s"] or 0
        )
        ctx["week_revenue"] = (
            paid.filter(paid_at__gte=now - timedelta(days=7))
                .aggregate(s=Sum("total"))["s"] or 0
        )
        ctx["month_revenue"] = (
            paid.filter(paid_at__gte=now - timedelta(days=30))
                .aggregate(s=Sum("total"))["s"] or 0
        )
        ctx["total_orders"]  = Order.objects.count()
        ctx["paid_orders"]   = paid.count()
        ctx["average_order"] = (
            (ctx["total_revenue"] / ctx["paid_orders"]) if ctx["paid_orders"] else 0
        )
        ctx["status_breakdown"] = (
            Order.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        line_total = ExpressionWrapper(
            F("quantity") * F("unit_price"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        ctx["top_products"] = (
            OrderItem.objects.filter(order__status__in=paid_statuses)
            .values("variant__product__name")
            .annotate(sold=Sum("quantity"), revenue=Sum(line_total))
            .order_by("-sold")[:10]
        )
        ctx["recent_paid"] = paid.select_related("user").order_by("-paid_at")[:15]
        return ctx


# ============================================================
# Inventory
# ============================================================
class InventoryView(StaffRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "catalog.view_productvariant"
    template_name = "dashboard/inventory.html"
    LOW_STOCK_THRESHOLD = 5

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        variants = (
            ProductVariant.objects.select_related("product", "product__category")
            .order_by("stock", "product__name", "size")
        )
        ctx["variants"]     = variants
        ctx["low_stock"]    = variants.filter(stock__lt=self.LOW_STOCK_THRESHOLD, stock__gt=0)
        ctx["out_of_stock"] = variants.filter(stock=0)
        ctx["total_units"]  = variants.aggregate(s=Sum("stock"))["s"] or 0
        ctx["total_value"]  = sum(v.stock * v.price for v in variants)
        ctx["low_threshold"] = self.LOW_STOCK_THRESHOLD
        return ctx


class InventoryUpdateView(StaffRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "catalog.change_productvariant"
    model = ProductVariant
    form_class = InventoryForm
    template_name = "dashboard/inventory_form.html"
    success_url = reverse_lazy("dashboard:inventory")

    def form_valid(self, form):
        messages.success(self.request, f"Stock updated for {self.object}.")
        return super().form_valid(form)


# ============================================================
# Staff management
# ============================================================
class StaffListView(StaffRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "accounts.view_customuser"
    template_name = "dashboard/staff_list.html"
    context_object_name = "staff"
    paginate_by = 50

    def get_queryset(self):
        return CustomUser.objects.filter(
            role__in=[CustomUser.Roles.STAFF,
                      CustomUser.Roles.MANAGER,
                      CustomUser.Roles.ADMIN],
        ).order_by("-date_joined")


class StaffCreateView(StaffRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "accounts.add_customuser"
    model = CustomUser
    form_class = StaffCreateForm
    template_name = "dashboard/staff_form.html"
    success_url = reverse_lazy("dashboard:staff_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            f"Staff account '{form.cleaned_data['username']}' created.",
        )
        return super().form_valid(form)


class StaffUpdateView(StaffRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "accounts.change_customuser"
    model = CustomUser
    form_class = StaffUpdateForm
    template_name = "dashboard/staff_form.html"
    success_url = reverse_lazy("dashboard:staff_list")

    def get_queryset(self):
        return CustomUser.objects.filter(is_superuser=False)

    def form_valid(self, form):
        messages.success(self.request, "Staff account updated.")
        return super().form_valid(form)


# ============================================================
# Staff documents
# ============================================================
class StaffDocumentListView(StaffRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "accounts.view_staffdocument"
    template_name = "dashboard/staff_documents.html"
    context_object_name = "documents"
    paginate_by = 50

    def get_queryset(self):
        qs = StaffDocument.objects.select_related("user", "uploaded_by")
        if not (self.request.user.is_superuser
                or self.request.user.role in ("manager", "admin")):
            qs = qs.filter(user=self.request.user)
        return qs.order_by("-created_at")


class StaffDocumentUploadView(StaffRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "accounts.add_staffdocument"
    template_name = "dashboard/staff_document_form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": StaffDocumentForm()})

    def post(self, request):
        form = StaffDocumentForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        uploaded = form.cleaned_data["file"]
        plaintext = uploaded.read()
        ciphertext, salt = encrypt_document(plaintext)

        StaffDocument.objects.create(
            user=form.cleaned_data["user"],
            document_type=form.cleaned_data["document_type"],
            title=form.cleaned_data["title"],
            original_filename=uploaded.name,
            content_type=uploaded.content_type,
            file_size=len(plaintext),
            encrypted_data=ciphertext,
            salt=salt,
            uploaded_by=request.user,
        )
        messages.success(
            request,
            f"Document '{form.cleaned_data['title']}' uploaded and encrypted.",
        )
        return redirect("dashboard:staff_documents")


class StaffDocumentDownloadView(StaffRequiredMixin, View):
    def get(self, request, pk):
        doc = get_object_or_404(StaffDocument, pk=pk)
        allowed = (
            request.user.is_superuser
            or request.user == doc.user
            or request.user.role in ("manager", "admin")
        )
        if not allowed:
            messages.error(request, "You do not have access to that document.")
            return redirect("dashboard:staff_documents")

        plaintext = decrypt_document(bytes(doc.encrypted_data), bytes(doc.salt))
        logger.info(
            "staff_document_download id=%s by=%s", doc.pk, request.user.username,
        )
        response = HttpResponse(plaintext, content_type=doc.content_type)
        response["Content-Disposition"] = (
            f'attachment; filename="{doc.original_filename}"'
        )
        return response


class StaffDocumentDeleteView(StaffRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "accounts.delete_staffdocument"

    def post(self, request, pk):
        doc = get_object_or_404(StaffDocument, pk=pk)
        title = doc.title
        doc.delete()
        logger.info(
            "staff_document_deleted id=%s title=%r by=%s",
            pk, title, request.user.username,
        )
        messages.success(request, f"Document '{title}' deleted.")
        return redirect("dashboard:staff_documents")