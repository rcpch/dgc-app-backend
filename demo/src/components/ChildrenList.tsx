import { removeChild, Organisation, Child, updateChild, Sex } from "../api";
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

  async function onAddChild(organisationId: string, child: Omit<Child, 'id' | 'organisation_ids'>) {
    appState.addChild(organisationId, child);
  }

  async function onSaveEdit(id: string, name: string, date_of_birth: string, sex: Sex) {
    await updateChild({
      id,
      name,
      date_of_birth,
      sex,
    });

    await appState.refetchChildren();
  }

  async function onRemoveChild(organisation_id: string, child_id: string) {
    await removeChild(organisation_id, child_id);
    await appState.refetchChildren();
  }

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
        <th>Sex</th>
        <th>Organisations</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {childrenWithOrgs.map(childWithOrgs => (
        <ChildRow
          key={childWithOrgs.id}
          childWithOrgs={childWithOrgs}
          onSave={(name, date_of_birth, sex) => {
            onSaveEdit(childWithOrgs.id, name, date_of_birth, sex);
          }}
          onRemove={(organisation_id) => {
            onRemoveChild(organisation_id, childWithOrgs.id);
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