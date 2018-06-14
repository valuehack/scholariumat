from django.test import TestCase
from django.contrib.auth import get_user_model


class UserTest(TestCase):
    def setUp(self):
        get_user_model().objects.create(email='a.b@c.de', name='merlin')

    def test_user(self):
        user = get_user_model().objects.get(email='a.b@c.de')
        self.assertEqual(user.profile.balance, 0)
