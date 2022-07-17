from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models
from django.db.models import Q, F
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True, max_length=254)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'


class Ingredient(models.Model):
    name = models.TextField(max_length=255, db_index=True, unique=True)
    measurement_unit = models.TextField(max_length=20)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.TextField(max_length=255, db_index=True, unique=True)
    slug = models.SlugField(unique=True)
    color = models.TextField(
        max_length=7,
        validators=[RegexValidator(regex=r'#[0-9,A-F]{6}')],
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


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
    tags = models.ManyToManyField('Tag', through='RecipeTag',
                                  related_name='recipes')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name}({self.cooking_time})'


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribed_to'],
                name='unique_subscription',
            ),
            models.CheckConstraint(
                check=~Q(user=F('subscribed_to')),
                name='no_self_subscription',
            ),
        ]

    def __str__(self):
        return f'{self.user} -> {self.subscribed_to}'


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tag'],
                name='unique_recipe_tag',
            ),
        ]

    def __str__(self):
        return f'{self.recipe} - {self.tag}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_recipe_user',
            ),
        ]

    def __str__(self):
        return f'{self.user}: {self.recipe}'


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_recipe_user',
            ),
        ]

    def __str__(self):
        return f'{self.user}: {self.recipe}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    amount = models.IntegerField(validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            ),
        ]

    def __str__(self):
        return f'{self.recipe}: {self.ingredient} -> {self.amount}'
