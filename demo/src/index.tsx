import { render } from 'preact';
import { LocationProvider, Router, Route } from 'preact-iso';

import { Home } from './pages/Home';
import { OAuthCallback } from './pages/OAuthCallback';
import { Share } from './pages/Share';
import { NotFound } from './pages/_404';

export function App() {
	return (
		<LocationProvider>
			<main>
				<Router>
					<Route path="/demo/oauth-callback" component={OAuthCallback} />
					<Route path="/demo/share" component={Share} />
					<Route path="/demo" component={Home} />
					<Route default component={NotFound} />
				</Router>
			</main>
		</LocationProvider>
	);
}

render(<App />, document.getElementById('app'));
