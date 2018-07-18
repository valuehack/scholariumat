from datetime import date, timedelta

from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model

from users.models import Profile
from donations.models import DonationLevel


class UserTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(email='a.b@c.de')
        Profile.objects.create(user=self.user)
        DonationLevel.objects.create(amount=75, title='Level 1')
        DonationLevel.objects.create(amount=150, title='Level 2')
        DonationLevel.objects.create(amount=300, title='Level 3')

    def test_user(self):
        user = get_user_model().objects.get(email='a.b@c.de')
        profile = user.profile

        # Test donation
        donation_amount = 200
        profile.donate(donation_amount)
        self.assertEqual(profile.balance, donation_amount)
        self.assertEqual(profile.donation.level.amount, 150)
        self.assertEqual(profile.level.amount, 150)
        self.assertEqual(profile.expiration, date.today() + timedelta(days=settings.DONATION_PERIOD))
