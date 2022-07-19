from django.contrib.auth import get_user_model
from django.forms import SlugField
from django_filters import CharFilter, ModelMultipleChoiceFilter, Filter
from django_filters.fields import MultipleChoiceField
from django_filters.rest_framework import FilterSet, BooleanFilter

from food.models import Recipe, RecipeTag, Tag

User = get_user_model()


class MultipleValueField(MultipleChoiceField):
    def __init__(self, *args, field_class, **kwargs):
        self.inner_field = field_class()
        super().__init__(*args, **kwargs)

    def valid_value(self, value):
        return self.inner_field.validate(value)

    def clean(self, values):
        return values and [self.inner_field.clean(value) for value in values]


class MultipleValueFilter(Filter):
    field_class = MultipleValueField

    def __init__(self, *args, field_class, **kwargs):
        kwargs.setdefault('lookup_expr', 'in')
        super().__init__(*args, field_class=field_class, **kwargs)


class RecipeFilter(FilterSet):

    is_favorited = BooleanFilter(
        field_name='favorites', method='relation_filter')
    is_in_shopping_cart = BooleanFilter(
        field_name='shopping_cart', method='relation_filter')

    tags = MultipleValueFilter(
        field_class=SlugField,
        field_name='tags__slug',
    )

    def relation_filter(self, queryset, name, value):
        params = {f'{name}__user': self.request.user}
        if value:
            return queryset.filter(**params)
        return queryset.exclude(**params)

    class Meta:
        model = Recipe
        fields = ['author']
