import uuid
from django.db import models

class UserRegistration(models.Model):
    id = models.CharField(max_length=150, primary_key=True)
    salt = models.CharField(max_length=150)
    iterations = models.IntegerField(default=100000)

    def __str__(self):
        return self.id


class UserPatientKey(models.Model):
    user = models.ForeignKey(
        to=UserRegistration,
        on_delete=models.CASCADE
    )
    patient = models.ForeignKey(
        to='Patient',
        on_delete=models.CASCADE
    )
    
    # Encrypted with the key derived from the user ID
    key = models.CharField(max_length=300)

    class Meta:
        unique_together = ('user', 'patient')


class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=300) # encrypted
    birth_date = models.CharField(max_length=300) # date but encrypted

    users = models.ManyToManyField(
        to=UserRegistration,
        through=UserPatientKey,
        related_name='patients'
    )

    def __str__(self):
        return str(self.id)


class SharePatient(models.Model):
    # Plaintext ID to lookup this data
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # The password is not stored in the db but is included in the share link
    salt = models.CharField(max_length=150)
    iterations = models.IntegerField(default=100000)

    # Encrypted with the key derived from the password in the share link
    key = models.CharField(max_length=300)

    patient = models.ForeignKey(
        to=Patient,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.id
