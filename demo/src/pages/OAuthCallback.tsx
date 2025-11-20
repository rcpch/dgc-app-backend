import { useEffect } from 'preact/hooks';
import * as client from 'openid-client';
import { exchangeIdToken } from '../api';
import { saveAuthData } from '../auth';
import { fetchConfig } from '../oauth';

async function oauthCallback() {
  const sessionOauthServer = sessionStorage['oauth_server'];
  
  const config = await fetchConfig(sessionOauthServer);

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

  const { access_token, name, email } = await exchangeIdToken(sessionOauthServer, id_token);

  saveAuthData({
    oauth_server: sessionOauthServer,
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