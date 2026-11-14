from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from catalog.forms import QuoteForm
from catalog.models import Category, Product, QuoteRequest


def home(request):
    featured = (
        Product.objects.filter(published=True, featured=True).select_related("category").first()
        or Product.objects.filter(published=True, kind=Product.GOODS).select_related("category").first()
    )
    return render(
        request,
        "company/home.html",
        {
            "featured": featured,
            "categories": Category.objects.all(),
        },
    )


def products(request):
    return render(request, "company/products.html", {"categories": Category.objects.all()})


def category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    items = category.products.filter(published=True).prefetch_related("images")
    return render(
        request,
        "company/category.html",
        {"category": category, "products": items},
    )


def product(request, category_slug, product_slug):
    item = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images"),
        category__slug=category_slug,
        slug=product_slug,
        published=True,
    )
    return render(request, "company/product.html", {"product": item})


def solutions(request):
    return render(request, "company/solutions.html")


def support(request):
    form = QuoteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        QuoteRequest.objects.create(
            name=form.cleaned_data["name"],
            contact=form.cleaned_data["contact"],
            message=form.cleaned_data["message"],
        )
        messages.success(request, "Message received. We will reply at the contact you gave.")
        return redirect("support")
    return render(
        request,
        "company/support.html",
        {
            "form": form,
            "flat_shipping": settings.FLAT_SHIPPING_CENTS,
            "free_shipping": settings.FREE_SHIPPING_CENTS,
        },
    )


def about(request):
    return render(request, "company/about.html")
