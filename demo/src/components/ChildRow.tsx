import { useState } from "preact/hooks";
import { Child, Organisation } from "../api";
import { organisationName } from "./ChildrenList";

export type ChildWithOrganisations = Child & {
  organisations: Organisation[];
}

type ChildRowProps = {
  childWithOrgs: ChildWithOrganisations;
  onSave: (name: string, date_of_birth: string) => void;
  onRemove: (organisation_id: string) => void;
}

export function ChildRow({ childWithOrgs, onSave, onRemove }: ChildRowProps) {
  const [editing, setEditing] = useState(false);

  const [editingName, setEditingName] = useState<string | null>(null);
  const [editingDateOfBirth, setEditingDateOfBirth] = useState<string | null>(null);

  function onStartEdit() {
    setEditing(true);
    setEditingName(childWithOrgs.name);
    setEditingDateOfBirth(childWithOrgs.date_of_birth);
  }

  function onCancelEdit() {
    setEditing(false);
    setEditingName(null);
    setEditingDateOfBirth(null);
  }

  function onSubmit(e: Event) {
    e.preventDefault();

    onSave(editingName!, editingDateOfBirth!);
    setEditing(false);
  }

  return (
    <tr key={childWithOrgs.id}>
      <td>
        {editing ? (
          <form onSubmit={onSubmit}>
            <input
              required
              type="text"
              value={editingName}
              onChange={e => setEditingName((e.target as HTMLInputElement).value)}
            />
          </form>
        ) : (
          childWithOrgs.name
        )}
      </td>
      <td>
        {editing ? (
          <input
            type="date"
            value={editingDateOfBirth}
            onChange={e => setEditingDateOfBirth((e.target as HTMLInputElement).value)}
          />
        ) : (
          childWithOrgs.date_of_birth
        )}
      </td>
      <td>
        {childWithOrgs.organisations.map(org => (
          <span key={org.id}>
            {organisationName(org)}
            <button class="pico-background-red" onClick={() => onRemove(org.id)}>
              X
            </button>
          </span>
        ))}
      </td>
      <td style={{ display: 'flex', gap: '0.5em', justifyContent: 'flex-end' }}>
        {editing ? (
          <>
            <button onClick={onSubmit}>
              Save
            </button>
            <button class="secondary" onClick={onCancelEdit}>
              Cancel
            </button>
          </>
        ) : (
          <>
            <button onClick={onStartEdit}>
              Edit
            </button>
          </>
        )}
      </td>
    </tr>
  );
}