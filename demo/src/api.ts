import { getAuthData } from "./auth";

export type OrganisationUser = {
  name: string;
  email: string;
  is_current_user: boolean;
}

export type Organisation = {
  id: string;
  users: OrganisationUser[];
  name?: string;
}

export type Patient = {
  id: string;
  name: string;
  date_of_birth: string;
};

export type TokenResponse = {
  access_token: string;
  email: string;
  name: string;
}

export async function exchangeTokens(idToken: string): Promise<TokenResponse> {
  const response = await fetch("/api/token", {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ id_token: idToken })
  });

  return response.json();
}

export async function testBackend() {
  const response = await fetch("/api/hello", {
    headers: {
      'Authorization': `Bearer ${getAuthData()!.access_token}`
    }
  });

  const name = await response.text();

  alert(`Hello ${name}`);
}

export async function getOrganisations(): Promise<Organisation[]> {
  const response = await fetch("/api/organisations", {
    headers: {
      'Authorization': `Bearer ${getAuthData()!.access_token}`
    }
  });

  const { organisations } = await response.json();

  return organisations;
}

export async function createDefaultOrganisation(): Promise<Organisation> {
  const response = await fetch("/api/organisations", {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAuthData()!.access_token}`,
       'Content-Type': 'application/json'
    },
    body: JSON.stringify({})
  });

  const organisation = await response.json();

  return organisation;
}

export async function getPatients(organisation_id: string): Promise<Patient[]> {
  const response = await fetch(`/api/organisations/${organisation_id}/patients`, {
    headers: {
      'Authorization': `Bearer ${getAuthData()!.access_token}`
    }
  });

  const { patients } = await response.json();

  return patients;
}

export async function addPatient(organisation_id: string, name: string, date_of_birth: string): Promise<Patient> {
  const response = await fetch(`/api/organisations/${organisation_id}/patients`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthData()!.access_token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name, date_of_birth })
    });

    const patient = await response.json();

    return patient;
}

export async function deletePatient(organisation_id: string, id: string): Promise<void> {
  await fetch(`/api/organisations/${organisation_id}/patients/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${getAuthData()!.access_token}`,
      }
    });
}

export async function updatePatient(organisation_id: string, patient: Patient): Promise<Patient> {
  const body = { ...patient };
  delete body.id;

  const response = await fetch(`/api/organisations/${organisation_id}/patients/${patient.id}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${getAuthData()!.access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(patient)
  });

  return response.json();
}

export type InviteLink = {
  invite_id: string;
  token: string;
}

export async function shareOrganisation(organisation_id: string): Promise<InviteLink> {
  const response = await fetch(`/api/organisations/${organisation_id}/share`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAuthData()!.access_token}`,
      'Content-Type': 'application/json'
    }
  });

  const { invite_id, token } = await response.json();

  return { invite_id, token };
}

export type InviteDetails = {
  organisation_id: string;
  organisation_name: string | null;
  patient_count: number;
  users: { name: string }[];
}

export async function getInviteDetails(invite_id: string, token: string): Promise<InviteDetails> {
  const response = await fetch(`/api/invites/${invite_id}/details`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAuthData()!.access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ token })
  });

  const { organisation_id, organisation_name, patient_count, users } = await response.json();

  return { organisation_id, organisation_name, patient_count, users };
}

export async function redeemInvite(invite_id: string, token: string) {
  await fetch(`/api/invites/${invite_id}/redeem`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAuthData()!.access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ token })
  });
}

export async function removeUserFromOrganisation(organisation_id: string, user_id: string) {
  await fetch(`/api/organisations/${organisation_id}/users/${user_id}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${getAuthData()!.access_token}`,
      'Content-Type': 'application/json'
    },
  });
}
