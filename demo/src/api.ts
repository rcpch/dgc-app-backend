export type Organisation = {
  id: string;
  name?: string;
}

export type Patient = {
  id: string;
  name: string;
  date_of_birth: string;
};

export async function testBackend() {
  const response = await fetch("/api/hello", {
    headers: {
      'Authorization': `Bearer ${localStorage['access_token']}`
    }
  });

  const name = await response.text();

  alert(`Hello ${name}`);
}

export async function getOrganisations(): Promise<Organisation[]> {
  const response = await fetch("/api/organisations", {
    headers: {
      'Authorization': `Bearer ${localStorage['access_token']}`
    }
  });

  const { organisations } = await response.json();

  return organisations;
}

export async function createDefaultOrganisation(): Promise<Organisation> {
  const response = await fetch("/api/organisations", {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage['access_token']}`,
       'Content-Type': 'application/json'
    },
    body: JSON.stringify({})
  });

  const organisation = await response.json();

  return organisation;
}

export async function getPatients(): Promise<Patient[]> {
  const response = await fetch("/api/patients", {
    headers: {
      'Authorization': `Bearer ${localStorage['access_token']}`
    }
  });

  const { patients } = await response.json();

  return patients;
}

export async function addPatient(name: string, date_of_birth: string): Promise<Patient> {
  const response = await fetch("/api/patients", {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage['access_token']}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name, date_of_birth })
    });

    const patient = await response.json();

    return patient;
}

export async function deletePatient(id: string): Promise<void> {
  await fetch(`/api/patients/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage['access_token']}`,
      }
    });
}

export async function updatePatient(patient: Patient): Promise<Patient> {
  const body = { ...patient };
  delete body.id;

  const response = await fetch(`/api/patients/${patient.id}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${localStorage['access_token']}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(patient)
  });

  return response.json();
}

export async function sharePatient(id: string): Promise<string> {
  const response = await fetch(`/api/patients/${id}/share`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage['access_token']}`,
      'Content-Type': 'application/json'
    }
  });

  const { token } = await response.json();

  return token;
}

export type ShareDetails = {
  sharer_name: string;
  patient_name: string;
}

export async function getShareDetails(token: string): Promise<ShareDetails> {
  const response = await fetch(`/api/share-token-details`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage['access_token']}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ token })
  });

  const { sharer_name, patient_name } = await response.json();

  return { sharer_name, patient_name };
}

export async function addSharedPatient(token: string) {
  const response = await fetch(`/api/use-share-token`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage['access_token']}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ token })
  });

  const { patient } = await response.json();

  return patient;
}
