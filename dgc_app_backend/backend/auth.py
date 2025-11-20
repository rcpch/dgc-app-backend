import jwt
import httpx
import datetime

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

def generate_access_token(sub: str, name: str, email: str) -> str:
  return jwt.encode({
    "iss": settings.SESSION_JWT_ISSUER,
    "aud": settings.SESSION_JWT_AUDIENCE,
    "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.SESSION_JWT_EXPIRY_SECONDS),
    "sub": sub,
    "name": name,
    "email": email
  }, settings.SECRET_KEY, algorithm="HS256")

class AuthBearer(HttpBearer):
  def authenticate(self, request, token: str | None) -> AuthData | None:
    if not token:
      return None
    
    claims = jwt.decode(
      token,
      settings.SECRET_KEY,
      algorithms=["HS256"],
      audience=settings.SESSION_JWT_AUDIENCE,
      issuer=settings.SESSION_JWT_ISSUER,
      strict_aud=True
    )

    # TODO MRB: hash at exchange time?
    user_id = sha_256(claims["sub"])

    (user, _) = User.objects.get_or_create(
        id=user_id,
        defaults={
          "salt": salt()
        }
    )

    key = derive_key(claims["sub"], user.salt, user.iterations)

    name = claims["name"]
    email = claims["email"]

    return AuthData(user, name, email, key)