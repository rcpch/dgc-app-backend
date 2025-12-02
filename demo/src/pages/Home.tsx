import { testBackend, refreshAccessToken} from '../api';
import { ChildrenList } from '../components/ChildrenList';
import { Nav } from '../components/Nav';
import { useLoggedInAppState } from '../state';

export function Home() {
  const appState = useLoggedInAppState();

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
      <form onSubmit={onTestFormSubmit}>
        <input type="submit" value="Test Backend" />
      </form>
      <form onSubmit={onTestRefreshToken}>
        <input type="submit" value="Test Refresh Token" />
      </form>
      <hr />
      <ChildrenList />
    </div>
	);
}