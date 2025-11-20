import { useState, useEffect } from 'preact/hooks';
import * as client from 'openid-client';

import { getPatients, addPatient, deletePatient, updatePatient, testBackend, Patient, Organisation, getOrganisations, createDefaultOrganisation, shareOrganisation, exchangeTokens } from '../api';
import { OrganisationPatientList } from '../components/OrganisationPatients';

async function login() {
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

async function refreshToken() {
  const config = await client.discovery(
    new URL(import.meta.env.VITE_DEMO_OAUTH_SERVER),
    import.meta.env.VITE_DEMO_OAUTH_CLIENT_ID
  );

  const refreshTokenBefore = localStorage['refresh_token'];

  const { id_token, refresh_token } = await client.refreshTokenGrant(config, refreshTokenBefore);

  const { access_token, name, email } = await exchangeTokens(id_token);

  localStorage['id_token'] = id_token;
  localStorage['refresh_token'] = refresh_token;
  localStorage['access_token'] = access_token;
}

export function Home() {
  const [token, setToken] = useState(localStorage.access_token);

  const [organisations, setOrganisations] = useState<Organisation[]>([]);

  useEffect(() => {
    if(token) {
      getOrganisations().then((organisations) => {
        if(organisations.length === 0) {
          createDefaultOrganisation().then(org => setOrganisations([org]));
        } else {
          setOrganisations(organisations);
        }
      });
    } else {
      setOrganisations([]);
    }
  }, [token]);

  // const name = token ? JSON.parse(atob(token.split('.')[1])).unique_name : null;

  function onTestFormSubmit(e: Event) {
    e.preventDefault();
    testBackend();
  }

  function onTestRefreshToken(e: Event) {
    e.preventDefault();
    refreshToken();
  }

  function onTestExchangeTokens(e: Event) {
    e.preventDefault();
    exchangeTokens(localStorage['id_token']);
  }

  function onLoginFormSubmit(e: Event) {
    e.preventDefault();
    if (token) {
      delete localStorage['access_token'];
      setToken('');
      setOrganisations([]);
    } else {
      login();
    }
  };

	return (
		<div id="app" class="container">
      {token ?
        <>  
          {/* <h3 id="sub">
            {name ? `Logged in as: ${name}` : ''}
          </h3> */}
          <hr />
          <form onSubmit={onTestFormSubmit}>
            <input type="submit" value="Test Backend" />
          </form>
          <form onSubmit={onTestRefreshToken}>
            <input type="submit" value="Test Refresh Token" />
          </form>
          <hr />
          {organisations.map(organisation => (
            <>
              <OrganisationPatientList key={organisation.id} organisation={organisation} />
              <hr />
            </> 
          ))}
        </>
      : ''}
			<form onSubmit={onLoginFormSubmit}>
				<input type="submit" value={token ? 'Logout' : 'Login'} />
			</form>
    </div>
	);
}