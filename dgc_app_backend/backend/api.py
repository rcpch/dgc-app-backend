import os
import logging
import uuid

from datetime import date
from uuid import UUID

from django.conf import settings

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
from .auth import AuthBearer

logger = logging.getLogger(__name__)


api = NinjaAPI()

@api.get("/hello", auth=AuthBearer())
def hello(request):
    return request.auth.name


class OrganisationUser(Schema):
    name: str
    email: str

class OrganisationSchema(Schema):
    id: UUID
    name: str | None = None
    users: list[OrganisationUser]

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

        users: list[OrganisationUser] = []
        for reg in all_registrations_for_this_organisation:
            users.append(OrganisationUser(
                name=decrypt_str(organisation_key_f, reg.encrypted_user_name),
                email=decrypt_str(organisation_key_f, reg.encrypted_user_email)
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

    encrypyed_user_name = encrypt_str(organisation_f, request.auth.name)
    encrypted_user_email = encrypt_str(organisation_f, request.auth.email)

    UserOrganisation.objects.create(
        user=request.auth.user,
        organisation=organisation,
        encrypted_organisation_key=encrypted_organisation_key,
        encrypted_user_name=encrypyed_user_name,
        encrypted_user_email=encrypted_user_email
    )

    return OrganisationSchema(
        id=organisation.id,
        name=data.name if data.name else None,
        users=[OrganisationUser(
            name=request.auth.name,
            email=request.auth.email
        )]
    )


class PatientUserSchema(Schema):
    name: str
    email: str

class PatientSchema(Schema):
    id: UUID
    name: str
    date_of_birth: date

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

    ret: list[PatientSchema] = []

    for patient in registration.organisation.patient_set.all():
        patient_name = decrypt_str(organisation_key_f, patient.encrypted_name)

        patient_dob_str = decrypt_str(organisation_key_f, patient.encrypted_date_of_birth)
        patient_dob = date.fromisoformat(patient_dob_str)

        ret.append(PatientSchema(
            id=patient.id,
            name=patient_name,
            date_of_birth=patient_dob
        ))

    return {"patients": ret}


# class NewPatientSchema(Schema):
#     name: str
#     date_of_birth: date

# @api.post("/patients", auth=AuthBearer(), response=PatientSchema)
# def add_patient(request, data: NewPatientSchema):
#     patient_key = Fernet.generate_key()
#     patient_f = Fernet(patient_key)

#     encrypted_name = encrypt_str(patient_f, data.name)
#     encrypted_date_of_birth = encrypt_str(patient_f, data.date_of_birth.isoformat())

#     patient = Patient.objects.create(
#         encrypted_name=encrypted_name,
#         encrypted_date_of_birth=encrypted_date_of_birth
#     )

#     encrypted_patient_key = encrypt_bytes(request.auth.key, patient_key)
#     encrypted_user_name = encrypt_str(patient_f, request.auth.name)
#     encrypted_user_email = encrypt_str(patient_f, request.auth.email)

#     UserPatient.objects.create(
#         user=request.auth.user,
#         patient=patient,
#         encrypted_patient_key=encrypted_patient_key,
#         encrypted_user_name=encrypted_user_name,
#         encrypted_user_email=encrypted_user_email
#     )

#     ret = PatientSchema.from_encrypted_patient(patient, patient_f)
#     return ret


# class UpdatePatientSchema(Schema):
#     name: str | None = None
#     date_of_birth: date | None = None

# @api.patch("/patients/{patient_id}", auth=AuthBearer(), response={200: PatientSchema, 404: None})
# def update_patient(request, patient_id: str, data: UpdatePatientSchema):
#     try:
#         patient = Patient.objects.get(id=patient_id)
#     except Patient.DoesNotExist:
#         return 404, None

#     user_patient = UserPatient.objects.get(
#         user=request.auth.user,
#         patient=patient
#     )

#     (_, patient_key) = user_patient.decrypt_patient_key(request.auth.key)

#     if data.name is not None:
#         patient.encrypted_name = encrypt_str(patient_key, data.name)

#     if data.date_of_birth is not None:
#         patient.encrypted_date_of_birth = encrypt_str(patient_key, data.date_of_birth.isoformat())

#     patient.save()

#     ret = PatientSchema.from_encrypted_patient(patient, patient_key)

#     return 200, ret

# @api.delete("/patients/{patient_id}", auth=AuthBearer(), response={204: None, 404: None})
# def delete_patient(request, patient_id: str):
#     try:
#         patient = Patient.objects.get(id=patient_id)
#     except Patient.DoesNotExist:
#         return 404, None

#     # Shouldn't be able to delete just by knowing the ID
#     try:
#         UserPatient.objects.get(
#             user=request.auth.user,
#             patient=patient
#         )
#     except:
#         return 404, None

#     patient.delete()
#     return 204, None


# class SharePatientSchema(Schema):
#     token: str

# @api.post("/patients/{patient_id}/share", auth=AuthBearer(), response={200: SharePatientSchema, 404: None})
# def share_patient(request, patient_id: str):
#     try:
#         patient = Patient.objects.get(id=patient_id)
#     except Patient.DoesNotExist:
#         return 404, None

#     # Shouldn't be able to share just by knowing the ID
#     try:
#         user_patient = UserPatient.objects.get(
#             user=request.auth.user,
#             patient=patient
#         )
#     except:
#         return 404, None

#     (patient_key, patient_key_f) = user_patient.decrypt_patient_key(request.auth.key)

#     decrypted_patient = PatientSchema.from_encrypted_patient(patient, patient_key_f)

#     password = str(uuid.uuid4())

#     salt = os.urandom(32).hex()
#     iterations = 100000

#     share_key = derive_key(password, salt, iterations)

#     encrypted_patient_key = encrypt_bytes(share_key, patient_key)
#     encrypted_sharer_name = encrypt_str(share_key, request.auth.name)
#     encrypted_patient_name = encrypt_str(share_key, decrypted_patient.name)

#     share_record = SharePatient.objects.create(
#         salt=salt,
#         iterations=iterations,
#         encrypted_patient_key=encrypted_patient_key,
#         encrypted_sharer_name=encrypted_sharer_name,
#         encrypted_patient_name=encrypted_patient_name,
#         patient=patient
#     )

#     return {
#         "token": f"{share_record.id}.{password}"
#     }


# class ShareTokenDetails(Schema):
#     sharer_name: str
#     patient_name: str

# @api.post("/share-token-details", auth=AuthBearer(), response={200: ShareTokenDetails, 401: None})
# def share_token_details(request, data: SharePatientSchema):
#     share_id = data.token.split('.')[0]
#     password = data.token.split('.')[1]

#     try:
#         share_record = SharePatient.objects.get(id=share_id)
#     except SharePatient.DoesNotExist:
#         return 401, None

#     share_key = derive_key(password, share_record.salt, share_record.iterations)

#     sharer_name = decrypt_str(share_key, share_record.encrypted_sharer_name)
#     patient_name = decrypt_str(share_key, share_record.encrypted_patient_name)

#     return 200, {
#         "sharer_name": sharer_name,
#         "patient_name": patient_name
#     }


# @api.post("/use-share-token", auth=AuthBearer(), response={200: PatientSchema, 401: None})
# def get_patient_from_share(request, data: SharePatientSchema):
#     share_id = data.token.split('.')[0]
#     password = data.token.split('.')[1]

#     try:
#         share_record = SharePatient.objects.get(id=share_id)
#     except SharePatient.DoesNotExist:
#         return 401, None

#     share_key = derive_key(password, share_record.salt, share_record.iterations)
#     (patient_key, patient_key_f) = share_record.decrypt_patient_key(share_key)

#     # Find the patient
#     try:
#         patient = Patient.objects.get(id=share_record.patient.id)
#     except Patient.DoesNotExist:
#         return 401, None

#     # Check we have the right patient key (throws if key invalid)
#     decrypt_str(patient_key_f, patient.encrypted_name)

#     # Re-encrypt the patient key for this user
#     encrypted_patient_key = encrypt_bytes(request.auth.key, patient_key)

#     encrypted_user_name = encrypt_str(patient_key_f, request.auth.name)
#     encrypted_user_email = encrypt_str(patient_key_f, request.auth.email)

#     UserPatient.objects.create(
#         user=request.auth.user,
#         patient=patient,
#         encrypted_patient_key=encrypted_patient_key,
#         encrypted_user_name=encrypted_user_name,
#         encrypted_user_email=encrypted_user_email
#     )

#     share_record.delete()

#     ret = PatientSchema.from_encrypted_patient(patient, patient_key_f)

#     return 200, ret 