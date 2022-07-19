import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from django.db.transaction import atomic
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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

        return models.Subscription.objects.filter(
            user=user,
            subscribed_to=obj
        ).exists()

    def get_recipes(self,
                    obj: User
                    ) -> 'RecipeShortSerializer':
        limit = self.context['request'].query_params.get('recipes_limit')
        if limit is not None:
            if not limit.isdigit():
                raise ValidationError('recipes_limit should be int!')
            limit = int(limit)
            if limit < 1:
                raise ValidationError('recipes_limit should be > 0')

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
            if not tags.exists():
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
            if not ingredients.exists():
                raise ValidationError(
                    f'Ingredient with id {pk} does not exist')
        return value

    @atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tag_ids = validated_data.pop('tags')

        recipe = models.Recipe.objects.create(
            author=self.context['request'].user, **validated_data)

        self.add_tags(recipe, tag_ids)
        self.add_ingredients(recipe, ingredients)
        return recipe

    @atomic()
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
        links = []
        for tag_id in tag_ids:
            obj = models.Tag.objects.get(pk=tag_id)
            links.append(models.RecipeTag(recipe=recipe, tag=obj))
        models.RecipeTag.objects.bulk_create(links)

    def add_ingredients(self, recipe, ingredients):
        links = []
        for ingredient in ingredients:
            obj = models.Ingredient.objects.get(pk=ingredient.get('id'))
            links.append(models.RecipeIngredient(
                recipe=recipe,
                ingredient=obj,
                amount=ingredient.get('amount')
            ))
        models.RecipeIngredient.objects.bulk_create(links)

    def get_is_favorited(self, obj: models.Recipe) -> bool:
        user = self.context.get('request').user
        if isinstance(user, AnonymousUser):
            return False
        return models.FavoriteRecipe.objects.filter(
            user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj: models.Recipe) -> bool:
        user = self.context.get('request').user
        if isinstance(user, AnonymousUser):
            return False
        return models.ShoppingCart.objects.filter(
            user=user, recipe=obj).exists()


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
