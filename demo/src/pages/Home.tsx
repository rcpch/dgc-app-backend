import { useState, useEffect } from 'preact/hooks';

import { testBackend, Organisation, getOrganisations, refreshAccessToken} from '../api';
import { ChildrenList } from '../components/ChildrenList';
import { Nav } from '../components/Nav';
import { useLoggedInAppState } from '../state';

export function Home() {
  const appState = useLoggedInAppState();

  const [organisations, setOrganisations] = useState<Organisation[]>([]);

  const authData = appState.authData.value;
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

	return (
		<div id="app" class="container">
      <Nav appState={appState} />
      {authData ?
        <>
          <form onSubmit={onTestFormSubmit}>
            <input type="submit" value="Test Backend" />
          </form>
          <form onSubmit={onTestRefreshToken}>
            <input type="submit" value="Test Refresh Token" />
          </form>
          <hr />
          {organisations.map(organisation => (
            <>
              <ChildrenList key={organisation.id} organisation={organisation} />
              <hr />
            </> 
          ))}
        </>
      : ''}
    </div>
	);
}