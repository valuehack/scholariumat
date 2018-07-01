from datetime import date, timedelta

from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model

from users.models import DonationLevel


class UserTest(TestCase):  # TODO: Split up in smaller tests.
    def setUp(self):
        get_user_model().objects.create(email='a.b@c.de', name='John Smith')
        DonationLevel.objects.create(amount=75, title='Level 1')
        DonationLevel.objects.create(amount=150, title='Level 2')
        DonationLevel.objects.create(amount=300, title='Level 3')

    def test_user(self):
        user = get_user_model().objects.get(email='a.b@c.de')
        # Test if profile with balance 0 got created
        profile = user.profile
        self.assertEqual(profile.balance, 0)
        self.assertEqual(profile.donation, None)
        self.assertEqual(profile.level, None)
        self.assertEqual(profile.expiration, None)
        self.assertEqual(profile.active, False)
        self.assertEqual(profile.expiring, False)
        # Test refill
        self.assertEqual(profile.spend(10), False)
        amount = 10
        profile.refill(amount)
        self.assertEqual(profile.balance, amount)
        self.assertEqual(profile.spend(amount), True)
        # Test donation
        donation_amount = 200
        profile.donate(donation_amount)
        self.assertEqual(profile.balance, donation_amount)
        self.assertEqual(profile.donation.level.amount, 150)
        self.assertEqual(profile.level.amount, 150)
        self.assertEqual(profile.expiration, date.today() + timedelta(days=settings.DONATION_PERIOD))
        # Test donation fail
        self.assertEqual(profile.donate(50), False)
