import base64
from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
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

    def _exclude_fields(self, exclude):
        for exclude_name in exclude:
            self.fields.pop(exclude_name)

    def get_is_subscribed(self, obj: User) -> bool:
        user = self.context.get('request').user
        if isinstance(user, AnonymousUser):
            return False

        subscription = models.Subscription.objects.filter(
            user=user,
            subscribed_to=obj
        )
        return subscription.count() != 0

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
        self._exclude_fields(['is_subscribed', 'recipes', 'recipes_count'])


class UserProfileSerializer(UserSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._exclude_fields(['recipes', 'recipes_count'])


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.pk')
    name = serializers.StringRelatedField(source='ingredient.name')
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit')

    class Meta:
        model = models.RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class TagsField(serializers.Field):
    def to_representation(self, value):
        serializer = TagSerializer(value, many=True)
        return serializer.data

    def to_internal_value(self, data):
        return data


class IngredientsField(serializers.Field):
    def to_representation(self, value):
        serializer = RecipeIngredientSerializer(value, many=True)
        return serializer.data

    def to_internal_value(self, data):
        return data


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            # base64 encoded image - decode
            format_str, img_data = data.split(';base64,')
            ext = format_str.split('/')[-1]  # guess file extension
            data = ContentFile(
                base64.b64decode(img_data),
                name='img.' + ext
            )
        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagsField()
    author = UserProfileSerializer(required=False)
    ingredients = IngredientsField()
    image = Base64ImageField()
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

    def validate_tags(self, value):
        if len(value) == 0:
            raise ValidationError('Tag list cannot be empty')
        for pk in value:
            tags = models.Tag.objects.filter(pk=pk)
            if tags.count() == 0:
                raise ValidationError(f'Tag with id {pk} does not exist')
        return value

    def validate_ingredients(self, value):
        if len(value) == 0:
            raise ValidationError('Ingredient list cannot be empty')
        for elem in value:
            pk = elem.get('id', None)
            if pk is None:
                raise ValidationError('Ingredient id error')
            amount = elem.get('amount', None)
            if amount is None:
                raise ValidationError('Amount error')
            ingredients = models.Ingredient.objects.filter(pk=pk)
            if ingredients.count() == 0:
                raise ValidationError(
                    f'Ingredient with id {pk} does not exist')
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tag_ids = validated_data.pop('tags')

        recipe = models.Recipe.objects.create(
            author=self.context['request'].user, **validated_data)

        self.add_tags(recipe, tag_ids)
        self.add_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tag_ids = validated_data.pop('tags')

        for attr in ['name', 'image', 'text', 'cooking_time']:
            val = validated_data.get(attr)
            setattr(instance, attr, val)

        models.RecipeTag.objects.filter(recipe=instance).delete()
        self.add_tags(instance, tag_ids)

        models.RecipeIngredient.objects.filter(recipe=instance).delete()
        self.add_ingredients(instance, ingredients)

        instance.save()

        return instance

    def add_tags(self, recipe, tag_ids):
        for tag_id in tag_ids:
            obj = get_object_or_404(models.Tag, pk=tag_id)
            r_t, _ = models.RecipeTag.objects.get_or_create(
                recipe=recipe,
                tag=obj,
            )

    def add_ingredients(self, recipe, ingredients):
        for ingredient in ingredients:
            obj = get_object_or_404(models.Ingredient, pk=ingredient.get('id'))
            r_i, _ = models.RecipeIngredient.objects.get_or_create(
                recipe=recipe,
                ingredient=obj,
                amount=ingredient.get('amount')
            )

    def get_is_favorited(self, obj: models.Recipe) -> bool:
        user = self.context.get('request').user
        if isinstance(user, AnonymousUser):
            return False

        favorite = models.FavoriteRecipe.objects.filter(
            user=user,
            recipe=obj
        )
        return favorite.count() != 0

    def get_is_in_shopping_cart(self, obj: models.Recipe) -> bool:
        user = self.context.get('request').user
        if isinstance(user, AnonymousUser):
            return False

        cart = models.ShoppingCart.objects.filter(
            user=user,
            recipe=obj
        )
        return cart.count() != 0


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
