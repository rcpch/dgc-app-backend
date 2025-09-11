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
   
    key = models.CharField(max_length=300)

    class Meta:
        unique_together = ('user', 'patient')


class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=300) # encrypted
    birth_date = models.CharField(max_length=10) # date but encrypted

    users = models.ManyToManyField(
        to=UserRegistration,
        through=UserPatientKey,
        related_name='patients'
    )

    def __str__(self):
        return self.id


