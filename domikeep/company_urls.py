from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from company import views

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.products, name="products"),
    path("products/<slug:category_slug>/", views.category, name="category"),
    path(
        "products/<slug:category_slug>/<slug:product_slug>/",
        views.product,
        name="product",
    ),
    path("solutions/", views.solutions, name="solutions"),
    path("support/", views.support, name="support"),
    path("about/", views.about, name="about"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
