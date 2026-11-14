from django import forms
from django.contrib import admin

from catalog.models import Category, Order, OrderLine, Product, ProductImage, QuoteRequest


class SpecsWidget(forms.Textarea):
    def format_value(self, value):
        if not value:
            return ""
        if isinstance(value, str):
            return value
        return "\n".join(f"{row.get('label', '')} | {row.get('value', '')}" for row in value)


class ProductAdminForm(forms.ModelForm):
    specs = forms.CharField(
        required=False,
        widget=SpecsWidget(attrs={"rows": 8}),
        help_text="One spec per line, written as Label | Value.",
        label="Specs",
    )

    class Meta:
        model = Product
        fields = "__all__"

    def clean_specs(self):
        raw = self.cleaned_data.get("specs") or ""
        if isinstance(raw, list):
            return raw
        rows = []
        for line in str(raw).splitlines():
            if not line.strip():
                continue
            if "|" not in line:
                raise forms.ValidationError("Each spec needs a label and a value, separated by |.")
            label, value = line.split("|", 1)
            label, value = label.strip(), value.strip()
            if not label or not value:
                raise forms.ValidationError("Each spec needs both a label and a value.")
            rows.append({"label": label, "value": value})
        return rows


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ("name", "category", "kind", "price_cents", "stock", "published", "featured")
    list_filter = ("kind", "published", "category")
    search_fields = ("name", "sku")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    readonly_fields = ("product", "product_name", "sku", "unit_price_cents", "quantity")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "email", "total_cents", "created_at")
    list_filter = ("status",)
    readonly_fields = (
        "id",
        "email",
        "subtotal_cents",
        "shipping_cents",
        "total_cents",
        "stripe_session_id",
        "ship_name",
        "ship_line1",
        "ship_line2",
        "ship_city",
        "ship_region",
        "ship_postal",
        "ship_country",
        "created_at",
    )
    inlines = [OrderLineInline]


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "contact", "service", "created_at")
    readonly_fields = ("name", "contact", "service", "message", "created_at")
