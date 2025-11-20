import os
import logging
import uuid
import jwt

from datetime import date
from uuid import UUID
from typing import Tuple

from django.conf import settings
from django.urls import reverse

from ninja import NinjaAPI, Schema
from ninja.security import HttpBearer
from cryptography.fernet import Fernet

from .models import (
    User,
    Organisation,
    UserOrganisation,
    Patient,
    OrganisationInvite
)
from .crypto import (
    derive_key,
    decrypt_str,
    encrypt_bytes,
    encrypt_str,
    decrypt_bytes
)
from .auth import (
    AuthBearer,
    AuthData,
    login_with_third_party_id_token,
    login_with_third_party_access_token,
    generate_access_token
)

logger = logging.getLogger(__name__)


api = NinjaAPI()


@api.exception_handler(jwt.ExpiredSignatureError)
def on_expired_access_token(request, exc):
    response = {
        "code": "token_expired"
    }
    return api.create_response(request, response, status=401)


class TokenRequestSchema(Schema):
    oauth_server: str
    id_token: str | None = None
    access_token: str | None = None

class TokenResponseSchema(Schema):
    access_token: str
    name: str | None = None
    email: str | None = None

@api.post("/token", response={200: TokenResponseSchema, 404: None})
def token(request, data: TokenRequestSchema):
    if data.access_token:
        auth_data = login_with_third_party_access_token(data.oauth_server, data.access_token)
    elif data.id_token:
        auth_data = login_with_third_party_id_token(data.oauth_server, data.id_token)
    else:
        return 400, {"detail": "Either id_token or access_token must be provided."}
    
    email = auth_data.email
    name = auth_data.name

    return 200, TokenResponseSchema(
        access_token=generate_access_token(auth_data.sub),
        name=auth_data.name,
        email=auth_data.email
    )


@api.get("/hello", auth=AuthBearer())
def hello(request):
    return request.auth.name


class OrganisationUserSchema(Schema):
    id: str
    name: str
    email: str
    is_current_user: bool

class OrganisationSchema(Schema):
    id: UUID
    name: str | None = None
    users: list[OrganisationUserSchema]

class OrganisationsSchema(Schema):
    organisations: list[OrganisationSchema]

@api.get("/organisations", auth=AuthBearer(), response=OrganisationsSchema)
def organisations(request):
    ret: list[OrganisationSchema] = []
    
    my_organisation_registrations = UserOrganisation.objects.filter(user=request.auth.user)
    
    for registration in my_organisation_registrations:
        organisation = registration.organisation
        (_, organisation_key_f) = registration.decrypt_organisation_key(request.auth.key)

        encrypted_organisation_name = organisation.encrypted_name
        organisation_name = decrypt_str(organisation_key_f, encrypted_organisation_name) if encrypted_organisation_name else None

        all_registrations_for_this_organisation = UserOrganisation.objects.filter(organisation=organisation)

        users: list[OrganisationUserSchema] = []
        for reg in all_registrations_for_this_organisation:
            users.append(OrganisationUserSchema(
                id=reg.user.id,
                name=decrypt_str(organisation_key_f, reg.encrypted_user_name),
                email=decrypt_str(organisation_key_f, reg.encrypted_user_email),
                is_current_user=(reg.user == request.auth.user)
            ))
        
        ret.append(OrganisationSchema(
            id=organisation.id,
            name=organisation_name,
            users=users
        ))

    return OrganisationsSchema(organisations=ret)


class CreateOrganisationSchema(Schema):
    name: str | None = None

@api.post("/organisations", auth=AuthBearer(), response=OrganisationSchema)
def add_organisation(request, data: CreateOrganisationSchema):
    organisation_key = Fernet.generate_key()
    organisation_f = Fernet(organisation_key)

    encrypted_name = encrypt_str(organisation_f, data.name) if data.name else None

    organisation = Organisation.objects.create(
        encrypted_name=encrypted_name
    )

    encrypted_organisation_key = encrypt_bytes(request.auth.key, organisation_key)

    # TODO MRB: what should we do if these change the next time a user logs in?
    encrypted_user_name = encrypt_str(organisation_f, request.auth.name)
    encrypted_user_email = encrypt_str(organisation_f, request.auth.email)

    UserOrganisation.objects.create(
        user=request.auth.user,
        organisation=organisation,
        encrypted_organisation_key=encrypted_organisation_key,
        encrypted_user_name=encrypted_user_name,
        encrypted_user_email=encrypted_user_email
    )

    return OrganisationSchema(
        id=organisation.id,
        name=data.name if data.name else None,
        users=[OrganisationUserSchema(
            id=request.auth.user.id,
            name=request.auth.name,
            email=request.auth.email,
            is_current_user=True
        )]
    )

