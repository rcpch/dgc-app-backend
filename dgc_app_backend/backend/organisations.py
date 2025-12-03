from cryptography.fernet import Fernet
from django.shortcuts import get_object_or_404

from .models import Organisation, UserOrganisation, User
from .auth import AuthData
from .crypto import (
    derive_key,
    decrypt_str,
    encrypt_bytes,
    encrypt_str,
)

def create_organisation(auth_data: AuthData, organisation_name: str | None) -> Organisation:
    organisation_key = Fernet.generate_key()
    organisation_f = Fernet(organisation_key)

    encrypted_name = encrypt_str(organisation_f, organisation_name) if organisation_name else None
    organisation = Organisation.objects.create(
        encrypted_name=encrypted_name
    )

    encrypted_organisation_key = encrypt_bytes(auth_data.key, organisation_key)

    # TODO MRB: what should we do if these change the next time a user logs in?
    encrypted_user_name = encrypt_str(organisation_f, auth_data.name)
    encrypted_user_email = encrypt_str(organisation_f, auth_data.email)
    UserOrganisation.objects.create(
        user=auth_data.user,
        organisation=organisation,
        encrypted_organisation_key=encrypted_organisation_key,
        encrypted_user_name=encrypted_user_name,
        encrypted_user_email=encrypted_user_email,
        is_creator=True
    )

    return organisation
