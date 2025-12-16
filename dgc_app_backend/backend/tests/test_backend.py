import pytest
from datetime import date
from ninja.testing import TestClient
from unittest.mock import patch, Mock

from ..api import api
from ..auth import generate_access_token, get_or_create_user
from ..models import User, Organisation, Child, UserOrganisation, UserRegistration
from ..crypto import sha_256
from ..organisations import create_organisation


@pytest.fixture
def user_fixture():
    auth_data = get_or_create_user({
        "iss": "test_issuer",
        "sub": "test_sub",
        "name": "Test User",
        "email": "test@example.com"
    })

    create_organisation(auth_data, organisation_name=None)

    return auth_data


@pytest.fixture(autouse=True)
def mock_dgc_api_call():
    with patch("dgc_app_backend.backend.api.call_bulk_dgc_api") as mock_call:
        mock_call.return_value = {}
        yield mock_call


@pytest.fixture(scope="session")
def client():
    client = TestClient(api)
    return client


@pytest.mark.django_db
def test_hello(user_fixture, client):
    access_token = generate_access_token(user_fixture.sub)

    response = client.get("/hello", headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200
    assert response.text == f"\"{user_fixture.name}\""


@pytest.mark.django_db
def test_sub_is_hashed(user_fixture, client):
    assert User.objects.count() == 1
    assert UserRegistration.objects.count() == 1

    user = User.objects.first()
    user_registration = UserRegistration.objects.first()

    assert user.id != user_fixture.sub
    assert user.id != sha_256(user_fixture.sub)

    assert user_registration.hashed_sub == sha_256(user_fixture.sub)


@pytest.mark.django_db
def test_user_pii_is_encrypted(user_fixture):
    assert User.objects.count() == 1
    assert UserOrganisation.objects.count() == 1

    user_org = UserOrganisation.objects.first()
    assert user_org.encrypted_user_name != user_fixture.name
    assert user_org.encrypted_user_email != user_fixture.email


@pytest.mark.django_db
def test_initial_organisation_list(user_fixture, client):
    access_token = generate_access_token(user_fixture.sub)

    response = client.get("/organisations", headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200
    
    orgs = response.json()["organisations"]
    assert len(orgs) == 1

    users = orgs[0]["users"]
    assert len(users) == 1

    assert users[0]["id"] == str(user_fixture.user.id)
    assert users[0]["is_current_user"] is True
    assert users[0]["is_creator"] is True


@pytest.mark.django_db
def test_child_in_single_org(user_fixture, client):
    access_token = generate_access_token(user_fixture.sub)

    organisation_id = Organisation.objects.first().id

    response = client.post(f"/organisations/{organisation_id}/children", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "name": "Child User",
        "date_of_birth": "2010-01-01",
        "sex": "female"
    })

    assert response.status_code == 200

    response = client.get(f"/children", headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200

    children = response.json()["children"]
    assert len(children) == 1

    assert children[0]["name"] == "Child User"
    assert children[0]["date_of_birth"] == "2010-01-01"
    assert children[0]["sex"] == "female"
    assert children[0]["organisation_ids"] == [str(organisation_id)]


@pytest.mark.django_db
def test_child_pii_is_encrypted(user_fixture, client):
    access_token = generate_access_token(user_fixture.sub)

    organisation_id = Organisation.objects.first().id

    client.post(f"/organisations/{organisation_id}/children", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "name": "Child User",
        "date_of_birth": "2010-01-01",
        "sex": "female"
    })

    child = Child.objects.first()

    assert child.encrypted_name != "Child User"
    assert child.encrypted_date_of_birth != "2010-01-01"

    assert child.sex == 1


@pytest.mark.django_db
def test_update_child(user_fixture, client):
    access_token = generate_access_token(user_fixture.sub)

    organisation_id = Organisation.objects.first().id

    response = client.post(f"/organisations/{organisation_id}/children", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "name": "Child User",
        "date_of_birth": "2010-01-01",
        "sex": "female"
    })

    assert response.status_code == 200

    child_id = response.json()["id"]

    response = client.patch(f"/children/{child_id}", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "name": "Updated Child User",
        "date_of_birth": "2011-02-02"
        # check not all fields need to be provided
    })

    assert response.status_code == 200

    response = client.get(f"/children", headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200

    children = response.json()["children"]
    assert len(children) == 1

    assert children[0]["name"] == "Updated Child User"
    assert children[0]["date_of_birth"] == "2011-02-02"
    assert children[0]["sex"] == "female"


@pytest.mark.django_db
def test_user_in_multiple_orgs(user_fixture, client):
    access_token = generate_access_token(user_fixture.sub)

    org1 = Organisation.objects.first()

    response = client.post("/organisations", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "name": "Second Organisation"
    })

    assert response.status_code == 200

    org2_id = response.json()["id"]

    response = client.get("/organisations", headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200

    orgs = response.json()["organisations"]
    assert len(orgs) == 2

    org_ids = {org["id"] for org in orgs}

    assert str(org1.id) in org_ids
    assert str(org2_id) in org_ids


@pytest.mark.django_db
def test_child_in_multiple_orgs(user_fixture, client):
    access_token = generate_access_token(user_fixture.sub)

    org1 = Organisation.objects.first()

    response = client.post("/organisations", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "name": "Second Organisation"
    })

    assert response.status_code == 200

    org2_id = response.json()["id"]
    org2 = Organisation.objects.get(id=org2_id)

    response = client.post(f"/organisations/{org1.id}/children", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "name": "Shared Child",
        "date_of_birth": "2010-01-01",
        "sex": "female"
    })

    assert response.status_code == 200

    child_id = response.json()["id"]

    # Add same child to second organisation
    response = client.put(f"/organisations/{org2_id}/children/{child_id}", headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 201
    
    response = client.get(f"/children", headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200

    children = response.json()["children"]
    assert len(children) == 1

    assert children[0]["name"] == "Shared Child"
    assert children[0]["date_of_birth"] == "2010-01-01"

    assert set(children[0]["organisation_ids"]) == {str(org1.id), str(org2.id)}


@pytest.mark.django_db
def test_add_observation(user_fixture, client):
    access_token = generate_access_token(user_fixture.sub)

    organisation_id = Organisation.objects.first().id

    # First create a child
    response = client.post(f"/organisations/{organisation_id}/children", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "name": "Child User",
        "date_of_birth": "2010-01-01",
        "sex": "male"
    })

    assert response.status_code == 200
    child_id = response.json()["id"]

    # Now add an observation
    response = client.post(f"/children/{child_id}/observations", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "observation_date": "2020-01-15",
        "observation_type": "height",
        "observation_value": 145.5
    })

    assert response.status_code == 201

    # Verify the observation appears in the children list
    response = client.get(f"/children/{child_id}/observations/uk-who", headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200

    observations = response.json()["observations"]
    assert len(observations) == 1

    observation = observations[0]
    assert observation["observation_type"] == "height"
    assert observation["observation_value"] == 145.5
    assert "dgc_api_result" in observation


# TODO MRB: add test for child in multiple orgs
#   - updates reflected cross org
#   - child deleted after last org reference
#   - doesn't leak ID of other org if the user doesn't have access to it
# TODO MRB: permission tests
#   - can't request children just by knowing org ID (will be removed anyway?)
#   - can't update or delete child just by knowing IDs
#   - can't create invite just by knowing org ID
# TODO MRB: create org and test PII encrypted
# TODO MRB: test redeeming invite and PII is still encrypted