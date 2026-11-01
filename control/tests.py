import csv
import io
import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from pytest_django.asserts import assertContains

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


# 1.20 deleted margin_percent and margin_value, which read four attributes the
# model never had; ADR-018 deletes that costing rather than patching it.


def test_every_recipe_line_property_reads_fields_the_model_has():
    line = Recipe_Ingredients(
        ingredient=RawMaterial(price=Decimal("1.20")),
        product=Product(price=Decimal("10.00"), vat=Decimal("0.23")),
        quantity=Decimal("0.250"),
    )
    properties = [
        name
        for name, value in vars(Recipe_Ingredients).items()
        if isinstance(value, property)
    ]

    assert {name: getattr(line, name) for name in properties} == {
        "cost": "0.30",
        "net_price": "7.70",
    }


def test_products_page_renders_its_recipe_lines(client, raw_materials):
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

    response = client.get(reverse("control:products", args=["CAKES"]))

    assertContains(response, "<td>0.30</td>", count=2)


# 2.9: every user-management and delete view logs one audit event (ADR-052),
# naming actor and target by primary key and never a field's value.


@pytest.fixture
def audit_events(caplog):
    # bakery.audit does not propagate, so caplog's root handler never sees it.
    logger = logging.getLogger("bakery.audit")
    logger.addHandler(caplog.handler)
    yield lambda: [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "bakery.audit"
    ]
    logger.removeHandler(caplog.handler)


@pytest.fixture
def post(client, django_capture_on_commit_callbacks):
    # Events are logged on commit, and each test runs inside a transaction.
    def post(url_name, *args, data=None):
        with django_capture_on_commit_callbacks(execute=True):
            return client.post(reverse(f"control:{url_name}", args=args), data or {})

    return post


@pytest.fixture
def baker():
    return get_user_model().objects.create_user(
        "baker", password="x", date_joined=datetime(2026, 11, 1, 8, tzinfo=timezone.utc)
    )


def without_time(event):
    at = event.pop("at")
    assert datetime.fromisoformat(at).utcoffset() == timedelta(0)
    return event


def delete_event(model, pk):
    target = {"model": model._meta.label_lower, "pk": pk}
    return {"action": "delete", "actor": None, "target": target}


def base_recipe(materials):
    return BaseRecipe.objects.create(name="Dough", recipe_yield=2, yield_unit="KG")


def base_recipe_line(materials):
    return Bs_Ingredients.objects.create(
        ingredient=materials[0],
        base_recipe=base_recipe(materials),
        quantity=Decimal("1.500"),
        unit="KG",
    )


def product(materials):
    return Product.objects.create(
        name="Cake",
        categorie="CAKES",
        recipe_yield=Decimal("4.00"),
        yield_unit="UNIT",
        price=Decimal("10.00"),
        vat=Decimal("0.23"),
    )


def product_line(materials):
    return Recipe_Ingredients.objects.create(
        ingredient=materials[0],
        product=product(materials),
        quantity=Decimal("0.250"),
        unit="KG",
    )


@pytest.mark.parametrize(
    "url_name, make",
    [
        ("raw_materials_delete", lambda materials: materials[0]),
        # A supplier's primary key is its name until 3.5 (ADR-052's Traps).
        ("supplier_delete", lambda materials: materials[0].supplier),
        ("base_recipe_delete", base_recipe),
        pytest.param(
            "br_ingre_delete",
            base_recipe_line,
            marks=pytest.mark.xfail(
                strict=True,
                raises=ImproperlyConfigured,
                reason="6.27: Br_Ingre_Delete has no success_url, so it never deletes",
            ),
        ),
        ("pro_ingre_delete", product_line),
        ("products_delete", product),
    ],
)
def test_each_delete_view_logs_one_delete_event(
    post, audit_events, raw_materials, url_name, make
):
    target = make(raw_materials)
    model, pk = type(target), target.pk

    response = post(url_name, pk)

    assert response.status_code == 302
    assert not model.objects.filter(pk=pk).exists()
    assert [without_time(event) for event in audit_events()] == [
        delete_event(model, pk)
    ]


def test_user_delete_logs_the_raw_material_it_actually_deletes(
    post, audit_events, raw_materials
):
    # Until 6.7, User_Delete's model is RawMaterial; the event names what went.
    material = raw_materials[0]

    post("users_delete", material.pk)

    assert [without_time(event) for event in audit_events()] == [
        delete_event(RawMaterial, material.pk)
    ]


def test_user_create_logs_the_new_user(post, audit_events):
    data = {"username": "baker", "password": "x", "date_joined": "2026-11-01 08:00"}

    assert post("users_create", data=data).status_code == 302

    user = get_user_model().objects.get(username="baker")
    assert [without_time(event) for event in audit_events()] == [
        {
            "action": "create",
            "actor": None,
            "target": {"model": "auth.user", "pk": user.pk},
        }
    ]


def test_user_update_logs_the_names_of_the_changed_fields(post, audit_events, baker):
    # An anonymous request making a superuser: 2.7's problem, now on record.
    # date_joined's callable default renders a hidden initial the browser posts.
    data = {
        "username": "baker",
        "password": baker.password,
        "date_joined": "2026-11-01 08:00",
        "initial-date_joined": "2026-11-01 08:00",
        "is_active": "on",
        "is_superuser": "on",
    }

    assert post("users_update", baker.pk, data=data).status_code == 302

    assert [without_time(event) for event in audit_events()] == [
        {
            "action": "update",
            "actor": None,
            "target": {"model": "auth.user", "pk": baker.pk},
            "changed": ["is_superuser"],
        }
    ]


def test_a_signed_in_actor_is_logged_by_primary_key(
    client, post, audit_events, raw_materials, baker
):
    client.force_login(baker)

    post("raw_materials_delete", raw_materials[0].pk)

    assert [event["actor"] for event in audit_events()] == [baker.pk]


def test_a_failed_write_logs_nothing(post, audit_events):
    assert post("users_create", data={}).status_code == 200
    assert post("raw_materials_delete", 999).status_code == 404

    assert audit_events() == []
