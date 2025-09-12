import uuid

from django.db import models
from cryptography.fernet import Fernet

from .crypto import decrypt_bytes

class User(models.Model):
    # SHA-256 hash of the "sub" claim from the OIDC token
    id = models.CharField(max_length=150, primary_key=True)

    salt = models.CharField(max_length=150)
    iterations = models.IntegerField(default=100000)

    def __str__(self):
        return self.id


class UserPatient(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE
    )
    patient = models.ForeignKey(
        to='Patient',
        on_delete=models.CASCADE
    )
    
    # Encrypted with the key derived from the user ID
    encrypted_patient_key = models.CharField(max_length=300)

    # Encrypted with the patient key - used for shared patients
    encrypted_user_name = models.CharField(max_length=300)
    encrypted_user_email = models.CharField(max_length=300)

    def decrypt_patient_key(self, user_key: Fernet) -> tuple[bytes, Fernet]:
        patient_key = decrypt_bytes(user_key, self.encrypted_patient_key)
        return (patient_key, Fernet(patient_key))

    class Meta:
        unique_together = ('user', 'patient')


class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    encrypted_name = models.CharField(max_length=300)
    encrypted_date_of_birth = models.CharField(max_length=300)

    users = models.ManyToManyField(
        to=User,
        through=UserPatient,
        related_name='patients'
    )

    def __str__(self):
        return str(self.id)


# TODO MRB: this needs to expire
class SharePatient(models.Model):
    # Plaintext ID to lookup this data
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # The password is not stored in the db but is included in the share link
    salt = models.CharField(max_length=150)
    iterations = models.IntegerField(default=100000)

    # Encrypted with the key derived from the password in the share link
    encrypted_patient_key = models.CharField(max_length=300)

    # Metadata about the share, also encrypted with the share key
    encrypted_sharer_name = models.CharField(max_length=300)
    encrypted_sharer_email = models.CharField(max_length=300)
    encrypted_patient_name = models.CharField(max_length=300)

    def decrypt_patient_key(self, share_key: Fernet) -> tuple[bytes, Fernet]:
        patient_key = decrypt_bytes(share_key, self.encrypted_patient_key)
        return (patient_key, Fernet(patient_key))

    patient = models.ForeignKey(
        to=Patient,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.id
