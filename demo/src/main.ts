import * as client from 'openid-client';

const config = await client.discovery(
  new URL(import.meta.env.VITE_DEMO_OAUTH_SERVER),
  import.meta.env.VITE_DEMO_OAUTH_CLIENT_ID,
  {
    client_secret: import.meta.env.VITE_DEMO_OAUTH_CLIENT_SECRET,
  }
);

document.getElementById('login_form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const code_verifier = client.randomPKCECodeVerifier();
  const code_challenge = await client.calculatePKCECodeChallenge(code_verifier);

  const state = client.randomState();

  const parameters = {
    redirect_uri: 'https://dgc-app-backend.localhost/demo/oauth-callback',
    scope: 'openid profile email',
    code_challenge,
    code_challenge_method: 'S256',
    state
  }

  const authUrl = client.buildAuthorizationUrl(config, parameters);

  sessionStorage['code_verifier'] = code_verifier;
  sessionStorage['state'] = state;

  window.location.href = authUrl.href;
})

console.log(config)