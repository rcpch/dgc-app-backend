import { useEffect, useState } from "preact/hooks";
import { addPatient, deletePatient, getPatients, Organisation, Patient, shareOrganisation, updatePatient } from "../api";
import { CreatePatientRow } from "./CreatePatientRow";
import { PatientRow } from "./PatientRow";

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
    const { invite_id, token } = await shareOrganisation(organisation.id);

    const shareUrl = new URL(window.location.origin);
    shareUrl.pathname = "/demo/invite";
    shareUrl.searchParams.set("invite_id", invite_id);
    shareUrl.searchParams.set("token", token);

    prompt("Share this link:", shareUrl.toString());
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