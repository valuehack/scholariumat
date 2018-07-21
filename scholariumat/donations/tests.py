from datetime import date, timedelta

from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from users.models import Profile
from donations.models import DonationLevel, Donation, PaymentMethod


class RequestDonationTest(TestCase):
    def setUp(self):
        self.client = Client()
        DonationLevel.objects.create(amount=75, title='Level 1')
        PaymentMethod.objects.create(title='Bar')

    def test_donation(self):
        response = self.client.get(reverse('donations:payment'))
        self.assertEqual(response.status_code, 302)
        post_data = {
            'email': 'a.b@c.de',
            'title': 'm',
            'name': '',
            'organization': '',
            'street': '',
            'postcode': '',
            'country': ''}
        response = self.client.post(response.url, post_data, follow=True)
        self.assertRedirects(response, reverse('donations:payment'))
        profile = Profile.objects.get(user__email='a.b@c.de')
        self.assertTrue(profile)

        post_data = {
            'level': 7,
            'payment_method': 1
        }
        response = self.client.post(reverse('donations:payment'), post_data)

        self.assertEqual(response.status_code, 302)

        donation = Donation.objects.get(profile=profile)
        response = self.client.post(reverse('donations:approve', kwargs={'slug': donation.slug}), {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.level.amount, 75)
        self.assertTrue(Donation.objects.get(profile=profile).executed)


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
