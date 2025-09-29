import { useState } from "preact/hooks";
import { Patient } from "../api";

type PatientRowProps = {
  patient: Patient;
  onSave: (name: string, date_of_birth: string) => void;
  onDelete: () => void;
}

export function PatientRow({ patient, onSave, onDelete }: PatientRowProps) {
  const [editing, setEditing] = useState(false);

  const [editingName, setEditingName] = useState<string | null>(null);
  const [editingDateOfBirth, setEditingDateOfBirth] = useState<string | null>(null);

  function onStartEdit() {
    setEditing(true);
    setEditingName(patient.name);
    setEditingDateOfBirth(patient.date_of_birth);
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
    <tr key={patient.id}>
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
          patient.name
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
          patient.date_of_birth
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
              onClick={onDelete}>
              Delete
            </button>
          </>
        )}
      </td>
    </tr>
  );
}