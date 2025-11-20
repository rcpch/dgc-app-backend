from cryptography.fernet import Fernet

from .models import Organisation, UserOrganisation, User
from .crypto import (
    derive_key,
    decrypt_str,
    encrypt_bytes,
    encrypt_str,
)

def create_organisation(user: User, user_key: bytes, organisation_name: str | None) -> Organisation:
    organisation_key = Fernet.generate_key()
    organisation_f = Fernet(organisation_key)

    encrypted_name = encrypt_str(organisation_f, organisation_name) if organisation_name else None
    organisation = Organisation.objects.create(
        encrypted_name=encrypted_name
    )

    encrypted_organisation_key = encrypt_bytes(user_key, organisation_key)

    username = decrypt_str(user_key, user.encrypted_name)
    email = decrypt_str(user_key, user.encrypted_email)

    # TODO MRB: what should we do if these change the next time a user logs in?
    encrypted_user_name = encrypt_str(organisation_f, username)
    encrypted_user_email = encrypt_str(organisation_f, email)
    UserOrganisation.objects.create(
        user=user,
        organisation=organisation,
        encrypted_organisation_key=encrypted_organisation_key,
        encrypted_user_name=encrypted_user_name,
        encrypted_user_email=encrypted_user_email,
        is_creator=True
    )

    return organisation