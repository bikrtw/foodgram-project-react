from django.contrib.auth import get_user_model
from django_filters import CharFilter, ModelMultipleChoiceFilter
from django_filters.rest_framework import FilterSet, BooleanFilter

from food.models import Recipe, RecipeTag, Tag

User = get_user_model()


class RecipeFilter(FilterSet):

    is_favorited = BooleanFilter(
        field_name='favorites', method='relation_filter')
    is_in_shopping_cart = BooleanFilter(
        field_name='shopping_cart', method='relation_filter')

    tags = ModelMultipleChoiceFilter(
        field_name='tag__slug',
        to_field_name='tags',
        queryset=Recipe.objects.all(),
    )

    def relation_filter(self, queryset, name, value):
        params = {f'{name}__user': self.request.user}
        if value:
            return queryset.filter(**params)
        return queryset.exclude(**params)

    class Meta:
        model = Recipe
        fields = ['author']
