from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models

admin.site.register(models.User, UserAdmin)

admin.site.register(models.Tag)
admin.site.register(models.Recipe)
admin.site.register(models.Ingredient)
admin.site.register(models.FavoriteRecipe)
admin.site.register(models.RecipeTag)
admin.site.register(models.ShoppingCart)
admin.site.register(models.Subscription)
