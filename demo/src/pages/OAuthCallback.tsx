import { useEffect } from 'preact/hooks';
import * as client from 'openid-client';
import { exchangeTokens } from '../api';
import { saveAuthData } from '../auth';

async function oauthCallback() {
  const config = await client.discovery(
    new URL(import.meta.env.VITE_DEMO_OAUTH_SERVER),
    import.meta.env.VITE_DEMO_OAUTH_CLIENT_ID
  );

  const pkceCodeVerifier = sessionStorage['code_verifier'];
  const expectedState = sessionStorage['state'];
  const expectedNonce = sessionStorage['nonce'];

  const { id_token, refresh_token } = await client.authorizationCodeGrant(
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

  const { access_token, name, email } = await exchangeTokens(id_token);

  saveAuthData({
    access_token,
    refresh_token,
    name,
    email
  })

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