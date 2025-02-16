"""Test module for check-in behaviour."""
import django.test
from django import urls
from django.utils import timezone
from profiles.models import Profile

from ..models import Attend
from .shortcuts import client_join_activity, create_activity, create_test_user


class CheckinTest(django.test.TestCase):
    """Test check-in behaviors."""

    def setUp(self):
        """Set up the common URL and common value."""
        self.url = lambda id: urls.reverse("activities:checkin", args=[id])

        self.host = create_test_user('Host')
        DAYSDELTA = 7
        data = {'name': 'test activity', 'detail': 'hello', 'date': (timezone.now()).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                'end_date': (timezone.now() + timezone.timedelta(days=DAYSDELTA)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}
        _, self.activity = create_activity(host=self.host, client=self.client, data=data)

        self.attendee = create_test_user('Attendee')
        client_join_activity(client=self.client, user=self.attendee, activity=self.activity)
        self.client.logout()

    def test_only_host_can_open(self):
        """Only host can open a check-in."""
        self.client.force_login(self.attendee)
        res = self.client.put(self.url(self.activity.id) + '?status=open')
        self.assertJSONEqual(res.content, {'message': 'User must be the host to perform this action.'})

    def test_host_can_open_check_in(self):
        """Host should able to open for participant to check-in."""
        self.client.force_login(self.host)
        res = self.client.put(self.url(self.activity.id) + '?status=open')

        self.assertJSONEqual(res.content, {
            'message': 'Activity check-in are open',
            "check_in_allowed": True
        })

        self.activity.refresh_from_db()
        self.assertTrue(self.activity.check_in_allowed)
        self.assertRegex(self.activity.check_in_code, r'^[A-Z]{6}$')

        code_res = self.client.get(self.url(self.activity.id))
        self.assertEqual(self.activity.check_in_code, code_res.data['check_in_code'])
        self.assertTrue(self.activity.check_in_allowed)

    def test_host_can_close_check_in(self):
        """Host shoud able to close for participant to check-in."""
        self.client.force_login(self.host)
        res = self.client.put(self.url(self.activity.id) + '?status=close')
        self.assertJSONEqual(res.content, {
            'message': 'Activity check-in are close',
            "check_in_allowed": False
        })

        self.activity.refresh_from_db()

        self.assertFalse(self.activity.check_in_allowed)
        self.assertIsNone(self.activity.check_in_code)

    def test_invalid_status(self):
        """Nothing should change is query param is invalid."""
        self.client.force_login(self.host)
        res = self.client.put(self.url(self.activity.id) + '?status=yes')
        self.assertJSONEqual(res.content, {'message': 'No status provided.'})
        self.activity.refresh_from_db()
        self.assertFalse(self.activity.check_in_allowed)

    def test_no_status(self):
        """Nothing should change if query param status are not provided."""
        self.client.force_login(self.host)
        res = self.client.put(self.url(self.activity.id))
        self.assertJSONEqual(res.content, {'message': 'No status provided.'})
        self.activity.refresh_from_db()
        self.assertFalse(self.activity.check_in_allowed)

    def test_host_open_and_close(self):
        """Host should able to open and close for participant to check-in."""
        self.client.force_login(self.host)

        self.client.force_login(self.host)
        res = self.client.put(self.url(self.activity.id) + '?status=open')

        self.assertJSONEqual(res.content, {
            'message': 'Activity check-in are open',
            "check_in_allowed": True
        })

        self.activity.refresh_from_db()

        self.assertRegex(self.activity.check_in_code, r'^[A-Z]{6}$')
        self.assertTrue(self.activity.check_in_allowed)

        code_res = self.client.get(self.url(self.activity.id))
        self.assertJSONEqual(
            code_res.content,
            {
                'check_in_code': self.activity.check_in_code,
                'check_in_allowed': True
            }
        )

        res = self.client.put(self.url(self.activity.id) + '?status=close')
        self.assertJSONEqual(res.content, {
            'message': 'Activity check-in are close',
            'check_in_allowed': True
        })
        self.activity.refresh_from_db()
        self.assertFalse(self.activity.check_in_allowed)

        code_res = self.client.get(self.url(self.activity.id))
        self.assertJSONEqual(
            code_res.content,
            {
                'message': 'Check-in are not allow at the moment'
            }
        )

    def test_logout_check_in(self):
        """Unauthenticated user should able to check-in."""
        res = self.client.post(self.url(self.activity.id))
        self.assertJSONEqual(res.content, {'message': 'Authentication credentials were not provided.'})

    def test_not_a_member_check_in(self):
        """User that are not the participant of activity should not able to check-in."""
        self.open()
        new_user = create_test_user('Not a member')
        self.client.force_login(new_user)
        res = self.client.post(
            self.url(self.activity.id),
            data={
                'check_in_code': self.activity.check_in_code
            }
        )
        self.assertJSONEqual(res.content, {'message': "You must be member of this activity before perform this action."})

        status_res = self.client.get(urls.reverse("activities:is-joined", args=[self.activity.id]))
        self.assertJSONEqual(status_res.content, {'is_joined': False, 'is_checked_in': False})

    def test_check_in_close(self):
        """User should unavailable to check-in when host is close the check-in."""
        self.open()
        self.close()
        self.client.force_login(self.attendee)
        res = self.client.post(
            self.url(self.activity.id),
            data={
                'check_in_code': self.activity.check_in_code
            }
        )
        self.assertJSONEqual(res.content, {'message': 'Check-in are not allow at the moment'})
        self.assertFalse(self.attendee.attend_set.get(activity=self.activity).checked_in)

        status_res = self.client.get(urls.reverse("activities:is-joined", args=[self.activity.id]))
        self.assertJSONEqual(status_res.content, {'is_joined': True, 'is_checked_in': False})

    def test_wrong_check_in_code(self):
        """User should not check-in if check-in code are not match."""
        self.open()

        self.client.force_login(self.attendee)
        res = self.client.post(
            self.url(self.activity.id),
            data={
                'check_in_code': 'wrongs'
            }
        )
        self.assertJSONEqual(res.content, {'message': 'Check-in code invalid'})
        self.assertFalse(self.attendee.attend_set.get(activity=self.activity).checked_in)

        status_res = self.client.get(urls.reverse("activities:is-joined", args=[self.activity.id]))
        self.assertJSONEqual(status_res.content, {'is_joined': True, 'is_checked_in': False})

    def test_complete_check_in(self):
        """Test success check-in."""
        self.open()

        self.client.force_login(self.attendee)

        user_profile = self.attendee.profile_set.first()
        rep_before = user_profile.reputation_score

        host_profile = self.attendee.profile_set.first()
        host_rep = host_profile.reputation_score

        res = self.client.post(
            self.url(self.activity.id),
            data={
                'check_in_code': self.activity.check_in_code
            }
        )

        user_profile.refresh_from_db()
        self.assertJSONEqual(res.content, {'message': f"You've successfully check-in to {self.activity.name}"})
        self.assertTrue(self.attendee.attend_set.get(activity=self.activity).checked_in)
        self.assertEqual(rep_before + 1, user_profile.reputation_score)
        self.assertEqual(host_rep, host_profile.reputation_score)

        status_res = self.client.get(urls.reverse("activities:is-joined", args=[self.activity.id]))
        self.assertJSONEqual(status_res.content, {'is_joined': True, 'is_checked_in': True})

    def test_decrease_reputation_for_missed_check_in(self):
        """Test that user's reputation decreases when check-in is missing."""
        self.open()
        self.activity.end_date = timezone.now() - timezone.timedelta(days=1)
        self.activity.date = timezone.now() - timezone.timedelta(days=2)
        self.activity.save()

        # Call the method to check for missed check-ins
        Profile.check_missed_check_ins()

        # attendee point deducted because not check-in
        user_profile = self.attendee.profile_set.first()
        self.assertEqual(user_profile.reputation_score,
                         max(0, user_profile.reputation_score - Profile.CHECK_IN_REPUTATION_DECREASE))

        attendee_record = Attend.objects.get(user=self.attendee, activity=self.activity)
        self.assertTrue(attendee_record.rep_decrease)

        # host point deducted because no attendee check-in
        host_profile = self.host.profile_set.first()
        self.assertEqual(host_profile.reputation_score,
                         max(0, host_profile.reputation_score - Profile.CHECK_IN_REPUTATION_DECREASE))

        host_record = Attend.objects.get(user=self.host, activity=self.activity)
        self.assertTrue(host_record.rep_decrease)

    def test_host_get_check_in_code(self):
        """Host should able to get check-in code."""
        self.open()
        self.client.force_login(self.host)

        res = self.client.get(self.url(self.activity.id))
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(res.content, {
            "check_in_code": self.activity.check_in_code,
            "check_in_allowed": True
        })

    def test_host_get_check_in_code_while_close(self):
        """GET check-in code should return NULL when activity are not allow to checked in."""
        self.open()
        self.close()
        self.client.force_login(self.host)

        res = self.client.get(self.url(self.activity.id))
        self.assertEqual(res.status_code, 403)
        self.assertJSONEqual(res.content, {'message': 'Check-in are not allow at the moment'})

    def test_not_host_get_check_in_code(self):
        """Attendee should unable to get and activity check-in code."""
        self.open()
        self.client.force_login(self.attendee)

        res = self.client.get(self.url(self.activity.id))
        self.assertEqual(res.status_code, 403)
        self.assertJSONEqual(res.content, {'message': 'User must be the host to perform this action.'})

    def open(self):
        """Open for check-in."""
        self.client.force_login(self.host)
        self.client.put(self.url(self.activity.id) + '?status=open')
        self.client.logout()
        self.activity.refresh_from_db()

    def close(self):
        """Close check in."""
        self.client.force_login(self.host)
        self.client.put(self.url(self.activity.id) + '?status=close')
        self.client.logout()
        self.activity.refresh_from_db()
