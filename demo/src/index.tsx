import { render } from 'preact';
import { LocationProvider, Router, Route } from 'preact-iso';

import { Home } from './pages/Home';
import { OAuthCallback } from './pages/OAuthCallback';
import { Invite } from './pages/Invite';
import { NotFound } from './pages/_404';
import { Organisations } from './pages/Organisations';
import { AppStateCtx, createAppState } from './state';
import { Login } from './pages/Login';
import { Observations } from './pages/Observations';

export function App() {
  return (
    <AppStateCtx.Provider value={createAppState()}>
      <LocationProvider>
        <main>
          <Router>
            <Route path="/demo/child/:child_id" component={Observations} />
            <Route path="/demo/organisations" component={Organisations} />
            <Route path="/demo/oauth-callback" component={OAuthCallback} />
            <Route path="/demo/invite" component={Invite} />
            <Route path="/demo/login" component={Login} />
            <Route path="/demo" component={Home} />
            <Route default component={NotFound} />
          </Router>
        </main>
      </LocationProvider>
    </AppStateCtx.Provider>
  );
}

render(<App />, document.getElementById('app'));
