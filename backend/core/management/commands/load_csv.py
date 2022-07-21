import csv
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection

from food import models

FILES_PATH = ['test_data']

User = get_user_model()


class Command(BaseCommand):
    help = 'Loads a CSV files from static/data into the database'

    def handle(self, *args, **options):
        files_models = {
            'users': User,
            'tags': models.Tag,
            'ingredients': models.Ingredient,
            'recipes': models.Recipe,
            'subscriptions': models.Subscription,
            'recipe_ingredients': models.RecipeIngredient,
            'recipe_tags': models.RecipeTag,
            'shopping_cart': models.ShoppingCart,
            'favorites': models.FavoriteRecipe,
        }

        row_replacements = {
            # 'author': 'author_id',
        }

        for file_name, model in files_models.items():
            initial_count = model.objects.count()
            path = os.path.join(
                settings.BASE_DIR, *FILES_PATH, f'{file_name}.csv')
            print(f'Loading {path} into {model.__name__}')
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    for key, new_key in row_replacements.items():
                        if key in row:
                            row[new_key] = row[key]
                            del row[key]
                    try:
                        if model == User:
                            is_staff = row.pop('is_staff')
                            if is_staff == '1':
                                User.objects.create_superuser(**row)
                            else:
                                User.objects.create_user(**row)
                            continue
                        model.objects.update_or_create(**row)
                    except Exception as e:
                        print(e)
            final_count = model.objects.count()
            print(f'{model.__name__} loaded: {final_count - initial_count}')

        print('Resetting pk sequences for PostgreSQL')

        sequence_sql = connection.ops.sequence_reset_sql(
            no_style(), [model for model in files_models.values()])
        with connection.cursor() as cursor:
            for sql in sequence_sql:
                cursor.execute(sql)
        print('Done')
