"""Module for handle URL /activities/<activity_id>."""
from typing import Any

from activities import models
from activities.logger import Action, RequestData, data_to_log, logger
from activities.serializer import model_serializers
from activities.serializer.permissions import OnlyHostCanEdit
from activities.views.util import (create_location, edit_host_access,
                                   image_deleter, image_loader,
                                   image_loader_64)
from django.db.models import Q
from django.http import HttpRequest
from rest_framework import generics, mixins, permissions, response


class ActivityDetail(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     generics.GenericAPIView):
    """Return detail of an activity when GET request, and edit the activity when PUT request."""

    queryset = models.Activity.objects.all()
    serializer_class = model_serializers.ActivitiesSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, OnlyHostCanEdit]

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> response.Response:
        """Handle get request by return detail of an activity.

        :param request: Http request object
        :return: Http response object
        """
        return self.retrieve(request, *args, **kwargs)

    def put(self, request: HttpRequest, *args: Any, **kwargs: Any) -> response.Response:
        """Handle put request by edit an activity.

        :param request: Http request object
        :return: Http response object
        """
        return self.update(request, *args, **kwargs)

    def update(self, request: HttpRequest, *args: Any, **kwargs: Any) -> response.Response:
        """Update an activity with new information provided.

        :param request: Http request object
        :return: Http response object
        """
        # Checking number of people join
        check_max_error = self.__check_max_people(request)
        if check_max_error:
            return check_max_error

        # Checking owner reputation score
        rep_error = self.__check_rep_score(request)
        if rep_error:
            return rep_error

        # Deal with location.
        loc_id = self.__edit_location(request)
        if loc_id:
            request.data['locations'] = loc_id

        # Update activity information
        res = super().update(request, partial=True, *args, **kwargs)
        res_dict = res.data

        # Deal with attachment.
        self.__add_remove_attachment(request)
        # Kick attendee
        self.__kick_attendee(request)

        # Deal with participants
        err_res = self.__grant_host_remove_host(request)
        if err_res:
            return err_res

        req_data = RequestData(req_user=request.user, act_id=res_dict.get("id"))
        logger.info(data_to_log(Action.EDIT, req_data))
        return response.Response(
            {
                "message": f"You have successfully edited the activity {res_dict.get('name')}",
                "id": res_dict.get("id")
            }
        )

    def __check_rep_score(self, request: HttpRequest) -> response.Response | None:
        """Check reputation score of owner compare to updated value.

        :param request: HttpRequest object
        :return: Http response object if minimum reputation score is not valid.
        """
        activity = self.get_object()
        owner_profile = activity.owner.profile_set.first()
        min_rep = request.data.get("minimum_reputation_score")
        if min_rep:
            if min_rep > owner_profile.reputation_score:
                req_data = RequestData(req_user=request.user, act_id=activity.id)
                logger.warning(data_to_log(Action.FAIL_EDIT, req_data, 'Owner rep < Min rep'))
                return response.Response(
                    {
                        'message': 'Activity Minimum reputation must less then or equal to creator reputation score',
                        "id": activity.id
                    },
                    status=403
                )
        return None

    def __check_max_people(self, request: HttpRequest) -> response.Response | None:
        """Check max people.

        :param request: HttpRequest object
        """
        activity = self.get_object()
        max_people = request.data.get("max_people")
        current_people = activity.people
        if max_people and current_people > max_people:
            req_data = RequestData(req_user=request.user, act_id=activity.id)
            logger.warning(data_to_log(Action.FAIL_EDIT, req_data, 'Current people > Max people'))
            return response.Response(
                {
                    "message": "Number of participants exceed the capacity.",
                    "id": activity.id
                },
            )
        return None

    def __edit_location(self, request: HttpRequest) -> int | None:
        activity = self.get_object()
        coordinate = request.data.get("location", {})

        if coordinate:
            location = activity.locations

            if location:
                location.latitude = coordinate.get("lat")
                location.longitude = coordinate.get("lon")
                location.save()
                location_id = location.id
            else:
                location_id = create_location(coordinate)

            return int(location_id)

        return None

    def __add_remove_attachment(self, request: HttpRequest) -> None:
        """Add or remove images from activity.

        :param request: HttpRequest object
        """
        activity = self.get_object()
        attachment_ids_to_remove = request.data.get("remove_attachments", [])

        if attachment_ids_to_remove:
            image_deleter(attachment_ids_to_remove)

        attachment_to_add = request.data.get("new_images", [])
        if attachment_to_add:
            if any("base64" in attachment for attachment in attachment_to_add):
                image_loader_64(attachment_to_add, activity)
            else:
                image_loader(attachment_to_add, activity)

    def __grant_host_remove_host(self, request: HttpRequest) -> response.Response | None:
        """Grant host and remove host from activity.

        :param request: HttpRequest object
        """
        activity = self.get_object()
        grant_host_user_ids = request.data.get("grant_host", [])
        if grant_host_user_ids:
            res = edit_host_access(grant_host_user_ids, activity, request.user, remove=False)
            if res:
                return res

        remove_host_user_ids = request.data.get("remove_host", [])
        if remove_host_user_ids:
            res = edit_host_access(remove_host_user_ids, activity, request.user, remove=True)
            if res:
                return res

        return None

    def __kick_attendee(self, request: HttpRequest) -> None:
        """Handle kick attendee from activity.

        :param request: HttpRequest object
        """
        activity = self.get_object()

        attendee_ids_to_remove = request.data.get("attendee_to_remove", [])
        attendee_to_remove = activity.attend_set.filter(user__id__in=attendee_ids_to_remove, is_host=False)
        attendee_infos_to_remove = [a.user for a in attendee_to_remove]

        print(attendee_ids_to_remove)
        attendee_to_remove.delete()

        for attendee in attendee_infos_to_remove:
            req_data = RequestData(req_user=request.user, act_id=activity.id, target_user=attendee)
            logger.info(data_to_log(Action.KICK, req_data))
