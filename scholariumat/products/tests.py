from django.test import TestCase
from django.contrib.auth import get_user_model

from library.models import Book
from products.models import Item, ItemType, Purchase


class ProductTest(TestCase):
    def setUp(self, price=10, amount=1):
        self.user = get_user_model().objects.create(email='mb@scholarium.at')
        self.book = Book.objects.create(title='Testbook', slug='testslug')
        itemtype = ItemType.objects.create(title='Kauf')
        self.item = Item.objects.create(type=itemtype, price=price, amount=amount, product=self.book.product)


class PurchaseTest(ProductTest):
    def setUp(self):
        self.amount_start = 10
        self.price_start = 10
        super(PurchaseTest, self).setUp(price=self.price_start, amount=self.amount_start)

    def test_balance(self):
        # Test if purchase fails if balance is not sufficient.
        purchase = Purchase.objects.create(profile=self.user.profile, item=self.item, amount=1)
        purchase.apply()
        self.assertEqual(purchase.applied, False)

        # Test if purchase works.
        self.user.profile.refill(10)
        purchase.apply()
        self.assertEqual(purchase.applied, True)
        self.assertEqual(self.user.profile.balance, 0)

    def test_purchase(self):
        # Test if total price works.
        amount = 3
        purchase = Purchase.objects.create(profile=self.user.profile, item=self.item, amount=3)
        self.assertEqual(purchase.total, amount * self.price_start)


class ItemTest(ProductTest):
    def setUp(self):
        self.amount_start = 2
        self.price_start = 1
        super(ItemTest, self).setUp(price=self.price_start, amount=self.amount_start)
        self.user.profile.refill(10)

    def test_item(self):
        # Test if purchase fails if amount if not sufficient.
        purchase = Purchase.objects.create(profile=self.user.profile, item=self.item, amount=self.amount_start + 1)
        purchase.apply()
        self.assertEqual(purchase.applied, False)
        self.assertEqual(self.item.amount, self.amount_start)

        # Test if amount reduces.
        purchase = Purchase.objects.create(profile=self.user.profile, item=self.item, amount=1)
        purchase.apply()
        self.assertEqual(purchase.applied, True)
        self.assertEqual(self.item.amount, self.amount_start - 1)
