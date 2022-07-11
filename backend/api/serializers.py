from typing import Optional

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from food import models

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'password',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj: User) -> bool:
        # subscription = models.Subscription.objects.filter(
        #     user=self.context.get('request').user,
        #     subscribed_to=obj
        # )
        # return subscription.count() != 0
        # TODO
        return False

    def get_recipes(self,
                    obj: User,
                    limit: Optional[int] = None
                    ) -> 'RecipeShortSerializer':
        if limit is not None and limit < 1:
            raise ValidationError()

        recipes = models.Recipe.objects.filter(author=obj)[:limit]
        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj: User) -> int:
        return models.Recipe.objects.filter(author=obj).count()


class UserCreateSerializer(UserSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        exclude_fields = ['is_subscribed', 'recipes', 'recipes_count']
        for exclude_name in exclude_fields:
            self.fields.pop(exclude_name)


class UserProfileSerializer(UserSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        exclude_fields = ['recipes', 'recipes_count']
        for exclude_name in exclude_fields:
            self.fields.pop(exclude_name)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserProfileSerializer()
    ingredients = IngredientSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = models.Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tag_ids = validated_data.pop('tags')

        recipe = models.Recipe.objects.create(**validated_data)

        for ingredient in ingredients:
            obj = get_object_or_404(models.Ingredient, pk=ingredient.get('id'))
            r_i, _ = models.RecipeIngredient.objects.get_or_create(
                recipe=recipe,
                ingredient=obj,
                amount=ingredient.get('amount')
            )

        for tag_id in tag_ids:
            obj = get_object_or_404(models.Tag, pk=tag_id)
            r_t, _ = models.RecipeTag.objects.get_or_create(
                recipe=recipe,
                tag=obj,
            )

    def get_is_favorited(self, obj: models.Recipe) -> bool:
        # TODO
        return False

    def get_is_in_shopping_cart(self, obj: models.Recipe) -> bool:
        # TODO
        return False


class RecipeShortSerializer(RecipeSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        exclude_fields = [
            'author',
            'tags',
            'ingredients',
            'text',
            'is_favorited',
            'is_in_shopping_cart',
        ]
        for exclude_name in exclude_fields:
            self.fields.pop(exclude_name)
