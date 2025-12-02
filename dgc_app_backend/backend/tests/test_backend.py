import pytest
from ninja.testing import TestClient
from ..api import api
from ..auth import generate_access_token, create_user

@pytest.fixture
def user_fixture():
    return create_user({
        "sub": "test_sub",
        "name": "Test User",
        "email": "test@example.com"
    })


client = TestClient(api)


@pytest.mark.django_db
def test_hello(user_fixture):
    access_token = generate_access_token(user_fixture.sub)

    response = client.get("/hello", headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200
    assert response.text == f"\"{user_fixture.name}\""


@pytest.mark.django_db
def test_initial_organisation_list(user_fixture):
    access_token = generate_access_token(user_fixture.sub)

    response = client.get("/organisations", headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200
    assert response.json() == []