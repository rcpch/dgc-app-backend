import { useState, useEffect } from 'preact/hooks';
import * as client from 'openid-client';

import { getPatients, addPatient, deletePatient, updatePatient, testBackend, Patient, Organisation, getOrganisations, createDefaultOrganisation, shareOrganisation, exchangeTokens } from '../api';
import { OrganisationPatientList } from '../components/OrganisationPatients';
import { AuthData, clearAuthData, getAuthData, saveAuthData } from '../auth';

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

  const refreshTokenBefore = getAuthData()!.refresh_token;

  const { id_token, refresh_token } = await client.refreshTokenGrant(config, refreshTokenBefore);

  const { access_token, name, email } = await exchangeTokens(id_token);

  saveAuthData({
    access_token,
    refresh_token,
    name,
    email
  })
}

export function Home() {
  const [authData, setAuthData] = useState<AuthData | undefined>(getAuthData());
  const [organisations, setOrganisations] = useState<Organisation[]>([]);

  const accessToken = authData?.access_token;

  useEffect(() => {
    if(accessToken) {
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
  }, [accessToken]);

  // const name = token ? JSON.parse(atob(token.split('.')[1])).unique_name : null;

  function onTestFormSubmit(e: Event) {
    e.preventDefault();
    testBackend();
  }

  function onTestRefreshToken(e: Event) {
    e.preventDefault();
    refreshToken();
  }

  function onLoginFormSubmit(e: Event) {
    e.preventDefault();
    if (authData) {
      clearAuthData();
      setAuthData(null);
      setOrganisations([]);
    } else {
      login();
    }
  };

	return (
		<div id="app" class="container">
      {authData ?
        <>  
          <h3 id="sub">
            Logged in as {authData.name} ({authData.email})
          </h3>
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
				<input type="submit" value={authData ? 'Logout' : 'Login'} />
			</form>
    </div>
	);
}