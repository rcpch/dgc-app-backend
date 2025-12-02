import pytest
from ninja.testing import TestClient
from ..api import api
from ..auth import generate_access_token, create_user
from ..models import User, Organisation
from ..crypto import sha_256

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
def test_sub_is_hashed(user_fixture):
    user = User.objects.first()
    assert user.id == sha_256(user_fixture.sub)


@pytest.mark.django_db
def test_initial_organisation_list(user_fixture):
    access_token = generate_access_token(user_fixture.sub)

    response = client.get("/organisations", headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200
    
    orgs = response.json()["organisations"]
    assert len(orgs) == 1

    users = orgs[0]["users"]
    assert len(users) == 1

    assert users[0]["id"] == sha_256(user_fixture.sub)
    assert users[0]["is_current_user"] is True
    assert users[0]["is_creator"] is True


@pytest.mark.django_db
def test_child_in_single_org(user_fixture):
    access_token = generate_access_token(user_fixture.sub)

    organisation_id = Organisation.objects.first().id

    response = client.post(f"/organisations/{organisation_id}/children", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "name": "Child User",
        "date_of_birth": "2010-01-01"
    })

    assert response.status_code == 200

    response = client.get(f"/organisations/{organisation_id}/children", headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200

    children = response.json()["children"]
    assert len(children) == 1

    assert children[0]["name"] == "Child User"
    assert children[0]["date_of_birth"] == "2010-01-01"