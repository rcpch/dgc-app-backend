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
            <th>Centile</th>
            <th>SDS</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {child.observations.map(observation => (
            <tr>
              <td>{new Date(observation.observation_date).toLocaleDateString()}</td>
              <td>{observation.observation_type}</td>
              <td>{observation.observation_value}</td>
              <td>
                {observation.dgc_api_result.measurement_calculated_values.corrected_centile}
              </td>
              <td>
                {observation.dgc_api_result.measurement_calculated_values.corrected_sds}
              </td>
              <td>
                {/* Empty cell for actions */}
              </td>
            </tr>
          ))}
          <CreateObservationRow
            onSave={async (observationDate, observationType, observationValue) => {
              await appState.addObservation(child.id, {
                observation_date: observationDate.toISOString(),
                observation_type: observationType,
                observation_value: observationValue
              });

              await appState.refetchChildren();
            }}
          />
        </tbody>
      </table>
    </div>
  );
}