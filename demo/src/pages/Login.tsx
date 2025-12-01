import { useLocation } from 'preact-iso';
import { Nav } from "../components/Nav";
import { useAppState } from "../state";
import { login, MICROSOFT_OAUTH_SERVER, GOOGLE_OAUTH_SERVER } from '../oauth';

export function Login() {
  const { route } = useLocation();
  
  const appState = useAppState();
  const authData = appState.authData.value;

  function onLoginWithMicrosoft(e: Event) {
    e.preventDefault();
    login(MICROSOFT_OAUTH_SERVER);
  }

  function onLoginWithGoogle(e: Event) {
    e.preventDefault();
    login(GOOGLE_OAUTH_SERVER);
  }

  if (authData) {
    route("/demo")
  }
  
  return (
    <div id="app" class="container">
      <Nav appState={appState} />
      {MICROSOFT_OAUTH_SERVER ?
        <form onSubmit={onLoginWithMicrosoft}>
          <input type="submit" value="Login with Microsoft" />
        </form>
      : ''}
      {GOOGLE_OAUTH_SERVER ?
        <form onSubmit={onLoginWithGoogle}>
          <input type="submit" value="Login with Google" />
        </form>
      : ''}
    </div>
  );
}