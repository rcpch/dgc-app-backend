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

  return <div>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        <h3>
          {organisationName(organisation)}
        </h3>
      </div>
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