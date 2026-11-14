import uuid

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    GOODS = "goods"
    SERVICE = "service"
    KIND_CHOICES = (
        (GOODS, "Goods"),
        (SERVICE, "Service"),
    )

    category = models.ForeignKey(Category, related_name="products", on_delete=models.PROTECT)
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default=GOODS)
    summary = models.CharField(max_length=240, blank=True)
    description = models.TextField(blank=True)
    specs = models.JSONField(default=list, blank=True)
    price_cents = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=64, blank=True)
    stock = models.PositiveIntegerField(null=True, blank=True)
    published = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["sku"],
                condition=~models.Q(sku=""),
                name="unique_sku_when_set",
            )
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def is_goods(self) -> bool:
        return self.kind == self.GOODS

    def in_stock(self) -> bool:
        if not self.is_goods:
            return False
        return self.stock is None or self.stock > 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=160, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.alt_text or f"Image for {self.product}"


class Order(models.Model):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"
    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (PAID, "Paid"),
        (CANCELED, "Canceled"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    email = models.EmailField(blank=True)
    subtotal_cents = models.PositiveIntegerField(default=0)
    shipping_cents = models.PositiveIntegerField(default=0)
    total_cents = models.PositiveIntegerField(default=0)
    stripe_session_id = models.CharField(max_length=255, blank=True)
    ship_name = models.CharField(max_length=160, blank=True)
    ship_line1 = models.CharField(max_length=160, blank=True)
    ship_line2 = models.CharField(max_length=160, blank=True)
    ship_city = models.CharField(max_length=80, blank=True)
    ship_region = models.CharField(max_length=80, blank=True)
    ship_postal = models.CharField(max_length=20, blank=True)
    ship_country = models.CharField(max_length=2, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.id} ({self.status})"


class OrderLine(models.Model):
    order = models.ForeignKey(Order, related_name="lines", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    product_name = models.CharField(max_length=160)
    sku = models.CharField(max_length=64, blank=True)
    unit_price_cents = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

    def line_total_cents(self) -> int:
        return self.unit_price_cents * self.quantity


class QuoteRequest(models.Model):
    name = models.CharField(max_length=120)
    contact = models.CharField(max_length=200)
    service = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.created_at:%Y-%m-%d})"