def get_organisation_or_404(auth: AuthData, organisation_id: str) -> Tuple[Organisation, Fernet] | Tuple[404, None]:
    try:
        registration = UserOrganisation.objects.get(
            user=auth.user,
            organisation__id=organisation_id
        )

        (organisation_key, organisation_key_f) = registration.decrypt_organisation_key(auth.key)

        return (registration.organisation, organisation_key, organisation_key_f)
    except UserOrganisation.DoesNotExist:
        return 404, None

# TODO MRB: shouldn't be able to remove the creator of an org?
@api.delete("/organisations/{organisation_id}/users/{user_id}", auth=AuthBearer(), response={204: None, 404: None})
def remove_user_from_organisation(request, organisation_id: str, user_id: str):
    (organisation, _, _) = get_organisation_or_404(request.auth, organisation_id)

    try:
        user_organisation = UserOrganisation.objects.get(
            user__id=user_id,
            organisation=organisation
        )
    except UserOrganisation.DoesNotExist:
        return 404, None

    user_organisation.delete()

    return 204, None


class PatientUserSchema(Schema):
    name: str
    email: str

class PatientSchema(Schema):
    id: UUID
    name: str
    date_of_birth: date

    @classmethod
    def from_encrypted_patient(cls, patient: Patient, organisation_key_f: Fernet) -> "PatientSchema":
        patient_name = decrypt_str(organisation_key_f, patient.encrypted_name)

        patient_dob_str = decrypt_str(organisation_key_f, patient.encrypted_date_of_birth)
        patient_dob = date.fromisoformat(patient_dob_str)

        return cls(
            id=patient.id,
            name=patient_name,
            date_of_birth=patient_dob
        )

class PatientsSchema(Schema):
    patients: list[PatientSchema]

@api.get("/organisations/{organisation_id}/patients", auth=AuthBearer(), response={200: PatientsSchema, 404: None})
def patients(request, organisation_id: str):
    try:
        registration = UserOrganisation.objects.get(
            user=request.auth.user,
            organisation__id=organisation_id
        )
    except UserOrganisation.DoesNotExist:
        return 404, None

    (_, organisation_key_f) = registration.decrypt_organisation_key(request.auth.key)

    patients = [PatientSchema.from_encrypted_patient(p, organisation_key_f) for p in registration.organisation.patient_set.all()]

    return {"patients": patients}


class NewPatientSchema(Schema):
    name: str
    date_of_birth: date

@api.post("/organisations/{organisation_id}/patients", auth=AuthBearer(), response={200: PatientSchema, 404: None})
def add_patient(request, organisation_id: str, data: NewPatientSchema):
    (organisation, _, organisation_key_f) = get_organisation_or_404(request.auth, organisation_id)

    encrypted_name = encrypt_str(organisation_key_f, data.name)
    encrypted_date_of_birth = encrypt_str(organisation_key_f, data.date_of_birth.isoformat())

    patient = Patient.objects.create(
        encrypted_name=encrypted_name,
        encrypted_date_of_birth=encrypted_date_of_birth,
        organisation=organisation
    )

    return PatientSchema.from_encrypted_patient(patient, organisation_key_f)


class UpdatePatientSchema(Schema):
    name: str | None = None
    date_of_birth: date | None = None

@api.patch("/organisations/{organisation_id}/patients/{patient_id}", auth=AuthBearer(), response={200: PatientSchema, 404: None})
def update_patient(request, organisation_id: str, patient_id: str, data: UpdatePatientSchema):
    (organisation, _, organisation_key_f) = get_organisation_or_404(request.auth, organisation_id)

    try:
        patient = Patient.objects.get(
            id=patient_id,
            organisation=organisation
        )
    except Patient.DoesNotExist:
        return 404, None

    if data.name is not None:
        patient.encrypted_name = encrypt_str(organisation_key_f, data.name)

    if data.date_of_birth is not None:
        patient.encrypted_date_of_birth = encrypt_str(organisation_key_f, data.date_of_birth.isoformat())

    patient.save()

    ret = PatientSchema.from_encrypted_patient(patient, organisation_key_f)

    return 200, ret

