import csv
import io
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest import mock

import pytest
from django.contrib import admin
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.admin.utils import quote
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

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


# 2.27: each admin write is mirrored into the stream, where it outlives its user,
# and the admin deactivates an account instead of deleting it (ADR-054).


def write_event(action, actor, model, pk, **details):
    target = {"model": model, "pk": pk}
    return {"action": action, "actor": actor.pk, "target": target, **details}


def log_entry(user, change_message=""):
    supplier = ContentType.objects.get_for_model(Supplier)
    return LogEntry.objects.log_action(
        user.pk, supplier.pk, SUPPLIER, SUPPLIER, CHANGE, change_message
    )


def user_admin_data(user):
    # Every field UserAdmin's form requires, with the hidden initial date_joined's
    # callable default renders. Leaving `is_active` out unticks it.
    return {
        "username": user.username,
        "date_joined_0": "2026-11-01",
        "date_joined_1": "08:00:00",
        "initial-date_joined_0": "2026-11-01",
        "initial-date_joined_1": "08:00:00",
    }


def test_an_added_row_logs_create(admin_client, admin_user, on_commit, audit_events):
    with on_commit():
        response = admin_client.post(
            reverse("admin:control_supplier_add"), {"name": SUPPLIER, "phone": 1}
        )

    assert response.status_code == 302
    assert [without_time(event) for event in audit_events()] == [
        write_event("create", admin_user, "control.supplier", SUPPLIER)
    ]


def test_a_save_logs_the_labels_it_changed_never_their_values(
    admin_client, admin_user, on_commit, audit_events, raw_materials
):
    url = reverse("admin:control_supplier_change", args=[quote(SUPPLIER)])

    with on_commit():
        response = admin_client.post(url, {"name": SUPPLIER, "phone": 87654321})

    assert response.status_code == 302
    assert LogEntry.objects.get().object_id == SUPPLIER
    [event] = audit_events()
    assert "87654321" not in json.dumps(event)
    assert without_time(event) == write_event(
        "update", admin_user, "control.supplier", SUPPLIER, changed=["Phone Number"]
    )


def test_a_deleted_row_logs_delete_under_its_integer_primary_key(
    admin_client, admin_user, on_commit, audit_events
):
    pk = product([]).pk

    with on_commit():
        response = admin_client.post(
            reverse("admin:control_product_delete", args=[pk]), {"post": "yes"}
        )

    assert response.status_code == 302
    assert not Product.objects.filter(pk=pk).exists()
    assert [without_time(event) for event in audit_events()] == [
        write_event("delete", admin_user, "control.product", pk)
    ]


def test_delete_selected_logs_each_row(
    admin_client, admin_user, on_commit, audit_events
):
    # Two rows on purpose: Django 5.2 logs one row with save(), which sends
    # post_save, and two or more with bulk_create, which does not. Failing here at
    # 19.4 is this test's job, so never reduce it to one row to get past it.
    names = ["Mill & Co", "Oat & Sons"]
    for name in names:
        Supplier.objects.create(name=name, phone=1)

    with on_commit():
        response = admin_client.post(
            reverse("admin:control_supplier_changelist"),
            {"action": "delete_selected", "_selected_action": names, "post": "yes"},
        )

    assert response.status_code == 302
    assert not Supplier.objects.exists()
    events = [without_time(event) for event in audit_events()]
    assert sorted(events, key=lambda event: event["target"]["pk"]) == [
        write_event("delete", admin_user, "control.supplier", name) for name in names
    ]


def test_a_password_change_logs_no_hash(
    admin_client, admin_user, on_commit, audit_events, baker
):
    password = "A-long-Unusual-phrase-42"

    with on_commit():
        response = admin_client.post(
            reverse("admin:auth_user_password_change", args=[baker.pk]),
            {"password1": password, "password2": password},
        )

    assert response.status_code == 302
    baker.refresh_from_db()
    assert baker.check_password(password)
    [event] = audit_events()
    assert baker.password not in json.dumps(event)
    assert password not in json.dumps(event)
    assert without_time(event) == write_event(
        "update", admin_user, "auth.user", baker.pk, changed=["password"]
    )


