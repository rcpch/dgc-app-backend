import os
import logging
import uuid
import jwt
import json

from datetime import date
from uuid import UUID
from typing import Tuple, List, Union, Literal

from ninja import NinjaAPI, Schema
from cryptography.fernet import Fernet
from django.db import transaction
from django.db.models import Q
from django.contrib.postgres.aggregates import ArrayAgg
from django.shortcuts import get_object_or_404
from django.http import Http404

from .models import (
    Organisation,
    UserOrganisation,
    User,
    Child,
    ChildOrganisation,
    OrganisationInvite,
    Observation,
    DGCResult
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
from .organisations import (
    create_organisation,
)
from .dgc import (
    calculate_dgc_results_for_reference,
    recalculate_dgc_results
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

        if not UserOrganisation.objects.filter(user=auth_data.user).exists():
            create_organisation(auth_data, organisation_name=None)
    else:
        return 400, {"detail": "Either id_token or access_token must be provided."}

    return 200, TokenResponseSchema(
        access_token=generate_access_token(auth_data.sub),
        name=auth_data.name,
        email=auth_data.email
    )


@api.get("/hello", auth=AuthBearer())
def hello(request):
    return request.auth.name


def get_organisation_or_404(auth: AuthData, organisation_id: str) -> Tuple[Organisation, bytes, Fernet]:
    registration = get_object_or_404(UserOrganisation,
        user=auth.user,
        organisation__id=organisation_id
    )

    (organisation_key, organisation_key_f) = registration.decrypt_organisation_key(auth.key)

    return (registration.organisation, organisation_key, organisation_key_f)

def get_child_and_organisation_or_404(request, user: User, child_id: str) -> Tuple[Child, bytes, Fernet]:
    # User might have the same child via multiple organisations so we can't use get_object_or_404
    child_with_org = ChildOrganisation.objects.filter(
        child__id=child_id,
        organisation__userorganisation__user=user
    ).select_related("child", "organisation").first()

    if not child_with_org:
        raise Http404("Child not found or user does not have access")

    (organisation, _, organisation_key_f) = get_organisation_or_404(request.auth, child_with_org.organisation.id)

    child_key = decrypt_bytes(organisation_key_f, child_with_org.encrypted_child_key)
    child_key_f = Fernet(child_key)

    return (child_with_org.child, child_key, child_key_f)


class OrganisationUserSchema(Schema):
    id: str
    name: str
    email: str
    is_current_user: bool
    is_creator: bool

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
            username = decrypt_str(organisation_key_f, reg.encrypted_user_name)

            users.append(OrganisationUserSchema(
                id=str(reg.user.id),
                name=username,
                email=decrypt_str(organisation_key_f, reg.encrypted_user_email),
                is_current_user=(reg.user == request.auth.user),
                is_creator=reg.is_creator
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
    organisation = create_organisation(request.auth, data.name)

    return OrganisationSchema(
        id=organisation.id,
        name=data.name if data.name else request.auth.name,
        users=[OrganisationUserSchema(
            id=str(request.auth.user.id),
            name=request.auth.name,
            email=request.auth.email,
            is_current_user=True,
            is_creator=True
        )]
    )

# TODO MRB: shouldn't be able to remove the creator of an org?
@api.delete("/organisations/{organisation_id}/users/{user_id}", auth=AuthBearer(), response={204: None})
def remove_user_from_organisation(request, organisation_id: str, user_id: str):
    (organisation, _, _) = get_organisation_or_404(request.auth, organisation_id)

    user_organisation = get_object_or_404(UserOrganisation,
        user__id=user_id,
        organisation=organisation
    )

    user_organisation.delete()

    return 204, None

Sex = Union[
    Literal['male'],
    Literal['female']
]

ObservationType = Union[
    Literal['height'],
    Literal['weight'],
    Literal['ofc']
]

Reference = Union[
    Literal['uk-who'],
    Literal['turner'],
    Literal['trisomy-21'],
    Literal['trisomy-21-aap'],
    Literal['cdc'],
    Literal['who']
]

class ChildSchema(Schema):
    id: UUID
    name: str
    date_of_birth: date
    sex: Sex
    reference: Reference
    gestation_days: int | None = None

class ObservationSchema(Schema):
    observation_date: date
    observation_type: ObservationType
    observation_value: float

class ExpandedChild(ChildSchema):
    organisation_ids: list[UUID]

class ExpandedChildren(Schema):
    children: list[ExpandedChild]


@api.get("/children", auth=AuthBearer(), response=ExpandedChildren)
def children(request):
    qs = Child.objects.filter(
        childorganisation__organisation__userorganisation__user=request.auth.user
    ).annotate(
        organisation_ids=ArrayAgg('childorganisation__organisation_id'),
        encrypted_organisation_keys=ArrayAgg('childorganisation__organisation__userorganisation__encrypted_organisation_key'),
        encrypted_child_keys=ArrayAgg('childorganisation__encrypted_child_key')
    ).values(
        'id',
        'encrypted_name',
        'encrypted_date_of_birth',
        'sex',
        'gestation_days',
        'organisation_ids',
        'encrypted_organisation_keys',
        'encrypted_child_keys',
        'reference'
    )

    rows = []

    for row in qs:
        encrypted_organisation_key = row['encrypted_organisation_keys'][0]
        organisation_key = decrypt_bytes(request.auth.key, encrypted_organisation_key)
        organisation_key_f = Fernet(organisation_key)

        encrypted_child_key = row['encrypted_child_keys'][0]
        child_key = decrypt_bytes(organisation_key_f, encrypted_child_key)
        child_f = Fernet(child_key)

        name = decrypt_str(child_f, row['encrypted_name'])
        date_of_birth = date.fromisoformat(decrypt_str(child_f, row['encrypted_date_of_birth']))

        match row['sex']:
            case 0:
                sex = 'male'
            case 1:
                sex = 'female'
            case _:
                raise ValueError("Unknown sex code")

        rows.append(ExpandedChild(
            id=row['id'],
            name=name,
            date_of_birth=date_of_birth,
            sex=sex,
            gestation_days=row['gestation_days'],
            organisation_ids=row['organisation_ids'],
            reference=row['reference']
        ))

    return 200, ExpandedChildren(children=rows)


class NewChildSchema(Schema):
    name: str
    date_of_birth: date
    sex: Sex
    gestation_days: int | None = None

@api.post("/organisations/{organisation_id}/children", auth=AuthBearer(), response={200: ChildSchema})
def add_child(request, organisation_id: str, data: NewChildSchema):
    (organisation, _, organisation_key_f) = get_organisation_or_404(request.auth, organisation_id)

    child_key = Fernet.generate_key()
    child_f = Fernet(child_key)

    encrypted_name = encrypt_str(child_f, data.name)
    encrypted_date_of_birth = encrypt_str(child_f, data.date_of_birth.isoformat())

    match data.sex:
        case 'male':
            sex = 0
        case 'female':
            sex = 1

    child = Child.objects.create(
        encrypted_name=encrypted_name,
        encrypted_date_of_birth=encrypted_date_of_birth,
        sex = sex,
        gestation_days = data.gestation_days,
        reference = organisation.default_reference
    )

    ChildOrganisation.objects.create(
        encrypted_child_key=encrypt_bytes(organisation_key_f, child_key),
        child=child,
        organisation=organisation
    )

    return 200, ChildSchema(
        id=child.id,
        name=data.name,
        date_of_birth=data.date_of_birth,
        sex=data.sex,
        reference=child.reference,
        gestation_days=data.gestation_days,
    )


@api.put("/organisations/{organisation_id}/children/{child_id}", auth=AuthBearer(), response={201: None})
def add_existing_child_to_organisation(request, organisation_id: str, child_id: str):
    (target_organisation, _, target_organisation_key_f) = get_organisation_or_404(request.auth, organisation_id)

    child = get_object_or_404(Child, id=child_id)
    
    # Can't add child just by knowing the ID, must check we have access via an existing organisation
    existing_child_org = ChildOrganisation.objects.filter(
        child=child,
        organisation__pk__in=UserOrganisation.objects.filter(
            user=request.auth.user
        ).values("organisation__id")
    ).first()

    (existing_organisation, _, existing_organisation_key_f) = get_organisation_or_404(request.auth, existing_child_org.organisation.id)

    user_organisation = get_object_or_404(UserOrganisation,
        user=request.auth.user,
        organisation=target_organisation
    )
    
    child_key = decrypt_bytes(existing_organisation_key_f, existing_child_org.encrypted_child_key)
    
    ChildOrganisation.objects.create(
        encrypted_child_key=encrypt_bytes(target_organisation_key_f, child_key),
        child=child,
        organisation=target_organisation
    )

    return 201, None


class UpdateChildSchema(Schema):
    name: str | None = None
    date_of_birth: date | None = None
    sex: Sex | None = None
    gestation_days: int | None = None
    reference: Reference | None = None

@api.patch("/children/{child_id}", auth=AuthBearer(), response={200: ChildSchema})
def update_child(request, child_id: str, data: UpdateChildSchema):
    (child, _, child_f) = get_child_and_organisation_or_404(request, request.auth.user, child_id)

    # TODO MRB: recalculate DGC results and obs days since birth?
    recalculation_required = False

    if data.name is not None:
        child.encrypted_name = encrypt_str(child_f, data.name)

    if data.date_of_birth is not None:
        child.encrypted_date_of_birth = encrypt_str(child_f, data.date_of_birth.isoformat())
        recalculation_required = True

    if data.sex is not None:
        match data.sex:
            case 'male':
                child.sex = 0
            case 'female':
                child.sex = 1
        
        recalculation_required = True

    if data.gestation_days is not None:
        child.gestation_days = data.gestation_days
        recalculation_required = True
    
    if data.reference is not None:
        child.reference = data.reference
        # Recalculated on demand when viewing the chart

    with transaction.atomic():
        child.save()

        if recalculation_required:
            recalculate_dgc_results(
                date_of_birth=data.date_of_birth,
                child=child,
                child_f=child_f
            )

    match child.sex:
        case 0:
            sex = 'male'
        case 1:
            sex = 'female'
        case _:
            raise ValueError("Unknown sex code")

    return 200, ChildSchema(
        id=child.id,
        name=decrypt_str(child_f, child.encrypted_name),
        date_of_birth=date.fromisoformat(decrypt_str(child_f, child.encrypted_date_of_birth)),
        sex=sex,
        gestation_days=child.gestation_days,
        reference=child.reference
    )

@api.delete("/organisations/{organisation_id}/children/{child_id}", auth=AuthBearer(), response={204: None})
def delete_child(request, organisation_id: str, child_id: str):
    (organisation, _, _) = get_organisation_or_404(request.auth, organisation_id)

    with transaction.atomic():
        # Shouldn't be able to delete just by knowing the ID
        child_organisation = get_object_or_404(ChildOrganisation,
            child__id=child_id,
            organisation=organisation
        )

        child_organisation.delete()

        if not ChildOrganisation.objects.filter(child__id=child_id).exists():
            # No more orgs have this child, delete the child record too
            Child.objects.filter(id=child_id).delete()
    
        return 204, None

class ExpandedObservationSchema(ObservationSchema):
    dgc_api_result: dict

class Observations(Schema):
    observations: list[ExpandedObservationSchema]

@api.get("/children/{child_id}/observations/{reference}", auth=AuthBearer(), response=Observations)
def get_observations(request, child_id: str, reference: Reference):
    (child, _, child_f) = get_child_and_organisation_or_404(request, request.auth.user, child_id)

    observations = Observation.objects.filter(
        child=child,
    )

    dgc_results = DGCResult.objects.filter(
        observation__in=observations,
        reference=reference
    ).select_related('observation')

    ret = []

    if observations.count() != dgc_results.count():
        date_of_birth = date.fromisoformat(decrypt_str(child_f, child.encrypted_date_of_birth))

        with transaction.atomic():
            calculate_dgc_results_for_reference(
                date_of_birth=date_of_birth,
                sex=child.sex,
                child_f=child_f,
                reference=reference,
                observations=observations
            )
    
        # Reload! Reload!
        dgc_results = dgc_results.all()

    for result in dgc_results:
        observation = result.observation

        dgc_api_result_encrypted = result.encrypted_dgc_api_result
        dgc_api_result_json = decrypt_str(child_f, dgc_api_result_encrypted)
        dgc_api_result = json.loads(dgc_api_result_json)

        ret.append(ExpandedObservationSchema(
            observation_date=date.fromisoformat(decrypt_str(child_f, observation.encrypted_observation_date)),
            observation_type={
                1: 'height',
                2: 'weight',
                3: 'ofc'
            }[observation.observation_type],
            observation_value=observation.observation_value,
            dgc_api_result=dgc_api_result
        ))

    return 200, Observations(observations=ret)


@api.post("/children/{child_id}/observations", auth=AuthBearer(), response={201: None})
def add_observation(request, child_id: str, data: ObservationSchema):
    (child, _, child_f) = get_child_and_organisation_or_404(request, request.auth.user, child_id)

    match data.observation_type:
        case 'height':
            observation_type = 1
        case 'weight':
            observation_type = 2
        case 'ofc':
            observation_type = 3
        case _:
            return 400, {"detail": "Invalid observation type"}

    date_of_birth = date.fromisoformat(decrypt_str(child_f, child.encrypted_date_of_birth))

    encrypted_observation_date = encrypt_str(child_f, data.observation_date.isoformat())

    observation = Observation.objects.create(
        observation_type=observation_type,
        observation_value=data.observation_value,
        encrypted_observation_date=encrypted_observation_date,
        days_since_birth=(data.observation_date - date_of_birth).days,
        child=child
    )

    return 201, None


class InviteCreateSchema(Schema):
    invite_id: UUID
    token: str

@api.post("/organisations/{organisation_id}/share", auth=AuthBearer(), response={200: InviteCreateSchema})
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
    child_count: int
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

    child_count = ChildOrganisation.objects.filter(
        organisation=organisation
    ).count()

    return 200, OrganisationInviteDetailsSchema(
        organisation_id=organisation.id,
        organisation_name=organisation_name,
        child_count=child_count,
        users=[]
    )


@api.post("/invites/{invite_id}/redeem", auth=AuthBearer(), response={204: None, 401: None})
def redeem_share_invite(request, invite_id: str, data: OrganisationInviteDetailsRequestSchema):
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
        encrypted_user_email=encrypted_user_email,
        is_creator=False
    )

    invite.delete()

    return 204, None
