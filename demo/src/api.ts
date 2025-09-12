export type Patient = {
  id: string;
  name: string;
  birth_date: string;
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

export async function getPatients() {
  const response = await fetch("/api/patients", {
    headers: {
      'Authorization': `Bearer ${localStorage['access_token']}`
    }
  });

  const { patients } = await response.json();

  return patients;
}

export async function addPatient(name: string, birth_date: string) {
  const response = await fetch("/api/patients", {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage['access_token']}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name, birth_date })
    });

    const patient = await response.json();

    return patient;
}

export async function deletePatient(id: string) {
  await fetch(`/api/patients/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage['access_token']}`,
      }
    });
}

export async function updatePatient(patient: Patient) {
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

export async function sharePatient(id: string) {
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

export async function addSharedPatient(token: string) {
  const response = await fetch(`/api/patients-from-share`, {
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
