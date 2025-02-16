"""Module for handle URL /profile."""
from typing import Any

from django.contrib.auth import models as auth_models
from django.db.models import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from profiles import models
from profiles.logger import Action, RequestData, data_to_log, logger
from profiles.serializer import model_serializers
from profiles.serializer.permissions import OnlyOwnerCanEdit
from rest_framework import generics, mixins, permissions, response, status


class ProfileDetail(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    generics.GenericAPIView
):
    """Return detail of the profile when GET request and edit profile when PUT request."""

    serializer_class = model_serializers.ProfilesSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, OnlyOwnerCanEdit]
    lookup_field = 'username'

    def get_queryset(self) -> QuerySet:
        """Profile view returns a user's profile."""
        return models.Profile.objects.all()

    def get_object(self) -> Any:
        """
        Get profile objects base on lookup field.

        :return: Data Model for profile
        """
        username = self.kwargs.get("username")
        user = get_object_or_404(auth_models.User, username=username)
        return models.Profile.objects.get(user=user)

    def retrieve(self, request: HttpRequest, *args: Any, **kwargs: Any) -> response.Response:
        """Override retrieve to return only base profile if KU Tangtee not found in the database and return it."""
        username = kwargs.get('username')
        user = get_object_or_404(auth_models.User, username=username)
        try:
            profile = models.Profile.objects.get(user=user)
            serializer = self.get_serializer(profile)
            return response.Response({**serializer.data})
        except models.Profile.DoesNotExist:
            # return only base user detail if not found
            serializer = self.get_serializer(user)
            user_data = {
                'user': {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "profile_picture_url": self.get_profile_picture(user)
            }
            return response.Response(user_data, status=status.HTTP_200_OK)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> response.Response:
        """Handle get request by return detail of a profile.

        :param request: Http request object
        :return: Http response object
        """
        return self.retrieve(request, *args, **kwargs)

    def put(self, request: HttpRequest, *args: Any, **kwargs: Any) -> response.Response:
        """Handle put request by edit a profile.

        :param request: Http request object
        :return: Http response object
        """
        new_kwargs = kwargs.copy()
        username = new_kwargs.pop('username', None)
        user = get_object_or_404(auth_models.User, username=username)

        if user != request.user:
            req_data = RequestData(req_user=request.user, profile_id=-1, target_user=user)
            logger.warning(data_to_log(Action.TRY_EDIT, req_data))
            return response.Response({'message': 'Cannot edit other profile.'}, status=403)

        new_kwargs["user_id"] = user.id
        res = self.update(request, partial=True, *args, **new_kwargs)
        res_dict = res.data

        req_data = RequestData(req_user=request.user, profile_id=res_dict.get("id"))
        logger.info(data_to_log(Action.EDIT, req_data))
        return response.Response(
            {
                "message": "You have successfully edited your KU Tangtee profile.",
                "id": res_dict.get("id"),
            }
        )
