import { useState } from "preact/hooks";
import { Child } from "../api";

type ChildRowProps = {
  child: Child;
  onSave: (name: string, date_of_birth: string) => void;
  onRemove: () => void;
}

export function ChildRow({ child, onSave, onRemove }: ChildRowProps) {
  const [editing, setEditing] = useState(false);

  const [editingName, setEditingName] = useState<string | null>(null);
  const [editingDateOfBirth, setEditingDateOfBirth] = useState<string | null>(null);

  function onStartEdit() {
    setEditing(true);
    setEditingName(child.name);
    setEditingDateOfBirth(child.date_of_birth);
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
    <tr key={child.id}>
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
          child.name
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
          child.date_of_birth
        )}
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
            <button
              class="pico-background-red"
              onClick={onRemove}>
              Delete Child Data
            </button>
          </>
        )}
      </td>
    </tr>
  );
}