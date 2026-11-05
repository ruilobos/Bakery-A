import csv
import io
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.admin.utils import quote
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
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


# 2.25: the user views store a hash, never what was typed (ADR-053).


def user_update_data(user, password):
    # date_joined's callable default renders a hidden initial the browser posts.
    return {
        "username": user.username,
        "password": password,
        "date_joined": "2026-11-01 08:00",
        "initial-date_joined": "2026-11-01 08:00",
        "is_active": "on",
    }


def test_user_create_stores_a_password_the_user_can_log_in_with(client, post):
    data = {
        "username": "baker",
        "password": "Secret-123",
        "date_joined": "2026-11-01 08:00",
        "is_active": "on",
    }

    assert post("users_create", data=data).status_code == 302

    assert get_user_model().objects.get(username="baker").password != "Secret-123"
    assert client.login(username="baker", password="Secret-123")


def test_user_update_hashes_a_changed_password(client, post, baker):
    data = user_update_data(baker, "Secret-123")

    assert post("users_update", baker.pk, data=data).status_code == 302

    baker.refresh_from_db()
    assert baker.password != "Secret-123"
    assert client.login(username="baker", password="Secret-123")
    assert not client.login(username="baker", password="x")


def test_user_update_leaves_an_unchanged_password_alone(post, baker):
    # The form shows the stored hash, so leaving it alone posts the hash back.
    stored = baker.password
    data = user_update_data(baker, stored)

    assert post("users_update", baker.pk, data=data).status_code == 302

    baker.refresh_from_db()
    assert baker.password == stored


def test_a_password_change_is_logged_by_name_never_by_value(
    post, audit_events, caplog, baker
):
    post("users_update", baker.pk, data=user_update_data(baker, "Secret-123"))

    assert [event["changed"] for event in audit_events()] == [["password"]]
    assert "Secret-123" not in caplog.text


# 2.26: a text cell a spreadsheet would run gains a leading `'`, and a number is
# written as it is (ADR-053). The negative numbers are there because `-` is a
# trigger: only the cell's type keeps them out.


@pytest.mark.parametrize("trigger", ["=", "+", "-", "@", "\t", "\r"])
def test_a_text_cell_starting_with_a_trigger_gains_the_prefix(client, trigger):
    Supplier.objects.create(name=f"{trigger}1+1", phone=12345678)

    rows = export_rows(client, "export_suppliers", "suppliers.csv")

    assert rows[1][0] == f"'{trigger}1+1"


def test_a_trigger_past_the_first_character_changes_nothing(client):
    Supplier.objects.create(
        name="Mill = Co",
        accNumber="AB-12",
        contact="Ana + Rui",
        phone=12345678,
        email="sales@mill.test",
        comment="5-10 bags",
    )

    assert export_rows(client, "export_suppliers", "suppliers.csv")[1] == [
        "Mill = Co",
        "AB-12",
        "Ana + Rui",
        "12345678",
        "sales@mill.test",
        "5-10 bags",
    ]


def test_supplier_export_neutralizes_text_and_leaves_numbers(client):
    Supplier.objects.create(
        name="=1+1",
        accNumber="+1+1",
        contact="-1+1",
        phone=-5,
        email="@SUM",
        comment="\t=1+1",
    )

    assert export_rows(client, "export_suppliers", "suppliers.csv")[1] == [
        "'=1+1",
        "'+1+1",
        "'-1+1",
        "-5",
        "'@SUM",
        "'\t=1+1",
    ]


def test_raw_material_export_neutralizes_text_and_leaves_numbers(client):
    RawMaterial.objects.create(
        description="+1+1",
        code="-1+1",
        supplier=Supplier.objects.create(name="=1+1", phone=12345678),
        categorie="@SUM",
        price=Decimal("-1.20"),
        quantity="=2",
        unit="\r=1",
    )

    assert export_rows(client, "export_raw_materials", "raw_materials.csv")[1] == [
        "'+1+1",
        "'-1+1",
        "'=1+1",
        "'@SUM",
        "-1.20",
        "'=2",
        "'\r=1",
    ]


def test_base_recipe_export_neutralizes_text_and_leaves_numbers(client):
    BaseRecipe.objects.create(name="=1+1", recipe_yield=-2, yield_unit="@KG")

    assert export_rows(client, "export_base_recipes", "base_recipes.csv")[1] == [
        "'=1+1",
        "-2",
        "'@KG",
    ]


def test_product_export_neutralizes_text_and_leaves_numbers(client):
    Product.objects.create(
        name="=1+1",
        categorie="+1",
        recipe_yield=Decimal("-4.00"),
        yield_unit="-KG",
        price=Decimal("-10.00"),
        vat=Decimal("-0.23"),
    )

    assert export_rows(client, "export_products", "products.csv")[1] == [
        "'=1+1",
        "'+1",
        "-4.00",
        "'-KG",
        "-10.00",
        "-0.23",
    ]


def test_a_raw_material_without_a_supplier_keeps_an_empty_cell(client):
    RawMaterial.objects.create(
        description="Flour",
        categorie="DRY GOODS",
        price=Decimal("1.20"),
        quantity="25",
        unit="KG",
    )

    rows = export_rows(client, "export_raw_materials", "raw_materials.csv")

    assert rows[1][2] == ""


