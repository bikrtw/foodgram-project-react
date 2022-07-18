import csv
from typing import Optional

from django.contrib.auth import get_user_model
from django.db.models import Sum, F
from django.http import HttpRequest, HttpResponse
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from food import models
from . import serializers
from .permissions import AuthorOrReadOnly, Forbidden

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


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.TagSerializer
    queryset = models.Tag.objects.all()
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.RecipeSerializer

    def get_queryset(self):
        queryset = models.Recipe.objects.all()

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited is not None:
            if is_favorited == '0':
                queryset = queryset.exclude(
                    favorites__user=self.request.user)
            elif is_favorited == '1':
                queryset = queryset.filter(
                    favorites__user=self.request.user)

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_in_shopping_cart is not None:
            if is_in_shopping_cart == '0':
                queryset = queryset.exclude(
                    shopping_cart__user=self.request.user)
            elif is_in_shopping_cart == '1':
                queryset = queryset.filter(
                    shopping_cart__user=self.request.user)

        author_id = self.request.query_params.get('author')
        if author_id is not None and author_id.isdigit():
            queryset = queryset.filter(author_id=author_id)

        tags = self.request.query_params.getlist('tags', [])
        if tags:
            queryset = queryset.filter(tags__slug__in=tags)

        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['update', 'destroy']:
            return [AuthorOrReadOnly()]
        elif self.action in ['partial_update']:
            return [Forbidden()]

        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ['shopping_cart', 'favorite']:
            return serializers.RecipeShortSerializer
        return serializers.RecipeSerializer

    def update(self, request, *args, **kwargs):
        # disable partial update
        kwargs['partial'] = False
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], name='Download shopping cart')
    def download_shopping_cart(self, request: HttpRequest) -> HttpResponse:
        response = HttpResponse(content_type='text/csv')
        response[
            'Content-Disposition'] = 'attachment; filename="somefilename.csv"'

        shopping_cart = models.Recipe.objects.filter(
            shopping_cart__user=request.user)

        ingredients = models.Ingredient.objects.filter(
            recipes__recipe__in=shopping_cart
        ).annotate(
            quantity=Sum('recipes__amount')
        ).values('name', 'quantity', unit=F('measurement_unit'))
        if ingredients.exists():
            writer = csv.DictWriter(response, fieldnames=ingredients[0].keys())
            writer.writeheader()
            writer.writerows(ingredients)

        return response

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


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.IngredientSerializer
    queryset = models.Ingredient.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)
    pagination_class = None
