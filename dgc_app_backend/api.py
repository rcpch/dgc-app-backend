import os

import logging
import hashlib

import httpx
import jwt

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from django.conf import settings

from ninja import NinjaAPI, Schema
from ninja.security import HttpBearer

from .backend.models import UserRegistration, Patient

logger = logging.getLogger(__name__)

@dataclass
class AuthData:
    user: UserRegistration
    name: str

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

            key = hashlib.pbkdf2_hmac(
                'sha256',
                user.id.encode('utf-8'),
                user.salt.encode('utf-8'),
                user.iterations
            ).hex()

            logger.info(key)

            name = claims["name"]

            return AuthData(user, name=name)

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

    return {"patients": patients}


class NewPatientSchema(Schema):
    name: str
    birth_date: date

@api.post("/patients", auth=AuthBearer(), response=PatientSchema)
def add_patient(request, data: NewPatientSchema):
    logger.info(f"Adding patient for user {request.auth.user.id}: {data.name}, {data.birth_date}")

    patient = Patient.objects.create(
        name=data.name,
        birth_date=data.birth_date
    )

    patient.users.add(request.auth.user)

    return patient