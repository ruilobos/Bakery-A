import csv
import io
from decimal import Decimal

import pytest
from django.urls import reverse

from control.models import (
    BaseRecipe,
    Bs_Ingredients,
    Product,
    RawMaterial,
    Recipe_Ingredients,
    Supplier,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def raw_materials():
    supplier = Supplier.objects.create(name="Mill & Co", phone=12345678)
    return [
        RawMaterial.objects.create(
            description=description,
            supplier=supplier,
            categorie="DRY GOODS",
            price=Decimal("1.20"),
            quantity="25",
            unit="KG",
        )
        for description in ("Flour", "Sugar")
    ]


def export_rows(client, url_name, filename):
    response = client.get(reverse(f"control:{url_name}"))
    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert response["Content-Disposition"] == f'attachment; filename="{filename}"'
    return list(csv.reader(io.StringIO(response.content.decode())))


# Each recipe and product gets two ingredient lines: a to-many in values_list
# would write one row per line, which is why 1.17 drops the column rather than
# restoring it.


def test_base_recipe_export_writes_one_row_per_recipe(client, raw_materials):
    recipe = BaseRecipe.objects.create(name="Dough", recipe_yield=2, yield_unit="KG")
    for material in raw_materials:
        Bs_Ingredients.objects.create(
            ingredient=material,
            base_recipe=recipe,
            quantity=Decimal("1.500"),
            unit="KG",
        )

    assert export_rows(client, "export_base_recipes", "base_recipes.csv") == [
        ["name", "recipe_yield", "yield_unit"],
        ["Dough", "2", "KG"],
    ]


def test_product_export_writes_one_row_per_product(client, raw_materials):
    product = Product.objects.create(
        name="Cake",
        categorie="CAKES",
        recipe_yield=Decimal("4.00"),
        yield_unit="UNIT",
        price=Decimal("10.00"),
        vat=Decimal("0.23"),
    )
    for material in raw_materials:
        Recipe_Ingredients.objects.create(
            ingredient=material, product=product, quantity=Decimal("0.250"), unit="KG"
        )

    assert export_rows(client, "export_products", "products.csv") == [
        ["name", "categorie", "recipe_yield", "yield_unit", "price", "vat"],
        ["Cake", "CAKES", "4.00", "UNIT", "10.00", "0.23"],
    ]