def test_only_the_fields_lists_of_a_change_message_are_read(
    admin_user, on_commit, audit_events, raw_materials
):
    # An inline's entry holds `str(obj)` beside its `fields`, and that is a value.
    inline = {"name": "ingredient line", "object": "Jane Doe"}

    with on_commit():
        log_entry(
            admin_user,
            [
                {"changed": {"fields": ["Phone Number"]}},
                {"changed": {**inline, "fields": ["Quantity", "Phone Number"]}},
                {"added": inline},
                {"deleted": inline},
            ],
        )

    [event] = audit_events()
    assert event["changed"] == ["Phone Number", "Quantity"]
    assert "Jane Doe" not in json.dumps(event)


def test_a_plain_text_change_message_logs_no_labels(
    admin_user, on_commit, audit_events, raw_materials
):
    # Django allows one, and a mirror must never be what fails an admin write.
    with on_commit():
        log_entry(admin_user, "Approved by Jane Doe")

    [event] = audit_events()
    assert event["changed"] == []
    assert "Jane Doe" not in json.dumps(event)


def test_a_delete_that_fails_logs_nothing(
    admin_client, on_commit, audit_events, raw_materials
):
    # The admin writes its LogEntry before it deletes, and the rollback takes both.
    url = reverse("admin:control_supplier_delete", args=[quote(SUPPLIER)])
    delete_model = mock.patch.object(
        admin.site._registry[Supplier], "delete_model", side_effect=RuntimeError
    )

    with on_commit(), delete_model, pytest.raises(RuntimeError):
        admin_client.post(url, {"post": "yes"})

    assert Supplier.objects.filter(pk=SUPPLIER).exists()
    assert not LogEntry.objects.exists()
    assert audit_events() == []


def test_a_fixture_load_logs_nothing(
    admin_user, on_commit, audit_events, raw_materials
):
    entry = log_entry(admin_user)
    fixture = serializers.serialize("json", [entry])
    entry.delete()

    with on_commit():
        for row in serializers.deserialize("json", fixture):
            row.save()

    assert LogEntry.objects.count() == 1
    assert audit_events() == []


def test_saving_an_existing_entry_logs_nothing(
    admin_user, on_commit, audit_events, raw_materials
):
    entry = log_entry(admin_user)

    with on_commit():
        entry.save()

    assert audit_events() == []


@pytest.mark.parametrize("method", ["get", "post"])
def test_the_admin_refuses_to_delete_a_user(
    admin_client, on_commit, audit_events, baker, method
):
    url = reverse("admin:auth_user_delete", args=[baker.pk])

    with on_commit():
        response = getattr(admin_client, method)(url, {"post": "yes"})

    assert response.status_code == 403
    assert get_user_model().objects.filter(pk=baker.pk).exists()
    assert audit_events() == []


def test_delete_selected_cannot_reach_a_user(
    admin_client, on_commit, audit_events, baker
):
    url = reverse("admin:auth_user_changelist")

    assertNotContains(admin_client.get(url), "delete_selected")
    with on_commit():
        admin_client.post(
            url,
            {
                "action": "delete_selected",
                "_selected_action": [baker.pk],
                "post": "yes",
            },
        )

    assert get_user_model().objects.filter(pk=baker.pk).exists()
    assert "delete" not in [event["action"] for event in audit_events()]


def test_a_user_page_offers_no_delete_link(admin_client, baker):
    page = admin_client.get(reverse("admin:auth_user_change", args=[baker.pk]))

    assert page.status_code == 200
    assertNotContains(page, reverse("admin:auth_user_delete", args=[baker.pk]))


def test_deactivating_keeps_the_account_and_stops_its_sign_in(
    admin_client, admin_user, client, on_commit, audit_events, baker
):
    url = reverse("admin:auth_user_change", args=[baker.pk])

    with on_commit():
        response = admin_client.post(url, user_admin_data(baker))

    assert response.status_code == 302
    baker.refresh_from_db()
    assert baker.is_active is False
    assert baker.check_password("x")
    assert not client.login(username="baker", password="x")
    assert [without_time(event) for event in audit_events()] == [
        write_event("update", admin_user, "auth.user", baker.pk, changed=["Active"]),
        login_event("login_failed", None, baker.pk),
    ]


# 2.28: the admin's autocomplete endpoint is closed, since no page calls it
# (ADR-054).

# Django serves this from `UserAdmin.search_fields`, whether or not any admin
# declares `autocomplete_fields`, and `LogEntry` needs no registration.
USERNAME_LOOKUP = {
    "app_label": "admin",
    "model_name": "logentry",
    "field_name": "user",
    "term": "baker",
}


