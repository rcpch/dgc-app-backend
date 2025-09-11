import os

import logging
import hashlib
import base64

import httpx
import jwt

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from django.conf import settings

from ninja import NinjaAPI, Schema
from ninja.security import HttpBearer
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .backend.models import (
    UserRegistration,
    Patient,
    UserPatientKey
)

logger = logging.getLogger(__name__)

@dataclass
class AuthData:
    user: UserRegistration
    name: str
    key: bytes

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        url = f"{settings.DEMO_OAUTH_SERVER}/.well-known/openid-configuration"
        oidc_doc = httpx.get(url).json()

        signing_algos = oidc_doc["id_token_signing_alg_values_supported"]

        jwks_client = jwt.PyJWKClient(oidc_doc["jwks_uri"])
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=signing_algos,
            audience=settings.DEMO_OAUTH_CLIENT_ID,
            issuer=settings.DEMO_OAUTH_ISSUER,
            strict_aud=True
        )

        if token:
            m = hashlib.sha256()
            m.update(claims["sub"].encode('utf-8'))
            user_id = m.hexdigest()

            (user, _) = UserRegistration.objects.get_or_create(
                id=user_id,
                defaults={
                    "salt": os.urandom(32).hex()
                }
            )

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=user.salt.encode('utf-8'),
                iterations=user.iterations,
            )

            key = base64.urlsafe_b64encode(kdf.derive(user_id.encode('utf-8')))

            name = claims["name"]

            return AuthData(user, name, key)

api = NinjaAPI()

@api.get("/hello", auth=AuthBearer())
def hello(request):
    return request.auth.name


class PatientSchema(Schema):
    id: UUID
    name: str
    birth_date: date

class PatientsSchema(Schema):
    patients: list[PatientSchema]

@api.get("/patients", auth=AuthBearer(), response=PatientsSchema)
def patients(request):
    logger.info(f"Fetching patients for user {request.auth.user.id}")

    patients = Patient.objects.filter(users=request.auth.user)

    for patient in patients:
        user_patient_key = UserPatientKey.objects.get(
            user=request.auth.user,
            patient=patient
        ).key

        user_patient_key = base64.urlsafe_b64decode(user_patient_key.encode('utf-8'))
        patient_key = Fernet(request.auth.key).decrypt(user_patient_key)

        f = Fernet(patient_key)

        encrypted_name = base64.urlsafe_b64decode(patient.name.encode('utf-8'))
        decrypted_name = f.decrypt(encrypted_name).decode('utf-8')
        patient.name = decrypted_name

        encrypted_birth_date = base64.urlsafe_b64decode(patient.birth_date.encode('utf-8'))
        decrypted_birth_date = f.decrypt(encrypted_birth_date).decode('utf-8')
        patient.birth_date = date.fromisoformat(decrypted_birth_date)

    return {"patients": patients}


class NewPatientSchema(Schema):
    name: str
    birth_date: date

@api.post("/patients", auth=AuthBearer(), response=PatientSchema)
def add_patient(request, data: NewPatientSchema):
    patient_key = Fernet.generate_key()
    f = Fernet(patient_key)

    encrypted_name = f.encrypt(data.name.encode('utf-8'))
    encrypted_name = base64.urlsafe_b64encode(encrypted_name).decode('utf-8')

    encrypted_birth_date = f.encrypt(data.birth_date.isoformat().encode('utf-8'))
    encrypted_birth_date = base64.urlsafe_b64encode(encrypted_birth_date).decode('utf-8')

    patient = Patient.objects.create(
        name=encrypted_name,
        birth_date=encrypted_birth_date
    )

    user_patient_key = Fernet(request.auth.key).encrypt(patient_key)
    user_patient_key = base64.urlsafe_b64encode(user_patient_key).decode('utf-8')

    UserPatientKey.objects.create(
        user=request.auth.user,
        patient=patient,
        key=user_patient_key
    )

    return {
        "id": patient.id,
        "name": data.name,
        "birth_date": data.birth_date
    }