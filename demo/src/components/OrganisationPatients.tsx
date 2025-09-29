import { useEffect, useState } from "preact/hooks";
import { addPatient, deletePatient, getPatients, Organisation, Patient, shareOrganisation, updatePatient } from "../api";

type PatientRowProps = {
  patient: Patient;
  onSave: (name: string, date_of_birth: string) => void;
  onDelete: () => void;
}

function PatientRow({ patient, onSave, onDelete }: PatientRowProps) {
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

type CreatePatientRowProps = {
  onSave: (name: string, date_of_birth: string) => void;
}

function CreatePatientRow({ onSave }: CreatePatientRowProps) {
  const [name, setName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('1970-01-01');

  function onSubmit(e: Event) {
    e.preventDefault();
    onSave(name, dateOfBirth);
    setName('');
    setDateOfBirth('1970-01-01');
  }

  return <tr key='create'>
    <td>
      <form onSubmit={onSubmit}>
        <input
          type="text"
          value={name}
          onChange={e => setName((e.target as HTMLInputElement).value)}
        />
      </form>
    </td>
    <td>
       <input
        type="date"
        value={dateOfBirth}
        onChange={e => setDateOfBirth((e.target as HTMLInputElement).value)}
      />
    </td>
    <td style={{ display: 'flex', gap: '0.5em', justifyContent: 'flex-end' }}>
      <button onClick={onSubmit}>
        Save
      </button>
    </td>
  </tr>;
}

export function OrganisationPatientList({ organisation }: { organisation: Organisation }) {
  const [patients, setPatients] = useState<Patient[]>([]);

  useEffect(() => {
    getPatients(organisation.id).then(setPatients);
  }, [organisation.id])

  async function onCreatePatient(name: string, date_of_birth: string) {
    const patient = await addPatient(organisation.id, name, date_of_birth);
    setPatients([...patients, patient]);
  }

  async function onSaveEdit(id: string, name: string, date_of_birth: string) {
    const patient = await updatePatient(organisation.id, {
      id,
      name,
      date_of_birth,
    });

    setPatients(patients =>
      patients.map(p =>
        p.id === id ? patient : p
      )
    );
  }

  async function onDeletePatient(id: string) {
    await deletePatient(organisation.id, id);
    setPatients(patients.filter(p => p.id !== id));
  }

  async function onShareOrganisation() {
    const link = await shareOrganisation(organisation.id);
    prompt("Share this link:", window.location.origin + link);
  }

  return <div>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <h3>
        {organisation.name ?? organisation.id}
      </h3>
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
        {patients.map(patient => (
          <PatientRow
            key={patient.id}
            patient={patient}
            onSave={(name, date_of_birth) => {
              onSaveEdit(patient.id, name, date_of_birth);
            }}
            onDelete={() => {
              onDeletePatient(patient.id);
            }}
          />
        ))}
        <CreatePatientRow
          onSave={onCreatePatient}
        />
      </tbody>
    </table>
  </div>;
}