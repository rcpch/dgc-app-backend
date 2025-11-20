import * as client from 'openid-client';

export const MICROSOFT_OAUTH_SERVER = import.meta.env.VITE_MICROSOFT_OAUTH_SERVER;
export const MICROSOFT_OAUTH_CLIENT_ID = import.meta.env.VITE_MICROSOFT_OAUTH_CLIENT_ID;

export const GOOGLE_OAUTH_SERVER = import.meta.env.VITE_GOOGLE_OAUTH_SERVER;
export const GOOGLE_OAUTH_CLIENT_ID = import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID;

export async function fetchConfig(oauthServer: string): Promise<client.Configuration> {
  switch(oauthServer) {
    case MICROSOFT_OAUTH_SERVER:
      return client.discovery(
        new URL(MICROSOFT_OAUTH_SERVER),
        import.meta.env.VITE_MICROSOFT_OAUTH_CLIENT_ID
      );
    case GOOGLE_OAUTH_SERVER:
      return client.discovery(
        new URL(GOOGLE_OAUTH_SERVER),
        import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID
      );
    default:
      throw new Error(`Unknown OAuth server ${oauthServer}`);
  }
}

export async function login(oauthServer: string) {
  const config = await fetchConfig(oauthServer);

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
  sessionStorage['oauth_server'] = oauthServer;

  window.location.href = authUrl.href;
}

type RefreshTokenResponse = {
    access_token: string;
    refresh_token: string;
}

export async function refreshToken(oauthServer: string, refreshTokenBefore: string): Promise<RefreshTokenResponse> {
  const config = await fetchConfig(oauthServer);
  const { access_token, refresh_token } = await client.refreshTokenGrant(config, refreshTokenBefore);

  return {
    access_token,
    refresh_token
  }
}
