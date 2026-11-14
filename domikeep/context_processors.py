from django.conf import settings

from catalog.models import Category
from shop.cart import count as cart_count


def site(request):
    kind = getattr(request, "site_kind", "company")
    return {
        "site_kind": kind,
        "shop_origin": settings.SHOP_ORIGIN,
        "company_origin": settings.COMPANY_ORIGIN,
        "contact_email": settings.CONTACT_EMAIL,
        "contact_phone": settings.CONTACT_PHONE,
        "flat_shipping_cents": settings.FLAT_SHIPPING_CENTS,
        "free_shipping_cents": settings.FREE_SHIPPING_CENTS,
        "stripe_ready": bool(settings.STRIPE_SECRET_KEY),
        "nav_categories": Category.objects.all(),
        "cart_count": cart_count(request) if kind == "shop" else 0,
    }
