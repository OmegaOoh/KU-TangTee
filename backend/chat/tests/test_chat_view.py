"""Test module for chat view."""
import time

from activities.models import Activity, Attend
from activities.tests.constants import SCHOOL_IMAGE
from chat.models import Attachment, Message
from chat.tests.shortcuts import image_loader
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class ChatMessageListTest(APITestCase):
    """Test case for the ChatMessageList view."""

    def setUp(self):
        """Create user, login user, create activity and create message."""
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.activity = Activity.objects.create(owner=self.user, name="Test Activity")
        Attend.objects.create(user=self.user, activity=self.activity)
        self.client.login(username="testuser", password="testpass")
        self.message1 = Message.objects.create(
            activity=self.activity,
            sender=self.user,
            message="Hello, this is a test message."
        )
        time.sleep(0.1)
        self.message2 = Message.objects.create(
            activity=self.activity,
            sender=self.user,
            message="This is another test message."
        )
        self.url = reverse('chat_message_list', args=[self.activity.id])

    def test_get_chat_messages(self):
        """Test the retrieval of chat messages for an activity."""
        response = self.client.get(self.url)

        # Check that the response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the response data matches the messages created
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['message'], self.message2.message)
        self.assertEqual(response.data['results'][1]['message'], self.message1.message)

    def test_get_chat_messages_empty(self):
        """Test retrieval when there are no messages for the activity."""
        # Delete messages to test empty response
        Message.objects.all().delete()
        response = self.client.get(self.url)

        # Check that the response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the response data is empty
        self.assertEqual(response.data['results'], [])

    def test_get_image_from_message(self):
        """Test getting image that comes along with message."""
        message3 = Message.objects.create(
            activity=self.activity,
            sender=self.user,
            message="Message comes up with image."
        )
        img_url = [SCHOOL_IMAGE]
        image_loader(img_url, message3)
        chat_img = Attachment.objects.filter(message=message3).first()
        chat_img_url = chat_img.image.url
        response = self.client.get(self.url)

        # Check that the response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][2]['message'], self.message1.message)
        self.assertEqual(response.data['results'][1]['message'], self.message2.message)
        self.assertEqual(response.data['results'][0]['message'], message3.message)
        self.assertEqual(response.data['results'][0]['images'][0], chat_img_url)
        chat_img.image.delete(save=False)
        chat_img.delete()
