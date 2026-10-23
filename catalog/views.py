from django.views.generic import ListView, DetailView
from .models import Product, Category


class ProductListView(ListView):
    model = Product
    template_name = "catalog/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related("category")
        category_slug = self.kwargs.get("category_slug")
        q = self.request.GET.get("q")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.all()
        ctx["active_category"] = self.kwargs.get("category_slug")
        ctx["search_query"] = self.request.GET.get("q", "")
        return ctx


class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.filter(is_active=True).prefetch_related("variants", "reviews")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["variants"] = self.object.variants.filter(stock__gt=0)
        ctx["reviews"] = self.object.reviews.filter(is_approved=True).select_related("user")
        return ctx