from typing import Optional

from django.contrib.auth import get_user_model
from django.http import HttpRequest, Http404
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

    def create(self, request, *args, **kwargs):
        data = request.data
        ingredients = data.pop('ingredients', [])
        tag_ids = data.pop('tags', [])
        # TODO
        _ = data.pop('image', None)

        serializer = self.get_serializer_class()(data=data)
        if serializer.is_valid() and tag_ids and ingredients:
            recipe = serializer.save(author=request.user)
            for tag_id in tag_ids:
                tag = models.Tag.objects.filter(pk=tag_id)
                if tag.count() == 0:
                    recipe.delete()
                    raise Http404(f'tag not found: {tag_id}')
                models.RecipeTag.objects.create(recipe=recipe, tag=tag[0])
            for ingredient in ingredients:
                pk = ingredient.get('id')
                amount = ingredient.get('amount')
                obj = models.Ingredient.objects.filter(pk=pk)
                if obj.count() == 0:
                    recipe.delete()
                    raise Http404(f'ingredient not found: {pk}')
                models.RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=obj[0],
                    amount=amount,
                )

            return Response(
                data=serializer.data, status=status.HTTP_201_CREATED)

        data = serializer.errors
        if not tag_ids:
            data['tags'] = ["This field is required."]
        if not ingredients:
            data['ingredients'] = ["This field is required."]
        return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

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