# 2.15: the Django admin is superuser-only, and each page showing a model's rows
# logs who opened it (ADR-019, ADR-052).

SUPPLIER = "Mill & Co"  # The name raw_materials gives it; the admin escapes the &.


@pytest.fixture
def on_commit(django_capture_on_commit_callbacks):
    # Events are logged on commit, and each test runs inside a transaction.
    return lambda: django_capture_on_commit_callbacks(execute=True)


@pytest.fixture
def get(on_commit):
    def get(client, url, **query):
        with on_commit():
            return client.get(url, query)

    return get


def admin_view_event(actor, model, pk):
    target = {"model": model, "pk": pk}
    return {"action": "admin_view", "actor": actor.pk, "target": target}


@pytest.mark.parametrize(
    "flags",
    [None, {"is_staff": True}, {"is_superuser": True}],
    ids=["anonymous", "staff", "superuser-not-staff"],
)
def test_the_admin_refuses_all_but_a_superuser(client, get, audit_events, baker, flags):
    if flags:
        # Every permission, so that only the site's own check can refuse it.
        baker.user_permissions.set(Permission.objects.all())
        get_user_model().objects.filter(pk=baker.pk).update(**flags)
        client.force_login(baker)

    response = get(client, reverse("admin:control_supplier_changelist"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))
    assert audit_events() == []


def test_the_admin_admits_a_superuser(admin_client):
    assert admin_client.get(reverse("admin:index")).status_code == 200


def test_every_registered_model_logs_its_list(
    admin_client, admin_user, get, audit_events
):
    metas = [model._meta for model in admin.site._registry]

    for meta in metas:
        get(
            admin_client,
            reverse(f"admin:{meta.app_label}_{meta.model_name}_changelist"),
        )

    assert [without_time(event) for event in audit_events()] == [
        admin_view_event(admin_user, meta.label_lower, None) for meta in metas
    ]


@pytest.mark.parametrize("page", ["change", "delete", "history"])
def test_a_row_page_logs_the_row_under_its_real_primary_key(
    admin_client, admin_user, get, audit_events, raw_materials, page
):
    url = reverse(f"admin:control_supplier_{page}", args=[quote(SUPPLIER)])

    assert get(admin_client, url).status_code == 200

    assert [without_time(event) for event in audit_events()] == [
        admin_view_event(admin_user, "control.supplier", SUPPLIER)
    ]


@pytest.mark.parametrize("url_name", ["change", "password_change"])
def test_a_user_page_logs_the_integer_primary_key(
    admin_client, admin_user, get, audit_events, baker, url_name
):
    url = reverse(f"admin:auth_user_{url_name}", args=[baker.pk])

    assert get(admin_client, url).status_code == 200

    assert [without_time(event) for event in audit_events()] == [
        admin_view_event(admin_user, "auth.user", baker.pk)
    ]


def test_a_history_page_is_logged_on_a_model_the_inventory_does_not_name(
    admin_client, admin_user, get, audit_events
):
    cake = product([])

    get(admin_client, reverse("admin:control_product_history", args=[cake.pk]))

    assert [without_time(event) for event in audit_events()] == [
        admin_view_event(admin_user, "control.product", cake.pk)
    ]


def test_a_search_term_stays_out_of_the_event(
    admin_client, admin_user, get, audit_events, baker
):
    get(admin_client, reverse("admin:auth_user_changelist"), q=baker.username)

    assert [without_time(event) for event in audit_events()] == [
        admin_view_event(admin_user, "auth.user", None)
    ]


def test_a_delete_selected_confirmation_is_logged(
    admin_client, admin_user, on_commit, audit_events, raw_materials
):
    with on_commit():
        response = admin_client.post(
            reverse("admin:control_supplier_changelist"),
            {"action": "delete_selected", "_selected_action": [SUPPLIER]},
        )

    assertContains(response, SUPPLIER.replace("&", "&amp;"))
    assert [without_time(event) for event in audit_events()] == [
        admin_view_event(admin_user, "control.supplier", None)
    ]


def test_a_missing_row_logs_nothing(admin_client, get, audit_events):
    url = reverse("admin:control_supplier_change", args=["Nobody"])

    assert get(admin_client, url).status_code == 302

    assert audit_events() == []


def test_a_save_stays_in_the_admin_log_and_out_of_the_stream(
    admin_client, on_commit, audit_events, raw_materials
):
    url = reverse("admin:control_supplier_change", args=[quote(SUPPLIER)])

    with on_commit():
        response = admin_client.post(url, {"name": SUPPLIER, "phone": 12345678})

    assert response.status_code == 302
    assert LogEntry.objects.get().object_id == SUPPLIER
    assert audit_events() == []


def test_the_admins_own_pages_log_nothing(admin_client, get, audit_events):
    get(admin_client, reverse("admin:index"))

    assert audit_events() == []


def test_no_template_links_to_the_admin():
    root = Path(__file__).resolve().parent.parent
    templates = list(root.glob("*/templates/**/*.html"))
    link = re.compile(r"admin:|/admin")

    assert templates
    assert [
        path for path in templates if link.search(path.read_text(encoding="utf-8"))
    ] == []
