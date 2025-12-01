import { removeUserFromOrganisation, shareOrganisation } from "../api";
import { Nav } from "../components/Nav";
import { useLoggedInAppState } from "../state";

export function Organisations() {
  const appState = useLoggedInAppState();

  async function onShareOrganisation(organisation_id: string) {
    const { invite_id, token } = await shareOrganisation(organisation_id);

    const shareUrl = new URL(window.location.origin);
    shareUrl.pathname = "/demo/invite";
    shareUrl.searchParams.set("invite_id", invite_id);
    shareUrl.searchParams.set("token", token);

    prompt("Share this link:", shareUrl.toString());
  }

  async function onRemoveUserFromOrganisation(organisation_id: string, user_id: string) {
    await removeUserFromOrganisation(organisation_id, user_id);
    window.location.reload();
  }

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
            <th></th>
          </tr>
        </thead>
        <tbody>
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
                    >
                      {user.email}
                      {!user.is_creator ? (
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
              <td>
                <button onClick={() => onShareOrganisation(organisation.id)}>
                  Share
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}