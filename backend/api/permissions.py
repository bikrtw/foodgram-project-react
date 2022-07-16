from rest_framework import permissions


class Forbidden(permissions.BasePermission):
    """Permission to disable some basic djoser and other views."""

    def has_permission(self, request, view):
        return False


class AuthorOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)
