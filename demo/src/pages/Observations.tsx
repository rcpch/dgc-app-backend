import { Nav } from "../components/Nav";
import { CreateObservationRow } from "../components/AddObservationRow";
import { useLoggedInAppState } from "../state";

export function Observations({ child_id }: { child_id: string }) {
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
              appState.addObservation(child.id, {
                observation_date: observationDate.toISOString(),
                observation_type: observationType,
                observation_value: observationValue
              });
            }}
          />
        </tbody>
      </table>
    </div>
  );
}