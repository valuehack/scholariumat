from django.test import TestCase
from django.contrib.auth import get_user_model

from users.models import Profile


class UserTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(email='a.b@c.de')
        Profile.objects.create(user=self.user)

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
