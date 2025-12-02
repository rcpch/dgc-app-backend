import jwt
import httpx
import datetime
import logging

from dataclasses import dataclass

from django.conf import settings
from ninja.security import HttpBearer

from .models import User, UserOrganisation
from .crypto import sha_256, derive_key, salt, encrypt_str, decrypt_str
from .organisations import create_organisation


logger = logging.getLogger(__name__)


@dataclass
class AuthConfig:
  oauth_server: str
  allowed_client_ids: list[str]

@dataclass
class AuthData:
  sub: str
  user: User
  name: str
  email: str
  key: bytes


def fetch_config(oauthServer: str) -> dict:
  match oauthServer:
    case settings.MICROSOFT_OAUTH_SERVER:
      return AuthConfig(
        oauth_server=settings.MICROSOFT_OAUTH_SERVER,
        allowed_client_ids=settings.MICROSOFT_OAUTH_ALLOWED_CLIENT_IDS
      )
    case settings.GOOGLE_OAUTH_SERVER:
      return AuthConfig(
        oauth_server=settings.GOOGLE_OAUTH_SERVER,
        allowed_client_ids=settings.GOOGLE_OAUTH_ALLOWED_CLIENT_IDS
      )
    case _:
      raise ValueError(f"Unknown OAuth server: {oauthServer}")


def create_user(claims) -> AuthData:
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

  if not UserOrganisation.objects.filter(user=user).exists():
    create_organisation(user, key, organisation_name=None)

  return AuthData(
    sub=claims["sub"],
    user=user,
    name=claims["name"],
    email=claims["email"],
    key=key
  )


def login_with_third_party_id_token(oauth_server: str, token: str) -> AuthData:
  config = fetch_config(oauth_server)

  url = f"{config.oauth_server}/.well-known/openid-configuration"
  oidc_doc = httpx.get(url).json()

  signing_algos = oidc_doc["id_token_signing_alg_values_supported"]

  jwks_client = jwt.PyJWKClient(oidc_doc["jwks_uri"])
  signing_key = jwks_client.get_signing_key_from_jwt(token)

  claims = jwt.decode(
      token,
      signing_key.key,
      algorithms=signing_algos,
      audience=config.allowed_client_ids,
      issuer=config.oauth_server,
      strict_aud=True
  )

  return create_user(claims)


def login_with_third_party_access_token(oauth_server: str, token: str) -> AuthData:
  config = fetch_config(oauth_server)

  url = f"{config.oauth_server}/.well-known/openid-configuration"
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