from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from catalog.forms import QuoteForm
from catalog.models import Category, Order, OrderLine, Product, QuoteRequest
from shop.cart import add, clear_cart, rows, set_quantity
from shop.payments import apply_paid_session, create_checkout, stripe_client


def home(request):
    return render(
        request,
        "shop/home.html",
        {"categories": Category.objects.all()},
    )


def category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    items = category.products.filter(published=True).prefetch_related("images")
    return render(
        request,
        "shop/category.html",
        {"category": category, "products": items},
    )


def product(request, product_slug):
    item = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images"),
        slug=product_slug,
        published=True,
    )
    form = QuoteForm() if not item.is_goods else None
    return render(request, "shop/product.html", {"product": item, "form": form})


def cart_view(request):
    lines, subtotal, shipping, total = rows(request)
    return render(
        request,
        "shop/cart.html",
        {
            "lines": lines,
            "subtotal": subtotal,
            "shipping": shipping,
            "total": total,
            "canceled": request.GET.get("canceled") == "1",
        },
    )


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, published=True)
    if not product.is_goods:
        messages.error(request, "Services are arranged with a quote, not a cart.")
        return redirect("product", product_slug=product.slug)
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except ValueError:
        quantity = 1
    if not add(request, product, quantity):
        messages.error(request, "That item is not available to add.")
    else:
        messages.success(request, f"{product.name} added to the cart.")
    return redirect("cart")


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, pk=product_id, published=True, kind=Product.GOODS)
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except ValueError:
        quantity = 1
    set_quantity(request, product, quantity)
    return redirect("cart")


@require_POST
def checkout(request):
    lines, subtotal, shipping, total = rows(request)
    if not lines:
        messages.error(request, "The cart is empty.")
        return redirect("cart")
    if not settings.STRIPE_SECRET_KEY:
        messages.error(request, "Card checkout is not connected yet. Email us and we will take the order.")
        return redirect("cart")
    order = Order.objects.create(
        subtotal_cents=subtotal,
        shipping_cents=shipping,
        total_cents=total,
    )
    OrderLine.objects.bulk_create(
        [
            OrderLine(
                order=order,
                product=line["product"],
                product_name=line["product"].name,
                sku=line["product"].sku,
                unit_price_cents=line["product"].price_cents,
                quantity=line["quantity"],
            )
            for line in lines
        ]
    )
    return redirect(create_checkout(order, settings.SHOP_ORIGIN))


def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("lines"), pk=order_id)
    session_id = request.GET.get("session_id")
    if session_id and settings.STRIPE_SECRET_KEY and order.status != Order.PAID:
        stripe = stripe_client()
        session = stripe.checkout.Session.retrieve(session_id)
        if str(session.get("metadata", {}).get("order_id")) == str(order.id):
            apply_paid_session(session)
            order.refresh_from_db()
            if order.status == Order.PAID:
                clear_cart(request)
    return render(request, "shop/order.html", {"order": order})


def quote(request, product_id=None):
    service = None
    if product_id is not None:
        service = get_object_or_404(Product, pk=product_id, published=True, kind=Product.SERVICE)
    form = QuoteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        QuoteRequest.objects.create(
            name=form.cleaned_data["name"],
            contact=form.cleaned_data["contact"],
            service=service,
            message=form.cleaned_data["message"],
        )
        messages.success(request, "Quote request received. We will reply at the contact you gave.")
        return redirect("home")
    return render(request, "shop/quote.html", {"form": form, "service": service})


@csrf_exempt
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponseBadRequest("Webhook secret is not set.")
    stripe = stripe_client()
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            request.META.get("HTTP_STRIPE_SIGNATURE", ""),
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponseBadRequest("Invalid payload.")
    if event["type"] == "checkout.session.completed":
        apply_paid_session(event["data"]["object"])
    return HttpResponse(status=200)
