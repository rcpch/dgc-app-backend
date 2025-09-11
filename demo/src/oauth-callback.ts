import * as client from 'openid-client';

const config = await client.discovery(
  new URL(import.meta.env.VITE_DEMO_OAUTH_SERVER),
  import.meta.env.VITE_DEMO_OAUTH_CLIENT_ID
);

const pkceCodeVerifier = sessionStorage['code_verifier'];
const expectedState = sessionStorage['state'];

const tokens = await client.authorizationCodeGrant(
    config,
    new URL(window.location.href),
    {
        pkceCodeVerifier,
        expectedState
    }
);

delete sessionStorage['code_verifier'];
delete sessionStorage['state'];

localStorage['access_token'] = tokens.access_token;

window.location.href = '/demo/';