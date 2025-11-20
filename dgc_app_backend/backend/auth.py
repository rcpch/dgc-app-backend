import jwt
import httpx

from dataclasses import dataclass

from django.conf import settings
from ninja.security import HttpBearer

from .models import User
from .crypto import sha_256, derive_key, salt

@dataclass
class AuthData:
    user: User
    name: str
    email: str
    key: bytes


def verify_third_party_jwt(token: str) -> dict:
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

    return claims


class AuthBearer(HttpBearer):
  def authenticate(self, request, token: str | None) -> AuthData | None:
    if not token:
      return None

    url = f"{settings.DEMO_OAUTH_SERVER}/.well-known/openid-configuration"
    oidc_doc = httpx.get(url).json()

    signing_algos = oidc_doc["id_token_signing_alg_values_supported"]

    jwks_client = jwt.PyJWKClient(oidc_doc["jwks_uri"])
    signing_key = jwks_client.get_signing_key_from_jwt(token)

    claims = verify_third_party_jwt(token)

    user_id = sha_256(claims["sub"])

    (user, _) = User.objects.get_or_create(
        id=user_id,
        defaults={
          "salt": salt()
        }
    )

    key = derive_key(claims["sub"], user.salt, user.iterations)

    name = claims["name"]
    email = claims["unique_name"]

    return AuthData(user, name, email, key)