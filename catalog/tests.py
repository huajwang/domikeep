from django.test import Client, TestCase

from catalog.models import Category, Product, QuoteRequest


class CategorySeedTests(TestCase):
    def test_empty_categories_are_created(self):
        self.assertEqual(
            list(Category.objects.order_by("sort_order").values_list("slug", flat=True)),
            ["cameras", "alarms", "locks", "lighting", "services"],
        )


class HostRoutingTests(TestCase):
    def test_company_and_shop_homes(self):
        company = Client()
        shop = Client()
        self.assertContains(company.get("/", HTTP_HOST="localhost"), "Domikeep Technologies Inc.")
        self.assertContains(shop.get("/", HTTP_HOST="emall.localhost"), "Devices in Canadian dollars")

    def test_www_redirects_to_apex(self):
        response = Client().get("/about/", HTTP_HOST="www.domikeep.com")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "https://domikeep.com/about/")

    def test_support_quote_is_stored(self):
        response = Client().post(
            "/support/",
            {"name": "Ada", "contact": "ada@example.com", "message": "Need a lock quote."},
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(QuoteRequest.objects.count(), 1)


class ShopFlowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test locks", slug="test-locks", sort_order=99)
        self.goods = Product.objects.create(
            category=self.category,
            name="Entry lock",
            slug="entry-lock",
            kind=Product.GOODS,
            price_cents=12000,
            stock=2,
            published=True,
        )
        self.service = Product.objects.create(
            category=self.category,
            name="Install a lock",
            slug="install-a-lock",
            kind=Product.SERVICE,
            published=True,
        )

    def test_service_is_not_added_to_the_cart(self):
        client = Client()
        response = client.post(
            f"/cart/add/{self.service.id}/",
            HTTP_HOST="emall.localhost",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.session.get("cart"), None)

    def test_cart_totals_and_free_shipping(self):
        client = Client()
        self.assertEqual(
            client.post(
                f"/cart/add/{self.goods.id}/",
                {"quantity": "2"},
                HTTP_HOST="emall.localhost",
            ).status_code,
            302,
        )
        page = client.get("/cart/", HTTP_HOST="emall.localhost")
        self.assertContains(page, "$240.00")
        self.assertContains(page, "Shipping $0.00")

    def test_checkout_without_stripe_does_not_create_an_order(self):
        from catalog.models import Order

        client = Client()
        client.post(f"/cart/add/{self.goods.id}/", HTTP_HOST="emall.localhost")
        response = client.post("/checkout/", HTTP_HOST="emall.localhost")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 0)

    def test_paid_session_decrements_stock_once(self):
        from catalog.models import Order, OrderLine
        from shop.payments import apply_paid_session

        order = Order.objects.create(subtotal_cents=12000, shipping_cents=0, total_cents=12000)
        OrderLine.objects.create(
            order=order,
            product=self.goods,
            product_name="Entry lock",
            unit_price_cents=12000,
            quantity=1,
        )
        session = {
            "metadata": {"order_id": str(order.id)},
            "payment_status": "paid",
            "customer_details": {
                "email": "ada@example.com",
                "name": "Ada",
                "address": {
                    "line1": "1 Road",
                    "line2": "",
                    "city": "Montreal",
                    "state": "QC",
                    "postal_code": "H2X 1Y4",
                    "country": "CA",
                },
            },
        }
        apply_paid_session(session)
        apply_paid_session(session)
        self.goods.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(order.status, Order.PAID)
        self.assertEqual(order.email, "ada@example.com")
        self.assertEqual(self.goods.stock, 1)

    def test_service_quote(self):
        response = Client().post(
            f"/quote/{self.service.id}/",
            {"name": "Lin", "contact": "555-0100", "message": "Front door."},
            HTTP_HOST="emall.localhost",
        )
        self.assertEqual(response.status_code, 302)
        quote = QuoteRequest.objects.get()
        self.assertEqual(quote.service, self.service)
