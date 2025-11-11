from django.urls import path
from .views import *

urlpatterns = [
    path('authorize/', authorization_endpoint, name='authorization_endpoint'),
    path('keys/', jwks_uri, name='jwks_uri'),
    path('token/', token_endpoint, name='token_endpoint'),
    path('userinfo/', userinfo_endpoint, name='userinfo_endpoint'),
    path('logout', end_session_endpoint, name='end_session_endpoint'),
    path('.well-known/openid-configuration', well_known_configuration, name='well_known_configuration'),
]