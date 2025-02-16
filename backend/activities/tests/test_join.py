"""Test for Join function."""
import django.test
from django import urls

from .shortcuts import client_join_activity, create_activity, create_test_user


class JoinTest(django.test.TestCase):
    """Test Cases for join function."""

    def setUp(self):
        """Set up the common URL."""
        self.host = create_test_user("Host", rep_score=50)
        self.url = lambda id: urls.reverse("activities:join", args=[id])

    def test_logout_join(self):
        """Join should respond with error if user are not authenticated."""
        _, new_act = create_activity(host=self.host)
        self.client.logout()

        response = self.client.post(self.url(new_act.id))
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(response.content, {'message': 'Authentication credentials were not provided.'})

    def test_join_without_profile(self):
        """User without profile will unable to join an activity."""
        _, new_act = create_activity(host=self.host)
        self.client.logout()

        attendee = create_test_user("attendee", with_profile=False)
        self.client.force_login(attendee)

        response = self.client.post(self.url(new_act.id))
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(response.content, {'message': 'User must have profile page before joining an activity'})

    def test_join(self):
        """Join will increase number of people in activity."""
        _, new_act = create_activity(host=self.host)

        attender = create_test_user("Attend")
        self.client.force_login(attender)

        self.assertEqual(new_act.people, 1)

        response = self.client.post(self.url(new_act.id))
        self.assertEqual(response.status_code, 201)
        new_act.refresh_from_db()
        self.assertEqual(new_act.people, 2)
        self.assertIn(attender, new_act.participants())

        self.assertJSONEqual(response.content, {'message': f'You have successfully joined the activity {new_act.name}'})

    def test_join_not_exist_actitvity(self):
        """User should unable to join activity that not exist."""
        attender = create_test_user("Attend")
        self.client.force_login(attender)

        not_exist_pk = 9999

        response = self.client.post(self.url(not_exist_pk))
        self.assertJSONEqual(response.content, {'message': f'Invalid pk "{not_exist_pk}" - object does not exist.'})

    def test_join_full(self):
        """Join will not increase number of people in activity as activities is full."""
        data = {
            "name": "Unjoinable",
            "detail": "This act is unjoinable",
            "max_people": 1
        }
        response, new_act = create_activity(host=self.host, data=data)
        self.assertEqual(response.status_code, 200)

        attender = create_test_user("Attend")
        self.client.force_login(attender)

        response = self.client.post(self.url(new_act.id))
        self.assertEqual(response.status_code, 403)
        new_act.refresh_from_db()
        self.assertEqual(new_act.people, 1)
        self.assertNotIn(attender, new_act.participants())

        self.assertJSONEqual(response.content, {'message': 'The activity Unjoinable is full.'})

    def test_rejoin_joined_activity(self):
        """Cannot join activity that already joined."""
        _, new_act = create_activity(host=self.host)

        attender = create_test_user("Attend")
        self.client.force_login(attender)

        # First time joined, number of people increase.
        response = self.client.post(self.url(new_act.id))
        new_act.refresh_from_db()
        self.assertEqual(new_act.people, 2)
        self.assertIn(attender, new_act.participants())

        # Second time joined, get error and number of people stays the same.
        response = self.client.post(self.url(new_act.id))
        self.assertEqual(response.status_code, 403)
        new_act.refresh_from_db()
        self.assertEqual(new_act.people, 2)
        self.assertIn(attender, new_act.participants())

        self.assertJSONEqual(response.content, {'message': f"You've already joined the activity {new_act.name}."})

    def test_logout_leave(self):
        """Join should respond with error if user are not authenticated."""
        _, new_act = create_activity(host=self.host)

        self.client.logout()
        response = self.client.delete(self.url(new_act.id))
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(response.content, {'message': 'Authentication credentials were not provided.'})

    def test_leave_activity(self):
        """User should able to leave activity that they've join."""
        _, new_act = create_activity(host=self.host)

        attender = create_test_user("Attend")
        self.client.force_login(attender)

        _ = self.client.post(self.url(new_act.id))
        new_act.refresh_from_db()
        self.assertEqual(new_act.people, 2)

        response = self.client.delete(self.url(new_act.id))
        new_act.refresh_from_db()
        self.assertEqual(new_act.people, 1)

        self.assertNotIn(attender, new_act.participants())

        self.assertJSONEqual(response.content, {'message': f"You've successfully leave {new_act.name}"})
        # self.assertJSONEqual(response.content, {'message': f"You've already joined the activity {new_act.name}."})

    def test_leave_not_exist_activity(self):
        """User should unable to leave activity that doesn't exist."""
        attender = create_test_user("Attend")
        self.client.force_login(attender)

        response = self.client.delete(self.url(9999))

        self.assertJSONEqual(response.content, {'message': "You've never join this activity"})

    def test_leave_activity_that_they_havent_join(self):
        """User should not leave activity that the haven't join."""
        _, new_act = create_activity(host=self.host)

        attendee = create_test_user("Attend")
        self.client.force_login(attendee)

        response = self.client.delete(self.url(new_act.id))

        self.assertJSONEqual(response.content, {'message': "You've never join this activity"})

    def test_join_limit_exceed(self):
        """User shouldn't able to join activity if their limit is met."""
        _, new_act1 = create_activity(host=self.host)
        _, new_act2 = create_activity(host=self.host)
        _, new_act3 = create_activity(host=self.host)
        _, new_act4 = create_activity(host=self.host)

        attendee = create_test_user("Attend")
        self.client.force_login(attendee)

        for act in [new_act1, new_act2, new_act3]:
            self.client.post(self.url(act.id))

        res = self.client.post(self.url(new_act4.id))

        self.assertEqual(res.status_code, 403)
        self.assertJSONEqual(res.content, {"message": "The number of activities you have joined has reached the limit"})

    def test_user_with_rep_score_more_then_activity_min(self):
        """User with reputation score more then activity minimum score will able to join that activity."""
        _, act_with_min_rep = create_activity(
            host=self.host,
            data={"name": "test_activity", "detail": "hello", "minimum_reputation_score": 40}
        )
        enough_rep_user = create_test_user("enough rep", rep_score=45)

        self.client.force_login(enough_rep_user)
        response = self.client.post(self.url(act_with_min_rep.id))

        self.assertEqual(response.status_code, 201)
        act_with_min_rep.refresh_from_db()
        self.assertEqual(act_with_min_rep.people, 2)
        self.assertIn(enough_rep_user, act_with_min_rep.participants())

        self.assertJSONEqual(
            response.content, {'message': f'You have successfully joined the activity {act_with_min_rep.name}'}
        )

    def test_user_with_rep_score_equal_to_activity_min(self):
        """User with reputation score more then activity minimum score will able to join that activity."""
        _, act_with_min_rep = create_activity(
            host=self.host,
            data={"name": "test_activity", "detail": "hello", "minimum_reputation_score": 40}
        )
        enough_rep_user = create_test_user("enough rep", rep_score=40)

        self.client.force_login(enough_rep_user)
        response = self.client.post(self.url(act_with_min_rep.id))

        self.assertEqual(response.status_code, 201)
        act_with_min_rep.refresh_from_db()
        self.assertEqual(act_with_min_rep.people, 2)
        self.assertIn(enough_rep_user, act_with_min_rep.participants())

        self.assertJSONEqual(
            response.content, {'message': f'You have successfully joined the activity {act_with_min_rep.name}'}
        )

    def test_user_with_rep_score_less_then_activity_min(self):
        """User with reputation score more then activity minimum score will able to join that activity."""
        _, act_with_min_rep = create_activity(
            host=self.host,
            data={"name": "test_activity", "detail": "hello", "minimum_reputation_score": 40}
        )
        enough_rep_user = create_test_user("enough rep", rep_score=20)

        self.client.force_login(enough_rep_user)
        response = self.client.post(self.url(act_with_min_rep.id))

        self.assertEqual(response.status_code, 403)
        act_with_min_rep.refresh_from_db()
        self.assertEqual(act_with_min_rep.people, 1)
        self.assertNotIn(enough_rep_user, act_with_min_rep.participants())

        self.assertJSONEqual(
            response.content, {'message': f'Your reputation score is too low to join {act_with_min_rep.name}'}
        )

    def test_is_join_api(self):
        """Is join API should correctly return user activity join status correctly."""
        _, act = create_activity(host=self.host)

        # Check unauthenticated user
        self.client.logout()
        res = self.client.get(f'/activities/{act.id}/is-joined/')
        self.assertJSONEqual(res.content, {'is_joined': False, 'is_checked_in': False})

        # Check authenticated user that not join yet
        attendee = create_test_user('join user')
        self.client.force_login(attendee)
        res = self.client.get(f'/activities/{act.id}/is-joined/')
        self.assertJSONEqual(res.content, {'is_joined': False, 'is_checked_in': False})

        # Check user that already join
        client_join_activity(client=self.client, user=attendee, activity=act)
        res = self.client.get(f'/activities/{act.id}/is-joined/')
        self.assertJSONEqual(res.content, {'is_joined': True, 'is_checked_in': False})
