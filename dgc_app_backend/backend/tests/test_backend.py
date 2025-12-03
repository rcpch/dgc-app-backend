import pytest
from ninja.testing import TestClient
from ..api import api
from ..auth import generate_access_token, create_user
from ..models import User, Organisation, Child, UserOrganisation
from ..crypto import sha_256
from ..organisations import create_organisation

@pytest.fixture
def user_fixture():
    auth_data = create_user({
        "sub": "test_sub",
        "name": "Test User",
        "email": "test@example.com"
    })

    create_organisation(auth_data, organisation_name=None)

    return auth_data


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
def test_user_pii_is_encrypted(user_fixture):
    assert User.objects.count() == 1
    assert UserOrganisation.objects.count() == 1

    user_org = UserOrganisation.objects.first()
    assert user_org.encrypted_user_name != user_fixture.name
    assert user_org.encrypted_user_email != user_fixture.email


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

    response = client.get(f"/children", headers={
        "Authorization": f"Bearer {access_token}"
    })

    assert response.status_code == 200

    children = response.json()["children"]
    assert len(children) == 1

    assert children[0]["name"] == "Child User"
    assert children[0]["date_of_birth"] == "2010-01-01"
    assert children[0]["organisation_ids"] == [str(organisation_id)]


@pytest.mark.django_db
def test_child_pii_is_encrypted(user_fixture):
    access_token = generate_access_token(user_fixture.sub)

    organisation_id = Organisation.objects.first().id

    client.post(f"/organisations/{organisation_id}/children", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "name": "Child User",
        "date_of_birth": "2010-01-01"
    })

    child = Child.objects.first()

    assert child.encrypted_name != "Child User"
    assert child.encrypted_date_of_birth != "2010-01-01"


@pytest.mark.django_db
def test_update_child(user_fixture):
    access_token = generate_access_token(user_fixture.sub)

    organisation_id = Organisation.objects.first().id

    response = client.post(f"/organisations/{organisation_id}/children", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "name": "Child User",
        "date_of_birth": "2010-01-01"
    })

    assert response.status_code == 200

    child_id = response.json()["id"]

    response = client.patch(f"/children/{child_id}", headers={
        "Authorization": f"Bearer {access_token}"
    }, json={
        "name": "Updated Child User",
        "date_of_birth": "2011-02-02"
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


@pytest.mark.django_db
def test_user_in_multiple_orgs(user_fixture):
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
def test_child_in_multiple_orgs(user_fixture):
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
        "date_of_birth": "2010-01-01"
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