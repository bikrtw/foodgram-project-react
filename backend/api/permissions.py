from rest_framework.permissions import BasePermission


class Forbidden(BasePermission):
    """Permission to disable some basic djoser views."""

    def has_permission(self, request, view):
        return False
