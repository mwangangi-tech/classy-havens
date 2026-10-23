from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardIndex.as_view(), name="index"),

    # Orders
    path("orders/", views.OrderManagementView.as_view(), name="orders"),
    path("orders/<int:pk>/edit/", views.OrderStatusUpdateView.as_view(), name="order_edit"),

    # Categories
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("categories/add/", views.CategoryCreateView.as_view(), name="category_add"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_edit"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),

    # Products
    path("products/", views.ProductManagementView.as_view(), name="products"),
    path("products/add/", views.ProductCreateView.as_view(), name="product_add"),
    path("products/<int:pk>/edit/", views.ProductUpdateView.as_view(), name="product_edit"),
    path("products/<int:pk>/delete/", views.ProductDeleteView.as_view(), name="product_delete"),

    # Reviews
    path("reviews/", views.ReviewModerationView.as_view(), name="reviews"),
    path("reviews/<int:pk>/toggle/", views.ReviewApproveToggleView.as_view(), name="review_toggle"),
    path("reviews/<int:pk>/delete/", views.ReviewDeleteView.as_view(), name="review_delete"),

    # Sales
    path("sales/", views.SalesOverviewView.as_view(), name="sales"),

    # Inventory
    path("inventory/", views.InventoryView.as_view(), name="inventory"),
    path("inventory/<int:pk>/edit/", views.InventoryUpdateView.as_view(), name="inventory_edit"),

    # Staff
    path("staff/", views.StaffListView.as_view(), name="staff_list"),
    path("staff/add/", views.StaffCreateView.as_view(), name="staff_add"),
    path("staff/<int:pk>/edit/", views.StaffUpdateView.as_view(), name="staff_edit"),

    # Staff documents
    path("staff-documents/", views.StaffDocumentListView.as_view(), name="staff_documents"),
    path("staff-documents/upload/", views.StaffDocumentUploadView.as_view(), name="staff_document_add"),
    path("staff-documents/<int:pk>/download/", views.StaffDocumentDownloadView.as_view(), name="staff_document_download"),
    path("staff-documents/<int:pk>/delete/", views.StaffDocumentDeleteView.as_view(), name="staff_document_delete"),
]