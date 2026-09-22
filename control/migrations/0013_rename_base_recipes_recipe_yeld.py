from django.db import migrations


class Migration(migrations.Migration):
    """Rename the two prototype identifiers Epic 3 leaves behind (task 1.7, ADR-039).

    Written by hand rather than generated: `makemigrations` asks interactively whether a
    rename occurred, and answering no — which `--no-input` does — emits DeleteModel plus
    CreateModel and drops the table.
    """

    dependencies = [
        ('control', '0012_auto_20210427_1652'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Base_recipes',
            new_name='BaseRecipe',
        ),
        migrations.RenameField(
            model_name='baserecipe',
            old_name='recipe_yeld',
            new_name='recipe_yield',
        ),
        migrations.RenameField(
            model_name='product',
            old_name='recipe_yeld',
            new_name='recipe_yield',
        ),
    ]
