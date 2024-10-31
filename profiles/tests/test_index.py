"""Module to test on profile index page."""
import json
import django.test
from django import urls
from .shortcuts import create_profile, create_test_user
from profiles.serializer.model_serializers import ProfilesSerializer


class IndexTest(django.test.TestCase):
    """Test Cases for Profile Index View."""

    def setUp(self):
        self.has_profile = [{'has_profile': True}]
        self.not_have_profile = [{'has_profile': False}]

    def test_index_does_not_have_profile(self):
        """Show only has_profile status."""
        user1 = create_test_user("Bruce")
        user2 = create_test_user("Clark")
        _, profile = create_profile(user=user1)
        self.client.force_login(user2)

        response = self.client.get(urls.reverse("profiles:index"))
        self.assertEqual(response.status_code, 200)

        self.assertJSONEqual(response.content, self.not_have_profile)

    def test_index_has_profile(self):
        """Show profile information and has_profile status."""
        user = create_test_user("Alexa")
        self.client.force_login(user)

        _, profile = create_profile(user=user)

        response = self.client.get(urls.reverse("profiles:index"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, [ProfilesSerializer(profile).data] + self.has_profile)
