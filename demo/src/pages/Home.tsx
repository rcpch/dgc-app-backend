import { useState, useEffect } from 'preact/hooks';
import * as client from 'openid-client';

import { getPatients, addPatient, deletePatient, updatePatient, testBackend, Patient, Organisation, getOrganisations, createDefaultOrganisation, shareOrganisation, exchangeAccessToken , refreshAccessToken} from '../api';
import { OrganisationPatientList } from '../components/OrganisationPatients';
import { AuthData, clearAuthData, getAuthData, saveAuthData } from '../auth';
import { login } from '../oauth';

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

  function onTestFormSubmit(e: Event) {
    e.preventDefault();
    testBackend();
  }

  function onTestRefreshToken(e: Event) {
    e.preventDefault();
    refreshAccessToken();
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