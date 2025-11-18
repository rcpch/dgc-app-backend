import { useEffect } from 'preact/hooks';
import * as client from 'openid-client';

async function oauthCallback() {
  const config = await client.discovery(
    new URL(import.meta.env.VITE_DEMO_OAUTH_SERVER),
    import.meta.env.VITE_DEMO_OAUTH_CLIENT_ID
  );

  const pkceCodeVerifier = sessionStorage['code_verifier'];
  const expectedState = sessionStorage['state'];
  const expectedNonce = sessionStorage['nonce'];

  const tokens = await client.authorizationCodeGrant(
      config,
      new URL(window.location.href),
      {
          pkceCodeVerifier,
          expectedState,
          expectedNonce,
          idTokenExpected: true
      }
  );

  delete sessionStorage['code_verifier'];
  delete sessionStorage['state'];

  localStorage['id_token'] = tokens.id_token;
  localStorage['refresh_token'] = tokens.refresh_token;
  localStorage['access_token'] = tokens.access_token;

  window.location.href = '/demo/';
}

export function OAuthCallback() {
  useEffect(() => {
    oauthCallback();
  }, []);

  return (
    <div id="app" class="container">
      <h2>OAuth Callback</h2>
    </div>
  );
}