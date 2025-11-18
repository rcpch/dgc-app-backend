import json
import logging

from functools import cache
from urllib.parse import urlencode

from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from Cryptodome.PublicKey import RSA
from jwkest.jwk import RSAKey
from pyop.provider import Provider
from pyop.authz_state import AuthorizationState
from pyop.subject_identifier import HashBasedSubjectIdentifierFactory
from pyop.userinfo import Userinfo
from pyop.exceptions import InvalidAuthenticationRequest, InvalidClientAuthentication, OAuthError
from pyop.util import should_fragment_encode
from oic.oic.message import TokenErrorResponse


logger = logging.getLogger(__name__)


username = "test"
user_email = "test@rcpch.tech"

# Handle circular dependency with views
@cache
def get_provider():
    signing_key = RSAKey(key=RSA.generate(2048), alg="RS256")

    base = f"https://{settings.SITE_DOMAIN}"

    clients = {}
    clients[settings.DEMO_OAUTH_CLIENT_ID] = {
        "redirect_uris": [f"https://{settings.SITE_DOMAIN}/demo/oauth-callback"],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_post"
    }

    users = {}
    users[username] = {
        "email": user_email
    }

    return Provider(
        signing_key=signing_key,
        configuration_information={
            "issuer": f"{base}/test-oidc",
            'authorization_endpoint': f"{base}{reverse(authorization_endpoint)}",
            'jwks_uri': f"{base}{reverse(jwks_uri)}",
            'token_endpoint': f"{base}{reverse(token_endpoint)}",
            'userinfo_endpoint': f"{base}{reverse(userinfo_endpoint)}",
            'end_session_endpoint': f"{base}{reverse(end_session_endpoint)}",
            'scopes_supported': ['openid', 'profile', 'email'],
            'response_types_supported': ['code', 'code id_token', 'code token', 'code id_token token'],  # code and hybrid
            'response_modes_supported': ['query', 'fragment'],
            'grant_types_supported': ['authorization_code', 'implicit'],
            'subject_types_supported': ['pairwise'],
            'token_endpoint_auth_methods_supported': ['client_secret_basic'],
            'claims_parameter_supported': True
        },
        authz_state=AuthorizationState(
            subject_identifier_factory=HashBasedSubjectIdentifierFactory("todo salt"),
            authorization_code_lifetime=10*60,
            access_token_lifetime=60*60,
            refresh_token_lifetime=24*60*60,
            refresh_token_threshold=60*60
        ),
        clients=clients,
        userinfo=Userinfo(db=users)
    )

def authorization_endpoint(request):
    provider = get_provider()

    try:
        auth_req = provider.parse_authentication_request(
            request_body=request.GET.urlencode()
        )
    except InvalidAuthenticationRequest as e:
        logger.warning(f"Invalid auth request", exc_info=True)

        error_url = e.to_error_url()
        if error_url:
            return redirect(error_url)
        
        return HttpResponse(str(e), status=400, content_type='application/json')

    authn_response = provider.authorize(auth_req, username)
    response_url = authn_response.request(auth_req['redirect_uri'], should_fragment_encode(auth_req))

    return redirect(response_url)

def jwks_uri(request):
    response = json.dumps(get_provider().jwks)
    return HttpResponse(response, status=200, content_type='application/json')

@csrf_exempt
def token_endpoint(request):
    try:
        token_response = get_provider().handle_token_request(
            request_body=request.body.decode('utf-8'),
            http_headers=request.headers
        )

        token_response = json.dumps(token_response.to_dict())

        return HttpResponse(token_response, status=200, content_type='application/json')
    except InvalidClientAuthentication as e:
        logger.warning('invalid client authentication at token endpoint', exc_info=True)

        error_resp = TokenErrorResponse(error='invalid_client', error_description=str(e))

        response = HttpResponse(error_resp.to_json(), status=401, content_type='application/json')
        response['WWW-Authenticate'] = 'Basic'

        return response
    except OAuthError as e:
        logger.warning('invalid request: %s', str(e), exc_info=True)

        error_resp = TokenErrorResponse(error=e.oauth_error, error_description=str(e))
        response = HttpResponse(error_resp.to_json(), status=400, content_type='application/json')

        return response

def userinfo_endpoint(request):
    response = get_provider().userinfo_endpoint(request)
    return HttpResponse(response['response'], status=response['status'], content_type='application/json')

def end_session_endpoint(request):
    response = get_provider().end_session_endpoint(request)
    return HttpResponse(response['response'], status=response['status'], content_type='application/json')

def well_known_configuration(request):
    response = json.dumps(get_provider().provider_configuration.to_dict())
    return HttpResponse(response, status=200, content_type='application/json')