@api.delete("/organisations/{organisation_id}/patients/{patient_id}", auth=AuthBearer(), response={204: None, 404: None})
def delete_patient(request, organisation_id: str, patient_id: str):
    (organisation, _, _) = get_organisation_or_404(request.auth, organisation_id)

    # Shouldn't be able to delete just by knowing the ID
    try:
        patient = Patient.objects.get(
            id=patient_id,
            organisation=organisation
        )
    except Patient.DoesNotExist:
        return 404, None

    patient.delete()
    return 204, None


class InviteCreateSchema(Schema):
    invite_id: UUID
    token: str

@api.post("/organisations/{organisation_id}/share", auth=AuthBearer(), response={200: InviteCreateSchema, 404: None})
def create_invite(request, organisation_id: str):
    # Shouldn't be able to share just by knowing the ID
    (organisation, organisation_key, organisation_key_f) = get_organisation_or_404(request.auth, organisation_id)

    password = str(uuid.uuid4())

    salt = os.urandom(32).hex()
    iterations = 100000

    share_key = derive_key(password, salt, iterations)

    encrypted_organisation_key = encrypt_bytes(share_key, organisation_key)

    invite = OrganisationInvite.objects.create(
        salt=salt,
        iterations=iterations,
        encrypted_organisation_key=encrypted_organisation_key,
        organisation=organisation
    )

    return {
        "invite_id": invite.id,
        "token": password
    }


class OrganisationInviteDetailsRequestSchema(Schema):
    token: str 

class OrganisationInviteDetailsUserSchema(Schema):
    name: str

class OrganisationInviteDetailsSchema(Schema):
    organisation_id: UUID
    organisation_name: str | None = None
    patient_count: int
    users: list[OrganisationInviteDetailsUserSchema]

@api.post("/invites/{invite_id}/details", auth=AuthBearer(), response={200: OrganisationInviteDetailsSchema, 401: None})
def organisation_invite_details(request, invite_id: str, data: OrganisationInviteDetailsRequestSchema):
    try:
        invite = OrganisationInvite.objects.get(id=invite_id)
    except OrganisationInvite.DoesNotExist:
        return 401, None

    organisation_key = derive_key(data.token, invite.salt, invite.iterations)

    organisation = invite.organisation
    organisation_name = decrypt_str(Fernet(organisation_key), organisation.encrypted_name) if organisation.encrypted_name else None

    patient_count = organisation.patient_set.count()

    return 200, OrganisationInviteDetailsSchema(
        organisation_id=organisation.id,
        organisation_name=organisation_name,
        patient_count=patient_count,
        users=[]
    )


@api.post("/invites/{invite_id}/redeem", auth=AuthBearer(), response={204: None, 401: None})
def get_patient_from_share(request, invite_id: str, data: OrganisationInviteDetailsRequestSchema):
    try:
        invite = OrganisationInvite.objects.get(id=invite_id)
    except OrganisationInvite.DoesNotExist:
        return 401, None

    share_key = derive_key(data.token, invite.salt, invite.iterations)
    (organisation_key, organisation_key_f) = invite.decrypt_organisation_key(share_key)

    organisation = invite.organisation

    # Check we have the right organisation key (throws if key invalid)
    decrypt_str(organisation_key_f, organisation.encrypted_name) if organisation.encrypted_name else None

    # Re-encrypt the organisation key for this user
    encrypted_organisation_key = encrypt_bytes(request.auth.key, organisation_key)

    encrypted_user_name = encrypt_str(organisation_key_f, request.auth.name)
    encrypted_user_email = encrypt_str(organisation_key_f, request.auth.email)

    UserOrganisation.objects.create(
        user=request.auth.user,
        organisation=organisation,
        encrypted_organisation_key=encrypted_organisation_key,
        encrypted_user_name=encrypted_user_name,
        encrypted_user_email=encrypted_user_email
    )

    invite.delete()

    return 204, None
