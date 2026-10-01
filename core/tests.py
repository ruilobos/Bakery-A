import pytest
from pytest_django.asserts import assertTemplateUsed


def test_cover_page_renders(client):
    # Settings, URLconf, template loading and pytest-django's client fixture,
    # end to end; the anonymous cover page touches no database.
    response = client.get('/')
    assert response.status_code == 200
    assertTemplateUsed(response, 'cover.html')


@pytest.mark.django_db
def test_test_database_is_usable(django_user_model):
    # pytest-django builds the test database through Django's own machinery
    # (ADR-034), against the compose postgres locally.
    django_user_model.objects.create_user(username='baker', password='unused')
    assert django_user_model.objects.filter(username='baker').exists()
