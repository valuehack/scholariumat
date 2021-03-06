import os

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.urls import reverse

from users.models import Profile
from library.models import ZotItem
from products.models import Item, ItemType, Purchase, Payment
from donations.models import DonationLevel, Donation, PaymentMethod


class RequestPaymentTest(TestCase):
    def setUp(self):
        os.environ['RECAPTCHA_TESTING'] = 'True'
        self.client = Client()
        self.book = ZotItem.objects.create(title='Testbook', slug='testslug')
        self.itemtype = ItemType.objects.create(title='Kauf', buy_unauthenticated=True, requires_donation=False)
        self.item = Item.objects.create(type=self.itemtype, _price=10, product=self.book.product)
        self.method = PaymentMethod.objects.create(title='Bar')

    def test_payment(self):
        response = self.client.get(reverse('products:payment'))
        self.assertEqual(response.status_code, 302)
        post_data = {
            'email': 'a.b@c.de',
            'g-recaptcha-response': 'PASSED',
            'title': 'm',
            'name': '',
            'organization': '',
            'street': '',
            'postcode': '',
            'country': ''}
        response = self.client.post(response.url, post_data, follow=True)
        self.assertRedirects(response, reverse('products:payment'))
        profile = Profile.objects.get(user__email='a.b@c.de')
        self.assertTrue(profile)

        post_data = {
            'item': self.item.pk,
            'payment_method': self.method.pk
        }
        response = self.client.post(reverse('products:payment'), post_data)
        self.assertEqual(response.status_code, 302)

        payment = Payment.objects.get(profile=profile)
        response = self.client.post(reverse('products:approve', kwargs={'slug': payment.slug}), {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.level, None)
        self.assertEqual(profile.balance, 0)
        self.assertEqual(len(profile.purchases), 1)
        self.assertTrue(Payment.objects.get(profile=profile).executed)

    def tearDown(self):
        del os.environ['RECAPTCHA_TESTING']


class PurchaseTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(email='a.b@c.de')
        Profile.objects.create(user=self.user)
        self.user.profile.cart.delete()
        self.book = ZotItem.objects.create(title='Testbook', slug='testslug')
        self.itemtype = ItemType.objects.create(title='Kauf')
        self.item = Item.objects.create(type=self.itemtype, _price=10, amount=10, product=self.book.product)

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
        purchase = Purchase.objects.create(profile=self.user.profile, item=self.item, amount=3)
        self.assertEqual(purchase.total, 30)

    def test_buy_once(self):
        self.itemtype.buy_once = True
        self.itemtype.save()
        profile = self.user.profile
        profile.refill(10)
        self.item.add_to_cart(profile)
        self.item.add_to_cart(profile)
        self.assertEqual(profile.cart_total, 10)
        self.assertEqual(profile.cart.first().amount, 1)
        profile.execute_cart()
        self.assertEqual(profile.balance, 0)

    def test_discount(self):
        DonationLevel.objects.create(amount=75)
        lowest_donation = DonationLevel.get_lowest_amount()
        donation = Donation.objects.create(amount=lowest_donation, profile=self.user.profile)
        donation.execute()
        self.item.discounts.create(level=DonationLevel.get_level_by_amount(lowest_donation), discount=50)
        purchase = Purchase.objects.create(profile=self.user.profile, item=self.item, amount=1)
        purchase.execute()
        self.assertEqual(purchase.executed, True)
        self.assertEqual(self.user.profile.balance, 70)


class ItemTest(TestCase):
    def setUp(self):
        self.amount_start = 2
        self.price_start = 1
        self.user = get_user_model().objects.create(email='a.b@c.de')
        Profile.objects.create(user=self.user)
        self.book = ZotItem.objects.create(title='Testbook', slug='testslug')
        self.itemtype = ItemType.objects.create(title='Kauf')
        self.item = Item.objects.create(
            type=self.itemtype, _price=self.price_start, amount=self.amount_start, product=self.book.product)
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


class RequestTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(email='a.b@c.de')
        Profile.objects.create(user=self.user)
        self.book = ZotItem.objects.create(title='Testbook', slug='testslug')
        self.itemtype = ItemType.objects.create(title='Kauf', additional_supply=True)
        self.item = Item.objects.create(
            type=self.itemtype, _price=1, amount=0, product=self.book.product)

    def test_request(self):
        self.item.request(self.user)
        self.item.refill(1)

        # Assert item put in basket
        self.assertIsNotNone(self.user.profile.cart.all())
        self.assertEqual(self.item, self.user.profile.cart.first().item)

        # Assert admins and user are informed
        self.assertEqual(len(mail.outbox), 2)
