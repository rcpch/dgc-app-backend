import { useState, useEffect } from 'preact/hooks';

import { testBackend, Organisation, getOrganisations, refreshAccessToken} from '../api';
import { OrganisationPatientList } from '../components/OrganisationPatients';
import { AuthData, clearAuthData, getAuthData } from '../auth';
import { login, MICROSOFT_OAUTH_SERVER, GOOGLE_OAUTH_SERVER } from '../oauth';

export function Home() {
  const [authData, setAuthData] = useState<AuthData | undefined>(getAuthData());
  const [organisations, setOrganisations] = useState<Organisation[]>([]);

  const accessToken = authData?.access_token;

  useEffect(() => {
    if(accessToken) {
      getOrganisations().then(setOrganisations);
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

  function onLoginWithMicrosoft(e: Event) {
    e.preventDefault();
    login(MICROSOFT_OAUTH_SERVER);
  }

  function onLoginWithGoogle(e: Event) {
    e.preventDefault();
    login(GOOGLE_OAUTH_SERVER);
  }

  function onLogout(e: Event) {
    e.preventDefault();
    clearAuthData();
    setAuthData(null);
    setOrganisations([]);
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
      {!authData && MICROSOFT_OAUTH_SERVER ?
        <form onSubmit={onLoginWithMicrosoft}>
          <input type="submit" value="Login with Microsoft" />
        </form>
      : ''}
      {!authData && MICROSOFT_OAUTH_SERVER ?
        <form onSubmit={onLoginWithGoogle}>
          <input type="submit" value="Login with Google" />
        </form>
      : ''}
      {authData ?
        <form onSubmit={onLogout}>
          <input type="submit" value="Logout" />
        </form>
      : ''}
    </div>
	);
}