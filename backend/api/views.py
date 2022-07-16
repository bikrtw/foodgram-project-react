from typing import Optional

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from food import models
from . import serializers

User = get_user_model()


def response_400(s: str) -> Response:
    return Response(
        data={'errors': s},
        status=status.HTTP_400_BAD_REQUEST,
    )


class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['subscriptions']:
            return serializers.UserSerializer
        return serializers.UserProfileSerializer

    @action(detail=False, name='Subscriptions')
    def subscriptions(self, request: HttpRequest) -> Response:
        users = User.objects.filter(
            subscriptions__subscribed_to=request.user)

        page = self.paginate_queryset(users)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], name='Subscribe')
    def subscribe(self, request: HttpRequest, pk: Optional[int] = None
                  ) -> Response:

        to_user = get_object_or_404(User, pk=pk)
        if to_user == request.user:
            return response_400('Choose different user!')

        if request.method == 'POST':
            subscription, created = models.Subscription.objects.get_or_create(
                user=request.user,
                subscribed_to=to_user,
            )
            if not created:
                return response_400('Already subscribed!')

            serializer = self.get_serializer(
                to_user,
                context={'request': self.request}
            )
            return Response(serializer.data)

        subscription = models.Subscription.objects.filter(
            user=request.user,
            subscribed_to=to_user,
        )

        if subscription.count() == 0:
            return response_400('Not subscribed!')

        subscription[0].delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(mixins.RetrieveModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    serializer_class = serializers.TagSerializer
    queryset = models.Tag.objects.all()
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = models.Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['shopping_cart', 'favorite']:
            return serializers.RecipeShortSerializer
        return serializers.RecipeSerializer

    def update(self, request, *args, **kwargs):
        # disable partial update
        kwargs['partial'] = False
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], name='Download shopping cart')
    def download_shopping_cart(self, request: HttpRequest) -> Response:
        return Response(data={'action': 'download_shopping_cart'})

    @action(detail=True, methods=['post', 'delete'], name='Shopping cart')
    def shopping_cart(self, request: HttpRequest, pk: Optional[int] = None
                      ) -> Response:
        recipe = get_object_or_404(models.Recipe, pk=pk)
        if request.method == 'POST':
            shopping_cart, created = models.ShoppingCart.objects.get_or_create(
                user=request.user,
                recipe=recipe,
            )
            if not created:
                return response_400('Recipe already in shopping cart!')

            serializer = self.get_serializer(
                recipe,
                context={'request': self.request}
            )
            return Response(serializer.data)

        shopping_cart = models.ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe,
        )

        if shopping_cart.count() == 0:
            return response_400('No such recipe in shopping cart!')

        shopping_cart[0].delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], name='Favorite')
    def favorite(self, request: HttpRequest, pk: Optional[int] = None
                 ) -> Response:
        recipe = get_object_or_404(models.Recipe, pk=pk)
        if request.method == 'POST':
            favorite, created = models.FavoriteRecipe.objects.get_or_create(
                user=request.user,
                recipe=recipe,
            )
            if not created:
                return response_400('Recipe already in favorites!')

            serializer = self.get_serializer(
                recipe,
                context={'request': self.request}
            )
            return Response(serializer.data)

        shopping_cart = models.FavoriteRecipe.objects.filter(
            user=request.user,
            recipe=recipe,
        )

        if shopping_cart.count() == 0:
            return response_400('No such recipe in favorites!')

        shopping_cart[0].delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = serializers.IngredientSerializer
    queryset = models.Ingredient.objects.all()
    pagination_class = None
