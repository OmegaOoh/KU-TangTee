"""Module for handle URL /activities/<activity_id>."""
from activities.views.util import image_loader
from typing import Any
from django.http import HttpRequest
from django.utils import timezone
from rest_framework import generics, permissions, mixins, response, status
from activities import models
from activities.serializer.permissions import IsHostOrReadOnly
from activities.serializer import model_serializers


class ActivityDetail(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     generics.GenericAPIView):
    """Return detail of an activity when GET request, and edit the activity when PUT request."""

    queryset = models.Activity.objects.filter(date__gte=timezone.now())
    serializer_class = model_serializers.ActivitiesSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsHostOrReadOnly]

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
        activity = self.get_object()
        max_people = request.data.get("max_people")
        current_people = activity.people
        if max_people and current_people > max_people:
            return response.Response(
                {"message": "Number of participants exceed the capacity.",
                 "id": activity.id
                 },
            )
        res = self.update(request, *args, **kwargs)
        res_dict = res.data
        attachment_ids_to_remove = res_dict.get("remove_attachments", [])

        if attachment_ids_to_remove:
            for attachment_id in attachment_ids_to_remove:
                attachment = activity.attachments.filter(id=attachment_id).first()
                if attachment:
                    attachment.image.delete(save=False)
                    attachment.delete()

        attachment_to_add = res_dict.get("new_images", [])

        image_loader(attachment_to_add, activity)

        return response.Response(
            {
                "message": f"You have successfully edited the activity {res_dict.get('name')}",
                "id": res_dict.get("id")
            }
        )
