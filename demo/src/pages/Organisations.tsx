import { Nav } from "../components/Nav";
import { useLoggedInAppState } from "../state";

export function Organisations() {
  const appState = useLoggedInAppState();

  return (
    <div id="app" class="container">
      <Nav appState={appState} />
      <h2>Organisations</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Users</th>
          </tr>
        </thead>
        {appState.organisations.value.map(organisation => (
          <tr key={organisation.id}>
            <td>{organisation.id}</td>
            <td>{organisation.name}</td>
            <td>
              <ul>
                {organisation.users.map(user => (
                  <li
                    key={user.email}
                    title={user.email}
                    style={{
                      listStyleType: 'none',
                      display: 'inline',
                      marginRight: '8px'
                    }}>
                    {user.email}
                    {!user.is_current_user && !user.is_creator ? (
                      <input
                        type="button"
                        value="x"
                        className="pico-background-red"
                        style={{
                          width: '2em',
                          height: '2em',
                          padding: '0'
                        }}
                        onClick={() => onRemoveUserFromOrganisation(organisation.id, user.id)}
                      />
                    ) : ''}
                  </li>
                ))}
              </ul>
            </td>
          </tr>
        ))}
      </table>
    </div>
  );
}