import json
import logging

from functools import cache

from django.http import HttpResponse
from django.urls import reverse
from django.conf import settings

from Cryptodome.PublicKey import RSA
from jwkest.jwk import RSAKey
from pyop.provider import Provider
from pyop.authz_state import AuthorizationState
from pyop.subject_identifier import HashBasedSubjectIdentifierFactory
from pyop.userinfo import Userinfo


logger = logging.getLogger(__name__)


# Handle circular dependency with views
@cache
def get_provider():
    signing_key = RSAKey(key=RSA.generate(2048), alg="RS256")

    issuer = f"https://{settings.SITE_DOMAIN}"

    return Provider(
        signing_key=signing_key,
        configuration_information={
            "issuer": issuer,
            'authorization_endpoint': f"{issuer}{reverse(authorization_endpoint)}",
            'jwks_uri': f"{issuer}{reverse(jwks_uri)}",
            'token_endpoint': f"{issuer}{reverse(token_endpoint)}",
            'userinfo_endpoint': f"{issuer}{reverse(userinfo_endpoint)}",
            'end_session_endpoint': f"{issuer}{reverse(end_session_endpoint)}",
            'scopes_supported': ['openid', 'profile'],
            'response_types_supported': ['code', 'code id_token', 'code token', 'code id_token token'],  # code and hybrid
            'response_modes_supported': ['query', 'fragment'],
            'grant_types_supported': ['authorization_code', 'implicit'],
            'subject_types_supported': ['pairwise'],
            'token_endpoint_auth_methods_supported': ['client_secret_basic'],
            'claims_parameter_supported': True
        },
        authz_state=AuthorizationState(
            HashBasedSubjectIdentifierFactory("todo salt")
        ),
        clients={},
        userinfo=Userinfo(db={})
    )

def authorization_endpoint(request):
    response = get_provider().authorization_endpoint(request)
    return HttpResponse(response['response'], status=response['status'], content_type='application/json')

def jwks_uri(request):
    response = get_provider().jwks_uri(request)
    return HttpResponse(response['response'], status=response['status'], content_type='application/json')

def token_endpoint(request):
    response = get_provider().token_endpoint(request)
    return HttpResponse(response['response'], status=response['status'], content_type='application/json')

def userinfo_endpoint(request):
    response = get_provider().userinfo_endpoint(request)
    return HttpResponse(response['response'], status=response['status'], content_type='application/json')

def end_session_endpoint(request):
    response = get_provider().end_session_endpoint(request)
    return HttpResponse(response['response'], status=response['status'], content_type='application/json')

def well_known_configuration(request):
    logger.info(get_provider().provider_configuration.to_dict())
    response = json.dumps(get_provider().provider_configuration.to_dict())
    return HttpResponse(response, status=200, content_type='application/json')