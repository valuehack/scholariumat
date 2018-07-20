from datetime import date, timedelta

from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from users.models import Profile
from donations.models import DonationLevel


class RequestDonationTest(TestCase):
    def setUp(self):
        self.client = Client()
        user = get_user_model().objects.create(email='a.b@c.de')
        self.profile = Profile.objects.create(user=user)
        DonationLevel.objects.create(amount=75, title='Level 1')

    def test_urls(self):
        response = self.client.get(reverse('donations:payment'), {'amount': '80'})
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        session['updated'] = self.profile.pk
        session.save()
        response = self.client.get(reverse('donations:payment'))
        self.assertEqual(response.status_code, 200)


class DonationTest(TestCase):
    def setUp(self):
        self.client = Client()
        user = get_user_model().objects.create(email='a.b@c.de')
        self.profile = Profile.objects.create(user=user)
        DonationLevel.objects.create(amount=75, title='Level 1')
        DonationLevel.objects.create(amount=150, title='Level 2')
        DonationLevel.objects.create(amount=300, title='Level 3')

    def test_level(self):
        self.assertEqual(DonationLevel.get_level_by_amount(80).amount, 75)
        self.assertEqual(DonationLevel.get_lowest_amount(), 75)

    def test_donation(self):
        donation_amount = 200
        self.profile.donate(donation_amount)
        self.assertEqual(self.profile.balance, donation_amount)
        self.assertEqual(self.profile.donation.level.amount, 150)
        self.assertEqual(self.profile.level.amount, 150)
        self.assertEqual(self.profile.expiration, date.today() + timedelta(days=settings.DONATION_PERIOD))
