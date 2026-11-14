from django.conf import settings

from catalog.models import Product

CART_KEY = "cart"


def get_cart(request) -> dict[int, int]:
    raw = request.session.get(CART_KEY, {})
    cart = {}
    for key, value in raw.items():
        try:
            cart[int(key)] = int(value)
        except (TypeError, ValueError):
            continue
    return cart


def save_cart(request, cart: dict[int, int]) -> None:
    request.session[CART_KEY] = {str(key): quantity for key, quantity in cart.items() if quantity > 0}
    request.session.modified = True


def clear_cart(request) -> None:
    request.session[CART_KEY] = {}
    request.session.modified = True


def count(request) -> int:
    if not hasattr(request, "session"):
        return 0
    return sum(get_cart(request).values())


def add(request, product: Product, quantity: int = 1) -> bool:
    if not product.is_goods or not product.published:
        return False
    cart = get_cart(request)
    next_quantity = min(99, cart.get(product.id, 0) + max(1, quantity))
    if product.stock is not None:
        next_quantity = min(next_quantity, product.stock)
    if next_quantity < 1:
        return False
    cart[product.id] = next_quantity
    save_cart(request, cart)
    return True


def set_quantity(request, product: Product, quantity: int) -> None:
    cart = get_cart(request)
    quantity = max(0, min(99, quantity))
    if product.stock is not None:
        quantity = min(quantity, product.stock)
    if quantity < 1:
        cart.pop(product.id, None)
    else:
        cart[product.id] = quantity
    save_cart(request, cart)


def shipping_cents(subtotal: int) -> int:
    if subtotal <= 0 or subtotal >= settings.FREE_SHIPPING_CENTS:
        return 0
    return settings.FLAT_SHIPPING_CENTS


def rows(request):
    cart = get_cart(request)
    products = {
        product.id: product
        for product in Product.objects.filter(
            id__in=cart.keys(),
            published=True,
            kind=Product.GOODS,
        )
    }
    cleaned = {}
    lines = []
    subtotal = 0
    for product_id, quantity in cart.items():
        product = products.get(product_id)
        if product is None:
            continue
        quantity = max(1, min(99, quantity))
        if product.stock is not None:
            quantity = min(quantity, product.stock)
        if quantity < 1:
            continue
        cleaned[product_id] = quantity
        line_total = product.price_cents * quantity
        subtotal += line_total
        lines.append(
            {
                "product": product,
                "quantity": quantity,
                "line_total": line_total,
            }
        )
    if cleaned != cart:
        save_cart(request, cleaned)
    lines.sort(key=lambda line: line["product"].name)
    shipping = shipping_cents(subtotal)
    return lines, subtotal, shipping, subtotal + shipping
