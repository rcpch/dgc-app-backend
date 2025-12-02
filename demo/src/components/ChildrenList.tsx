import { addChild, removeChild, getChildrenInOrganisation, Organisation, Child, removeUserFromOrganisation, shareOrganisation, updateChild } from "../api";
import { CreateChildRow } from "./AddChildRow";
import { ChildRow, ChildWithOrganisations } from "./ChildRow";
import { useLoggedInAppState } from '../state';

export function organisationName(organisation: Organisation): string {
  if(organisation.name) {
    return organisation.name;
  }

  const creator = organisation.users.find(user => user.is_creator);
  if(creator) {
    return `${creator.name}'s Organisation`;
  }
  
  return organisation.id;
}

export function ChildrenList() {
  const appState = useLoggedInAppState();

  const organisations = appState.organisations.value;
  const children = appState.children.value;

  async function onAddChild(organisationId: string, name: string, date_of_birth: string) {
    appState.addChild(organisationId, name, date_of_birth);
  }

  // async function onSaveEdit(id: string, name: string, date_of_birth: string) {
  //   const child = await updateChild(organisation.id, {
  //     id,
  //     name,
  //     date_of_birth,
  //   });

  //   setChildren(children =>
  //     children.map(c =>
  //       c.id === id ? child : c
  //     )
  //   );
  // }

  // async function onRemoveChild(id: string) {
  //   await removeChild(organisation.id, id);
  //   setChildren(children.filter(c => c.id !== id));
  // }

  const childrenWithOrgs: ChildWithOrganisations[] = children.map(child => {
    const organisationsForChild = organisations.filter(org =>
      child.organisation_ids.includes(org.id)
    );

    return {
      ...child,
      organisations: organisationsForChild
    };
  });

  return <table>
    <thead>
      <tr>
        <th>Name</th>
        <th>Birth Date</th>
        <th>Organisations</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {childrenWithOrgs.map(childWithOrgs => (
        <ChildRow
          key={childWithOrgs.id}
          childWithOrgs={childWithOrgs}
          onSave={(name, date_of_birth) => {
            onSaveEdit(child.id, name, date_of_birth);
          }}
          onRemove={() => {
            onRemoveChild(child.id);
          }}
        />
      ))}
      {organisations.length > 0 && (
        <CreateChildRow
          organisations={organisations}
          onSave={onAddChild}
        />
      )}
    </tbody>
  </table>;
}