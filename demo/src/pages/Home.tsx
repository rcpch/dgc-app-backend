import { useState, useEffect } from 'preact/hooks';
import * as client from 'openid-client';

import { getPatients, addPatient, deletePatient, updatePatient, testBackend, sharePatient, Patient, Organisation, getOrganisations, createDefaultOrganisation, shareOrganisation } from '../api';
import { OrganisationPatientList } from '../components/OrganisationPatients';

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
    scope: import.meta.env.VITE_DEMO_OAUTH_SCOPE,
    code_challenge,
    code_challenge_method: 'S256',
    state
  }

  const authUrl = client.buildAuthorizationUrl(config, parameters);

  sessionStorage['code_verifier'] = code_verifier;
  sessionStorage['state'] = state;

  window.location.href = authUrl.href;
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