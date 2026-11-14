from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from shop import views

urlpatterns = [
    path("", views.home, name="home"),
    path("c/<slug:category_slug>/", views.category, name="category"),
    path("p/<slug:product_slug>/", views.product, name="product"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/<uuid:order_id>/", views.order_detail, name="order"),
    path("quote/", views.quote, name="quote"),
    path("quote/<int:product_id>/", views.quote, name="quote_for"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
