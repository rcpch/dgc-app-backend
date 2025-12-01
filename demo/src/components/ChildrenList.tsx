import { useEffect, useState } from "preact/hooks";
import { addChild, removeChild, getChildren, Organisation, Child, removeUserFromOrganisation, shareOrganisation, updateChild } from "../api";
import { CreateChildRow } from "./CreateChildRow";
import { ChildRow } from "./ChildRow";

function organisationName(organisation: Organisation): string {
  if(organisation.name) {
    return organisation.name;
  }

  const creator = organisation.users.find(user => user.is_creator);
  if(creator) {
    return `${creator.name}'s Organisation`;
  }
  
  return organisation.id;
}

export function ChildrenList({ organisation }: { organisation: Organisation }) {
  const [children, setChildren] = useState<Child[]>([]);

  useEffect(() => {
    getChildren(organisation.id).then(setChildren);
  }, [organisation.id])

  async function onCreateChild(name: string, date_of_birth: string) {
    const child = await addChild(organisation.id, name, date_of_birth);
    setChildren([...children, child]);
  }

  async function onSaveEdit(id: string, name: string, date_of_birth: string) {
    const child = await updateChild(organisation.id, {
      id,
      name,
      date_of_birth,
    });

    setChildren(children =>
      children.map(c =>
        c.id === id ? child : c
      )
    );
  }

  async function onRemoveChild(id: string) {
    await removeChild(organisation.id, id);
    setChildren(children.filter(c => c.id !== id));
  }

  async function onShareOrganisation() {
    const { invite_id, token } = await shareOrganisation(organisation.id);

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

  const sharedWithUsers = organisation.users.filter(user => !user.is_current_user);

  return <div>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        <h3>
          {organisationName(organisation)}
        </h3>
        {sharedWithUsers.length > 0 &&
          <ul>
            {sharedWithUsers.map(user => (
              <li
                key={user.email}
                title={user.email}
                style={{
                  listStyleType: 'none',
                  display: 'inline',
                  marginRight: '8px'
                }}>
                {user.name} {user.is_current_user ? "(You)" : ""}
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
              </li>
            ))}
          </ul>
        }
      </div>
      <button onClick={onShareOrganisation}>
        Share
      </button>
    </div>
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Birth Date</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {children.map(child => (
          <ChildRow
            key={child.id}
            child={child}
            onSave={(name, date_of_birth) => {
              onSaveEdit(child.id, name, date_of_birth);
            }}
            onRemove={() => {
              onRemoveChild(child.id);
            }}
          />
        ))}
        <CreateChildRow
          onSave={onCreateChild}
        />
      </tbody>
    </table>
  </div>;
}