"""Test for activity model of activities app."""
import django.test
from .shortcuts import create_activity, create_test_user


class TestActivityModel(django.test.TestCase):
    """TestCase Class for Activity model."""

    def test_can_join_equal_max(self):
        """can_join() return False as Number of people is equal to max_people."""
        data = {
            "name": "Exceed",
            "detail": "",
            "max_people": 1
        }
        response, activity = create_activity(data=data)
        self.assertFalse(activity.can_join())

    def test_can_join_less(self):
        """can_join() return True as Number of people is less than max_people."""
        data = {
            "name": "Less",
            "detail": "",
            "max_people": 10
        }
        response, activity = create_activity(data=data)
        self.assertTrue(activity.can_join())

    def test_can_join_past(self):
        """can_join return False when date is in the past."""
        response, activity = create_activity(days_delta=-1)
        self.assertFalse(activity.can_join())

    def test_can_join_future(self):
        """can_join return True when date is in the future."""
        response, activity = create_activity(days_delta=1)
        self.assertTrue(activity.can_join())

    def test_upcoming(self):
        """Return True when activities take place in upcoming weeks."""
        response, up_activity = create_activity(days_delta=7)
        self.assertTrue(up_activity.is_upcoming())

    def test_not_upcoming(self):
        """Return False when activities don't take place in upcoming weeks."""
        response, not_up_activity = create_activity(days_delta=8)
        self.assertFalse(not_up_activity.is_upcoming())

    def test_is_host(self):
        """Return user that is host of that activity."""
        host = create_test_user("My lovely host")
        response, activity = create_activity(host=host)
        self.assertEqual(activity.host(), host)
