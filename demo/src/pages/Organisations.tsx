import { Nav } from "../components/Nav";
import { useLoggedInAppState } from "../state";

export function Organisations() {
  const appState = useLoggedInAppState();

  return (
    <div id="app" class="container">
      <Nav appState={appState} />
      <h2>Organisations Page</h2>
    </div>
  );
}