def test_autocomplete_returns_no_usernames_to_a_superuser(
    admin_client, get, audit_events, baker
):
    response = get(admin_client, reverse("admin:autocomplete"), **USERNAME_LOOKUP)

    # Not the JSON list of `{"id": ..., "text": username}` it used to return.
    assert response.status_code == 404
    assert response["Content-Type"] != "application/json"
    assert audit_events() == []


def test_autocomplete_still_sends_anyone_else_to_sign_in(client, get, audit_events):
    response = get(client, reverse("admin:autocomplete"), **USERNAME_LOOKUP)

    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))
    assert audit_events() == []


def test_no_admin_declares_autocomplete_fields():
    # Its widget would call the closed endpoint and fail only in the browser.
    # Turning autocomplete back on means logging it first (ADR-054).
    admins = [type(model_admin) for model_admin in admin.site._registry.values()]
    inlines = [inline for model_admin in admins for inline in model_admin.inlines]

    assert admins
    assert [cls.__name__ for cls in admins + inlines if cls.autocomplete_fields] == []


# 2.23: a sign-in logs `login`, a refused one `login_failed`, and neither carries
# what was typed (ADR-052). A refusal writes nothing to wait for, so the tests
# that expect one alone run without `on_commit`: it is logged at once.

WRONG = "Wrong-Secret-456"  # Distinctive, so `caplog.text` can be searched for it.


def sign_in(client, username, password, url_name="login"):
    return client.post(reverse(url_name), {"username": username, "password": password})


def login_event(action, actor_pk, pk, **details):
    target = {"model": "auth.user", "pk": pk}
    return {"action": action, "actor": actor_pk, "target": target, **details}


def test_a_sign_in_logs_login(client, on_commit, audit_events, baker):
    with on_commit():
        response = sign_in(client, "baker", "x")

    assert response.status_code == 302
    assert [without_time(event) for event in audit_events()] == [
        login_event("login", baker.pk, baker.pk)
    ]


def test_a_wrong_password_logs_the_account_never_the_password(
    client, audit_events, caplog, baker
):
    response = sign_in(client, "baker", WRONG)

    assert response.status_code == 200
    assert [without_time(event) for event in audit_events()] == [
        login_event("login_failed", None, baker.pk)
    ]
    assert WRONG not in caplog.text


def test_an_unknown_account_is_named_by_its_username(client, audit_events, caplog):
    response = sign_in(client, "nobody", WRONG)

    assert response.status_code == 200
    assert [without_time(event) for event in audit_events()] == [
        login_event("login_failed", None, None, username="nobody")
    ]
    assert WRONG not in caplog.text


def test_a_deactivated_account_logs_a_failed_login(client, audit_events, baker):
    get_user_model().objects.filter(pk=baker.pk).update(is_active=False)

    response = sign_in(client, "baker", "x")

    assert response.status_code == 200
    assert [without_time(event) for event in audit_events()] == [
        login_event("login_failed", None, baker.pk)
    ]


def test_a_signed_in_actor_is_named_on_a_failed_attempt(client, audit_events, baker):
    other = get_user_model().objects.create_user("other", password="y")
    client.force_login(baker)

    sign_in(client, "other", WRONG)

    assert [without_time(event) for event in audit_events()] == [
        login_event("login_failed", baker.pk, other.pk)
    ]


def test_a_blank_password_is_no_attempt(client, on_commit, audit_events, baker):
    # The form refuses it before it calls `authenticate()`.
    with on_commit():
        response = sign_in(client, "baker", "")

    assert response.status_code == 200
    assert audit_events() == []


def test_an_admin_sign_in_logs_login(client, on_commit, audit_events, admin_user):
    with on_commit():
        response = sign_in(client, "admin", "password", url_name="admin:login")

    assert response.status_code == 302
    assert [without_time(event) for event in audit_events()] == [
        login_event("login", admin_user.pk, admin_user.pk)
    ]


@pytest.mark.parametrize(
    "password", ["x", WRONG], ids=["right-password-not-staff", "wrong-password"]
)
def test_the_admin_logs_one_failed_login_for_an_account_it_refuses(
    client, on_commit, audit_events, caplog, baker, password
):
    # `on_commit` too, so that a `login` waiting on commit would show up as well.
    with on_commit():
        response = sign_in(client, "baker", password, url_name="admin:login")

    assert response.status_code == 200
    assert [without_time(event) for event in audit_events()] == [
        login_event("login_failed", None, baker.pk)
    ]
    assert WRONG not in caplog.text
