import { getAuthData, saveAuthData } from "./auth";
import { refreshToken } from "./oauth";

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

export type ExchangeIdTokenResponse = {
  access_token: string;
  email: string;
  name: string;
}

export async function exchangeIdToken(oauth_server: string, id_token: string): Promise<ExchangeIdTokenResponse> {
  const response = await fetch("/api/token", {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ oauth_server, id_token })
  });

  return response.json();
}

export type ExchangeAccessTokenResponse = {
  access_token: string;
}

export async function exchangeAccessToken(oauth_server: string, access_token: string): Promise<ExchangeAccessTokenResponse> {
  const response = await fetch("/api/token", {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ oauth_server, access_token })
  });

  return response.json();
}

export async function refreshAccessToken(): Promise<void> {
  const authData = getAuthData();

  if(authData) {
    const thirdPartyTokens = await refreshToken(authData.oauth_server, authData.refresh_token);
    const { access_token } = await exchangeAccessToken(authData.oauth_server, thirdPartyTokens.access_token);

    const newAuthData = {
      ...authData,
      access_token,
      refresh_token: thirdPartyTokens.refresh_token
    };

    saveAuthData(newAuthData);
  }
}


async function authFetch(input: RequestInfo, init?: RequestInit, retryOn401: boolean = true): Promise<Response> {
  const authData = getAuthData();

  if (!authData) {
    throw new Error("No auth data");
  }

  const headers = new Headers(init?.headers || {});
  headers.set('Authorization', `Bearer ${authData.access_token}`);

  const response = await fetch(input, {
    ...init,
    headers
  });

  if(response.status === 401) {
    const code = (await response.json()).code;

    if(code === "token_expired" && retryOn401) {
      await refreshAccessToken();
      return authFetch(input, init, false);
    }

    throw new Error("Unauthorized");
  }

  return response;
}

export async function testBackend() {
  const response = await authFetch("/api/hello");

  const name = await response.text();

  alert(`Hello ${name}`);
}

export async function getOrganisations(): Promise<Organisation[]> {
  const response = await authFetch("/api/organisations");

  const { organisations } = await response.json();

  return organisations;
}

export async function getPatients(organisation_id: string): Promise<Patient[]> {
  const response = await authFetch(`/api/organisations/${organisation_id}/patients`);

  const { patients } = await response.json();

  return patients;
}

export async function addPatient(organisation_id: string, name: string, date_of_birth: string): Promise<Patient> {
  const response = await authFetch(`/api/organisations/${organisation_id}/patients`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name, date_of_birth })
    });

    const patient = await response.json();

    return patient;
}

export async function deletePatient(organisation_id: string, id: string): Promise<void> {
  await authFetch(`/api/organisations/${organisation_id}/patients/${id}`, {
    method: 'DELETE'
  });
}

export async function updatePatient(organisation_id: string, patient: Patient): Promise<Patient> {
  const body = { ...patient };
  delete body.id;

  const response = await authFetch(`/api/organisations/${organisation_id}/patients/${patient.id}`, {
    method: 'PATCH',
    headers: {
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
  const response = await authFetch(`/api/organisations/${organisation_id}/share`, {
    method: 'POST',
    headers: {
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
  const response = await authFetch(`/api/invites/${invite_id}/details`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ token })
  });

  const { organisation_id, organisation_name, patient_count, users } = await response.json();

  return { organisation_id, organisation_name, patient_count, users };
}

export async function redeemInvite(invite_id: string, token: string) {
  await authFetch(`/api/invites/${invite_id}/redeem`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ token })
  });
}

export async function removeUserFromOrganisation(organisation_id: string, user_id: string) {
  await authFetch(`/api/organisations/${organisation_id}/users/${user_id}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json'
    },
  });
}
