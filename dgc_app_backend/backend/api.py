import os
import logging
import hashlib
import base64
import uuid

import httpx
import jwt

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from django.conf import settings

from ninja import NinjaAPI, Schema
from ninja.security import HttpBearer
from cryptography.fernet import Fernet

from .models import (
    Patient,
    UserPatient,
    SharePatient
)
from .crypto import (
    derive_key,
    decrypt_str,
    encrypt_bytes,
    encrypt_str,
    decrypt_bytes
)
from .auth import AuthBearer

logger = logging.getLogger(__name__)


api = NinjaAPI()

@api.get("/hello", auth=AuthBearer())
def hello(request):
    return request.auth.name


class PatientSchema(Schema):
    id: UUID
    name: str
    date_of_birth: date

    @classmethod
    def from_encrypted_patient(cls, patient: Patient, patient_key: Fernet):
        return cls(
            id=patient.id,
            name=decrypt_str(patient_key, patient.name),
            date_of_birth=date.fromisoformat(decrypt_str(patient_key, patient.date_of_birth))
        )

class PatientsSchema(Schema):
    patients: list[PatientSchema]

@api.get("/patients", auth=AuthBearer(), response=PatientsSchema)
def patients(request):
    ret: list[PatientSchema] = []
    patients = Patient.objects.filter(users=request.auth.user)

    for patient in patients:
        user_patient = UserPatient.objects.get(
            user=request.auth.user,
            patient=patient
        )

        (_, patient_key) = user_patient.decrypt_patient_key(request.auth.key)

        ret.append(PatientSchema.from_encrypted_patient(patient, patient_key))

    return {"patients": ret}


class NewPatientSchema(Schema):
    name: str
    date_of_birth: date

@api.post("/patients", auth=AuthBearer(), response=PatientSchema)
def add_patient(request, data: NewPatientSchema):
    patient_key = Fernet.generate_key()
    patient_f = Fernet(patient_key)

    encrypted_name = encrypt_str(patient_f, data.name)
    encrypted_date_of_birth = encrypt_str(patient_f, data.date_of_birth.isoformat())

    patient = Patient.objects.create(
        name=encrypted_name,
        date_of_birth=encrypted_date_of_birth
    )

    encrypted_patient_key = encrypt_bytes(request.auth.key, patient_key)

    UserPatient.objects.create(
        user=request.auth.user,
        patient=patient,
        encrypted_patient_key=encrypted_patient_key
    )

    ret = PatientSchema.from_encrypted_patient(patient, patient_f)
    return ret


class UpdatePatientSchema(Schema):
    name: str | None = None
    date_of_birth: date | None = None

@api.patch("/patients/{patient_id}", auth=AuthBearer(), response={200: PatientSchema, 404: None})
def update_patient(request, patient_id: str, data: UpdatePatientSchema):
    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return 404, None

    user_patient = UserPatient.objects.get(
        user=request.auth.user,
        patient=patient
    )

    (_, patient_key) = user_patient.decrypt_patient_key(request.auth.key)

    if data.name is not None:
        patient.name = encrypt_str(patient_key, data.name)

    if data.date_of_birth is not None:
        patient.date_of_birth = encrypt_str(patient_key, data.date_of_birth.isoformat())

    patient.save()

    ret = PatientSchema.from_encrypted_patient(patient, patient_key)

    return 200, ret

@api.delete("/patients/{patient_id}", auth=AuthBearer(), response={204: None, 404: None})
def delete_patient(request, patient_id: str):
    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return 404, None

    # Shouldn't be able to delete just by knowing the ID
    try:
        UserPatient.objects.get(
            user=request.auth.user,
            patient=patient
        )
    except:
        return 404, None

    patient.delete()
    return 204, None


class SharePatientSchema(Schema):
    token: str

@api.post("/patients/{patient_id}/share", auth=AuthBearer(), response={200: SharePatientSchema, 404: None})
def share_patient(request, patient_id: str):
    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return 404, None

    # Shouldn't be able to share just by knowing the ID
    try:
        user_patient = UserPatient.objects.get(
            user=request.auth.user,
            patient=patient
        )
    except:
        return 404, None

    (patient_key, _) = user_patient.decrypt_patient_key(request.auth.key)

    password = str(uuid.uuid4())

    salt = os.urandom(32).hex()
    iterations = 100000

    share_key = derive_key(password, salt, iterations)

    encrypted_patient_key = share_key.encrypt(patient_key)
    encrypted_patient_key = base64.urlsafe_b64encode(encrypted_patient_key).decode('utf-8')

    share_record = SharePatient.objects.create(
        salt=salt,
        iterations=iterations,
        encrypted_patient_key=encrypted_patient_key,
        patient=patient
    )

    return {
        "token": f"{share_record.id}.{password}"
    }


@api.post("/patients-from-share", auth=AuthBearer(), response={200: PatientSchema, 401: None})
def get_patient_from_share(request, data: SharePatientSchema):
    share_id = data.token.split('.')[0]
    password = data.token.split('.')[1]

    try:
        share_record = SharePatient.objects.get(id=share_id)
    except SharePatient.DoesNotExist:
        return 401, None

    share_key = derive_key(password, share_record.salt, share_record.iterations)
    (patient_key, patient_key_f) = share_record.decrypt_patient_key(share_key)

    # Find the patient
    try:
        patient = Patient.objects.get(id=share_record.patient.id)
    except Patient.DoesNotExist:
        return 401, None

    # Check we have the right patient key (throws if key invalid)
    decrypt_str(patient_key_f, patient.name)

    # Re-encrypt the patient key for this user
    encrypted_patient_key = encrypt_bytes(request.auth.key, patient_key)

    UserPatient.objects.create(
        user=request.auth.user,
        patient=patient,
        encrypted_patient_key=encrypted_patient_key
    )

    share_record.delete()

    ret = PatientSchema.from_encrypted_patient(patient, patient_key_f)

    return 200, ret 