from typing import Optional

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import serializers
from food import models

User = get_user_model()


def response_400(s: str) -> Response:
    return Response(
        data={'errors': s},
        status=status.HTTP_400_BAD_REQUEST,
    )


class UserViewSet(viewsets.ViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=False, name='Subscriptions')
    def subscriptions(self, request: HttpRequest) -> Response:
        users = User.objects.filter(
            subscriptions__subscribed_to=request.user)
        serializer = serializers.UserSerializer(
            users,
            context={'request': self.request},
            many=True
        )
        return Response(data=serializer.data)

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

            serializer = serializers.UserProfileSerializer(
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


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = models.Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer

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

            serializer = serializers.RecipeShortSerializer(
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
        if request.method == 'POST':
            return Response(data={'action': 'shopping_cart_add', 'pk': pk})

        return Response(data={'action': 'shopping_cart_delete', 'pk': pk})


class IngredientViewSet(mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = serializers.IngredientSerializer
    queryset = models.Ingredient.objects.all()
