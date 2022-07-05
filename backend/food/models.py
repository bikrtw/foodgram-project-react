from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    name = models.TextField(max_length=255, db_index=True, unique=True)
    unit = models.TextField(max_length=20)


class Tag(models.Model):
    name = models.TextField(max_length=255, db_index=True, unique=True)
    slug = models.SlugField(unique=True)
    color = models.TextField(
        max_length=7,
        validators=[RegexValidator(regex=r'#[0-9,A-F]{6}')],
    )


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    name = models.TextField(max_length=255, unique=True)
    image = models.ImageField()
    text = models.TextField()
    cooking_time = models.IntegerField(
        validators=[MinValueValidator(0)],
    )


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    subscribed_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed',
    )

    # TODO unique validation


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='tags',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='recipes',
    )

    # TODO unique validation


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart_user'
    )

    # TODO unique validation


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites_user'
    )
