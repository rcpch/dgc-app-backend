import { Nav } from "../components/Nav";
import { CreateObservationRow } from "../components/CreateObservationRow";
import { useLoggedInAppState } from "../state";

export function Measurements({ child_id }: { child_id: string }) {
  const appState = useLoggedInAppState();

  const child = appState.children.value.find(c => c.id === child_id);

  if (!child) {
    return <div>Child not found</div>;
  }

  return (
    <div id="app" class="container">
      <Nav appState={appState} />
      <h1>{child.name}</h1>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Observation Type</th>
            <th>Observation Value</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <CreateObservationRow
            onSave={(observationDate, observationType, observationValue) => {
              console.log('Save observation', observationDate, observationType, observationValue);
            }}
          />
        </tbody>
      </table>
    </div>
  );
}