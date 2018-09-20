from django.test import TestCase
from django.contrib.auth import get_user_model

from users.models import Profile
from library.models import ZotItem
from products.models import Item, ItemType, Purchase


class ProductTest(TestCase):
    def setUp(self, price=10, amount=1):
        self.user = get_user_model().objects.create(email='a.b@c.de')
        Profile.objects.create(user=self.user)
        self.book = ZotItem.objects.create(title='Testbook', slug='testslug')
        self.itemtype = ItemType.objects.create(title='Kauf')
        self.item = Item.objects.create(type=self.itemtype, price=price, amount=amount, product=self.book.product)


class PurchaseTest(ProductTest):
    def setUp(self):
        self.amount_start = 10
        self.price_start = 10
        super().setUp(price=self.price_start, amount=self.amount_start)

    def test_balance(self):
        # Test if purchase fails if balance is not sufficient.
        purchase = Purchase.objects.create(profile=self.user.profile, item=self.item, amount=1)
        purchase.execute()
        self.assertEqual(purchase.executed, False)

        # Test if purchase works.
        self.user.profile.refill(10)
        purchase.execute()
        self.assertEqual(purchase.executed, True)
        self.assertEqual(self.user.profile.balance, 0)

    def test_purchase(self):
        # Test if total price works.
        amount = 3
        purchase = Purchase.objects.create(profile=self.user.profile, item=self.item, amount=3)
        self.assertEqual(purchase.total, amount * self.price_start)

    def test_buy_together(self):
        itemtype = ItemType.objects.create(title='Kauf2')
        self.itemtype.contains.add(itemtype)
        item2 = Item.objects.create(type=itemtype, price=1, amount=10, product=self.book.product)

        self.user.profile.refill(10)
        purchase = Purchase.objects.create(profile=self.user.profile, item=self.item, amount=1)
        purchase.execute()
        self.assertEqual(purchase.executed, True)
        self.assertIn(item2, self.user.profile.items_bought)
        
        # Test revert
        purchase.revert()
        self.assertNotIn(item2, self.user.profile.items_bought)


class ItemTest(ProductTest):
    def setUp(self):
        self.amount_start = 2
        self.price_start = 1
        super().setUp(price=self.price_start, amount=self.amount_start)
        self.user.profile.refill(10)

    def test_item(self):
        # Test if purchase fails if amount if not sufficient.
        purchase = Purchase.objects.create(profile=self.user.profile, item=self.item, amount=self.amount_start + 1)
        purchase.execute()
        self.assertEqual(purchase.executed, False)
        self.assertEqual(self.item.amount, self.amount_start)

        # Test if amount reduces.
        purchase = Purchase.objects.create(profile=self.user.profile, item=self.item, amount=1)
        purchase.execute()
        self.assertEqual(purchase.executed, True)
        self.assertEqual(self.item.amount, self.amount_start - 1)
