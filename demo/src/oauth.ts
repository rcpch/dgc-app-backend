import * as client from 'openid-client';

export async function login() {
  const config = await client.discovery(
    new URL(import.meta.env.VITE_DEMO_OAUTH_SERVER),
    import.meta.env.VITE_DEMO_OAUTH_CLIENT_ID
  );

  const code_verifier = client.randomPKCECodeVerifier();
  const code_challenge = await client.calculatePKCECodeChallenge(code_verifier);

  const state = client.randomState();
  const nonce = client.randomNonce();

  const parameters = {
    redirect_uri: `https://${import.meta.env.VITE_SITE_DOMAIN}/demo/oauth-callback`,
    scope: 'openid profile email',
    code_challenge,
    code_challenge_method: 'S256',
    state,
    nonce
  }

  const authUrl = client.buildAuthorizationUrl(config, parameters);

  sessionStorage['code_verifier'] = code_verifier;
  sessionStorage['state'] = state;
  sessionStorage['nonce'] = nonce;

  window.location.href = authUrl.href;
}

type RefreshTokenResponse = {
    access_token: string;
    refresh_token: string;
}

export async function refreshToken(refreshTokenBefore: string): Promise<RefreshTokenResponse> {
  const config = await client.discovery(
    new URL(import.meta.env.VITE_DEMO_OAUTH_SERVER),
    import.meta.env.VITE_DEMO_OAUTH_CLIENT_ID
  );

  const { access_token, refresh_token } = await client.refreshTokenGrant(config, refreshTokenBefore);

  return {
    access_token,
    refresh_token
  }
}
