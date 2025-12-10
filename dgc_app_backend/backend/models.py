import uuid

from django.db import models
from cryptography.fernet import Fernet

from .crypto import decrypt_bytes

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Placeholder to allow for normalised users in the future
    # e.g. a user who logs in with Google and later on uses NHS login

    def __str__(self):
        return self.id


class UserRegistration(models.Model):
    oauth_iss = models.CharField(max_length=300)

    # SHA-256 hash of the "sub" claim from the OIDC token
    hashed_sub = models.CharField(max_length=150, primary_key=True)

    # Used to derive the user key from the plaintext "sub" claim
    salt = models.CharField(max_length=150)
    iterations = models.IntegerField()

    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('oauth_iss', 'hashed_sub')


class Organisation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Encrypted with the organisation key
    encrypted_name = models.CharField(max_length=300, blank=True, null=True)


class UserOrganisation(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE
    )
    organisation = models.ForeignKey(
        to=Organisation,
        on_delete=models.CASCADE
    )

    is_creator = models.BooleanField()

    # Encrypted with the user key (derived from the user ID)
    encrypted_organisation_key = models.CharField(max_length=300)

    # Encrypted with the organisation key
    encrypted_user_name = models.CharField(max_length=300)
    encrypted_user_email = models.CharField(max_length=300)

    def decrypt_organisation_key(self, user_key: Fernet) -> tuple[bytes, Fernet]:
        organisation_key = decrypt_bytes(user_key, self.encrypted_organisation_key)
        return (organisation_key, Fernet(organisation_key))

    class Meta:
        unique_together = ('user', 'organisation')


class Child(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Encrypted with the child key
    encrypted_name = models.CharField(max_length=300)
    encrypted_date_of_birth = models.CharField(max_length=300)

    # Plaintext - for analysis
    sex = models.PositiveSmallIntegerField(
        choices=[
            (0, 'male'),
            (1, 'female'),
        ]
    )

    # Only set if known, otherwise term is assumed when calling the API
    gestation_days = models.PositiveIntegerField(blank=True, null=True)

    # Plaintext - for analysis
    days_since_birth = models.PositiveIntegerField()

    # TODO: in the future add plaintext linkage identifiers like NHS number

    def __str__(self):
        return str(self.id)


class ChildOrganisation(models.Model):
    # Encrypted with the organisation key
    encrypted_child_key = models.CharField(max_length=300)

    child = models.ForeignKey(
        to=Child,
        on_delete=models.CASCADE
    )
    organisation = models.ForeignKey(
        to=Organisation,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('child', 'organisation')


class Observation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Encrypted with the child key
    encrypted_dgc_api_result = models.CharField(max_length=10000)

    observation_type = models.PositiveSmallIntegerField(
        choices=[
            (1, "height"),
            (2, "weight"),
            (3, "ofc")
        ]
    )

    observation_value = models.DecimalField(max_digits=5, decimal_places=2)

    child = models.ForeignKey(
        to=Child,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.id)


# TODO MRB: this needs to expire
class OrganisationInvite(models.Model):
    # Plaintext ID to lookup this data
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # The password is not stored in the db but is included in the share link
    salt = models.CharField(max_length=150)
    iterations = models.IntegerField(default=100000)

    # Encrypted with the key derived from the password in the share link
    encrypted_organisation_key = models.CharField(max_length=300)

    def decrypt_organisation_key(self, share_key: Fernet) -> tuple[bytes, Fernet]:
        organisation_key = decrypt_bytes(share_key, self.encrypted_organisation_key)
        return (organisation_key, Fernet(organisation_key))

    organisation = models.ForeignKey(
        to=Organisation,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.id
