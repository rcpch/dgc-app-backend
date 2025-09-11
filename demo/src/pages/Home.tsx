import { useState, useEffect } from 'preact/hooks';
import * as client from 'openid-client';

async function login() {
  const config = await client.discovery(
    new URL(import.meta.env.VITE_DEMO_OAUTH_SERVER),
    import.meta.env.VITE_DEMO_OAUTH_CLIENT_ID,
    {
      client_secret: import.meta.env.VITE_DEMO_OAUTH_CLIENT_SECRET,
    }
  );

  const code_verifier = client.randomPKCECodeVerifier();
  const code_challenge = await client.calculatePKCECodeChallenge(code_verifier);

  const state = client.randomState();

  const parameters = {
    redirect_uri: 'https://dgc-app-backend.localhost/demo/oauth-callback',
    scope: `${import.meta.env.VITE_DEMO_OAUTH_CLIENT_ID}/.default`,
    code_challenge,
    code_challenge_method: 'S256',
    state
  }

  const authUrl = client.buildAuthorizationUrl(config, parameters);

  sessionStorage['code_verifier'] = code_verifier;
  sessionStorage['state'] = state;

  window.location.href = authUrl.href;
}

async function testBackend() {
  const response = await fetch("/api/hello", {
    headers: {
      'Authorization': `Bearer ${localStorage['access_token']}`
    }
  });

  const name = await response.text();

  alert(`Hello ${name}`);
}

async function getPatients() {
  const response = await fetch("/api/patients", {
    headers: {
      'Authorization': `Bearer ${localStorage['access_token']}`
    }
  });

  const patients = await response.json();

  console.log(patients);
}

export function Home() {
  const [token, setToken] = useState(localStorage.access_token);

  useEffect(() => {
    getPatients();
  }, []);

  const sub = token ? JSON.parse(atob(token.split('.')[1])).sub : null;

  function onTestFormSubmit(e: Event) {
    e.preventDefault();
    testBackend();
  }

  function onLoginFormSubmit(e: Event) {
    e.preventDefault();
    if (token) {
      delete localStorage['access_token'];
      setToken('');
    } else {
      login();
    }
  };

	return (
		<div id="app" class="container">
      {token ?
        <form id="test_form" onSubmit={onTestFormSubmit}>
          <h3 id="sub">
            {sub ? `Logged in as: ${sub}` : ''}
          </h3>
          <input type="submit" value="Test Backend" />
        </form>
      : ''}
			<form id="login_form" onSubmit={onLoginFormSubmit}>
				<input type="submit" value={token ? 'Logout' : 'Login'} />
			</form>
			</div>
	);
}