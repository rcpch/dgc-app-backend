import logging

import httpx
import jwt

from django.conf import settings

from ninja import NinjaAPI
from ninja.security import HttpBearer

logger = logging.getLogger(__name__)

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

        logger.info(claims)

        if token:
            return token

api = NinjaAPI()

@api.get("/hello", auth=AuthBearer())
def hello(request):
    return request.auth