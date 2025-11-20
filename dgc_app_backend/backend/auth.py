import jwt
import httpx
import datetime
import logging

from dataclasses import dataclass

from django.conf import settings
from ninja.security import HttpBearer

from .models import User
from .crypto import sha_256, derive_key, salt, encrypt_str, decrypt_str


logger = logging.getLogger(__name__)


@dataclass
class AuthData:
  sub: str
  user: User
  name: str
  email: str
  key: bytes


def login_with_third_party_id_token(token: str) -> AuthData:
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

  # Extremely important! Don't store the actual user ID in the database as we treat it as a secret
  # to derive the per user encryption key
  user_id = sha_256(claims["sub"])

  key_salt = salt()
  iterations = 100000

  key = derive_key(claims["sub"], key_salt, iterations=iterations)

  (user, _) = User.objects.get_or_create(
      id=user_id,
      defaults={
        "salt": key_salt,
        "iterations": iterations,
        "encrypted_name": encrypt_str(key, claims["name"]),
        "encrypted_email": encrypt_str(key, claims["email"]), 
      }
  )

  # User might have already existed, update key
  key = derive_key(claims["sub"], user.salt, user.iterations)
  
  # TODO MRB: update name and email if they've changed?

  return AuthData(
    sub=claims["sub"],
    user=user,
    name=claims["name"],
    email=claims["email"],
    key=key
  )


def login_with_third_party_access_token(token: str) -> dict:
  url = f"{settings.DEMO_OAUTH_SERVER}/.well-known/openid-configuration"
  oidc_doc = httpx.get(url).json()

  userinfo_endpoint = oidc_doc["userinfo_endpoint"]
  response = httpx.get(
      userinfo_endpoint,
      headers={"Authorization": f"Bearer {token}"}
  )

  ret = response.json()
  
  sub = ret["sub"]
  user_id = sha_256(sub)

  user = User.objects.get(id=user_id)

  key = derive_key(sub, user.salt, user.iterations)

  name = decrypt_str(key, user.encrypted_name)
  email = decrypt_str(key, user.encrypted_email)

  return AuthData(
    sub=sub,
    user=user,
    name=name,
    email=email,
    key=key
  )

def generate_access_token(sub: str) -> str:
  return jwt.encode({
    "iss": settings.SESSION_JWT_ISSUER,
    "aud": settings.SESSION_JWT_AUDIENCE,
    "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.SESSION_JWT_EXPIRY_SECONDS),
    "sub": sub
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

    user_id = sha_256(claims["sub"])

    user = User.objects.get(id=user_id)

    key = derive_key(claims["sub"], user.salt, user.iterations)

    name = decrypt_str(key, user.encrypted_name)
    email = decrypt_str(key, user.encrypted_email)

    return AuthData(
      sub=claims["sub"],
      user=user,
      name=name,
      email=email,
      key=key
    )