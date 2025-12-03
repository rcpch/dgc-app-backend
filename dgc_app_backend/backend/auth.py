import jwt
import httpx
import datetime
import logging

from dataclasses import dataclass

from django.conf import settings
from ninja.security import HttpBearer

from .models import User, UserOrganisation, UserRegistration
from .crypto import sha_256, derive_key, salt, decrypt_str


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


def get_or_create_user(claims) -> AuthData:
  # Extremely important! Don't store the actual syub in the database as we treat it as a secret
  # to derive the per user encryption key
  hashed_sub = sha_256(claims["sub"])

  user_registration = UserRegistration.objects.filter(
    oauth_iss=claims["iss"],
    hashed_sub=hashed_sub
  ).select_related("user").first()

  if user_registration:
    user = user_registration.user
  else:
    user = User.objects.create()
    user_registration = UserRegistration.objects.create(
      oauth_iss=claims["iss"],
      hashed_sub=hashed_sub,
      salt=salt(),
      iterations=100000,
      user=user
    )
  
  key = derive_key(claims["sub"], user_registration.salt, user_registration.iterations)
  
  # TODO MRB: update name and email if they've changed?

  return AuthData(
    sub=claims["sub"],
    user=user,
    name=claims["name"],
    email=claims["email"],
    key=key
  )


def find_and_decrypt_user(sub: str) -> AuthData:
  hashed_sub = sha_256(sub)

  user_registration = UserRegistration.objects.filter(
    hashed_sub=hashed_sub
  ).select_related("user").first()

  user_organisation = UserOrganisation.objects.filter(
    user__id=user_registration.user.id
  ).select_related("user").first()

  user = user_organisation.user

  user_key_f = derive_key(sub, user_registration.salt, user_registration.iterations)
  _, organisation_key_f = user_organisation.decrypt_organisation_key(user_key_f)

  name = decrypt_str(organisation_key_f, user_organisation.encrypted_user_name)
  email = decrypt_str(organisation_key_f, user_organisation.encrypted_user_email)

  return AuthData(
    sub=sub,
    user=user,
    name=name,
    email=email,
    key=user_key_f
  )


def login_with_third_party_id_token(oauth_server: str, token: str) -> AuthData:
  config = fetch_config(oauth_server)

  url = f"{config.oauth_server}/.well-known/openid-configuration"
  oidc_doc = httpx.get(url).json()

  signing_algos = oidc_doc["id_token_signing_alg_values_supported"]

  jwks_client = jwt.PyJWKClient(oidc_doc["jwks_uri"])
  signing_key = jwks_client.get_signing_key_from_jwt(token)

  logger.info(config.allowed_client_ids)

  claims = jwt.decode(
      token,
      signing_key.key,
      algorithms=signing_algos,
      audience=config.allowed_client_ids,
      issuer=config.oauth_server
  )

  return get_or_create_user(claims)


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

  return find_and_decrypt_user(sub)



def generate_access_token(sub: str) -> str:
  return jwt.encode({
    "iss": settings.SESSION_JWT_ISSUER,
    "aud": settings.SESSION_JWT_AUDIENCE,
    "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=settings.SESSION_JWT_EXPIRY_SECONDS),
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
      options={
        "strict_aud": True
      }
    )

    logger.info(f"!! sub: {claims['sub']}:{type(claims['sub'])}")
    return find_and_decrypt_user(claims["sub"])