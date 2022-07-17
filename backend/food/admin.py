from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    readonly_fields = ('favorited',)
    list_display = ('name', 'author', 'favorited')
    list_filter = ('name', 'author', 'tags')
    search_fields = ('name',)

    def favorited(self, obj: models.Recipe) -> int:
        return obj.favorites.count()


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


admin.site.register(models.User, UserAdmin)

admin.site.register(models.Tag)
admin.site.register(models.FavoriteRecipe)
admin.site.register(models.RecipeTag)
admin.site.register(models.ShoppingCart)
admin.site.register(models.Subscription)
admin.site.register(models.RecipeIngredient)
