from django.conf import settings
from django.db import transaction

from catalog.models import Order


def stripe_client():
    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def create_checkout(order: Order, shop_origin: str) -> str:
    stripe = stripe_client()
    line_items = [
        {
            "quantity": line.quantity,
            "price_data": {
                "currency": "cad",
                "unit_amount": line.unit_price_cents,
                "product_data": {"name": line.product_name},
            },
        }
        for line in order.lines.all()
    ]
    if order.shipping_cents:
        line_items.append(
            {
                "quantity": 1,
                "price_data": {
                    "currency": "cad",
                    "unit_amount": order.shipping_cents,
                    "product_data": {"name": "Shipping in Canada"},
                },
            }
        )
    session = stripe.checkout.Session.create(
        mode="payment",
        currency="cad",
        line_items=line_items,
        shipping_address_collection={"allowed_countries": ["CA"]},
        success_url=f"{shop_origin}/orders/{order.id}/?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{shop_origin}/cart/?canceled=1",
        metadata={"order_id": str(order.id)},
    )
    order.stripe_session_id = session.id
    order.save(update_fields=["stripe_session_id"])
    return session.url


def apply_paid_session(session) -> Order | None:
    metadata = session.get("metadata") or {}
    order_id = metadata.get("order_id")
    if not order_id:
        return None
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.status == Order.PAID:
            return order
        if session.get("payment_status") != "paid":
            return order
        details = session.get("customer_details") or {}
        address = details.get("address") or {}
        order.status = Order.PAID
        order.email = details.get("email") or order.email
        order.ship_name = details.get("name") or ""
        order.ship_line1 = address.get("line1") or ""
        order.ship_line2 = address.get("line2") or ""
        order.ship_city = address.get("city") or ""
        order.ship_region = address.get("state") or ""
        order.ship_postal = address.get("postal_code") or ""
        order.ship_country = address.get("country") or ""
        order.save()
        for line in order.lines.select_related("product"):
            product = line.product
            if product is None or product.stock is None:
                continue
            product.stock = max(0, product.stock - line.quantity)
            product.save(update_fields=["stock"])
        return order
