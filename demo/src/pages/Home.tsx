import { useState, useEffect } from 'preact/hooks';
import * as client from 'openid-client';

import { getPatients, addPatient, deletePatient, updatePatient, testBackend, sharePatient, Patient } from '../api';

async function login() {
  const config = await client.discovery(
    new URL(import.meta.env.VITE_DEMO_OAUTH_SERVER),
    import.meta.env.VITE_DEMO_OAUTH_CLIENT_ID,
    {
      client_secret: import.meta.env.VITE_DEMO_OAUTH_CLIENT_SECRET,
    }
  );

  const code_verifier = client.randomPKCECodeVerifier();
  const code_challenge = await client.calculatePKCECodeChallenge(code_verifier);

  const state = client.randomState();

  const parameters = {
    redirect_uri: 'https://dgc-app-backend.localhost/demo/oauth-callback',
    scope: `${import.meta.env.VITE_DEMO_OAUTH_CLIENT_ID}/.default`,
    code_challenge,
    code_challenge_method: 'S256',
    state
  }

  const authUrl = client.buildAuthorizationUrl(config, parameters);

  sessionStorage['code_verifier'] = code_verifier;
  sessionStorage['state'] = state;

  window.location.href = authUrl.href;
}

export function Home() {
  const [token, setToken] = useState(localStorage.access_token);
  const [patients, setPatients] = useState<Patient[]>([]);
  
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState<string | null>(null);
  const [editingDateOfBirth, setEditingDateOfBirth] = useState<string | null>(null);

  useEffect(() => {
    if(token) {
      getPatients().then(setPatients);
    } else {
      setPatients([]);
    }
  }, [token]);

  const name = token ? JSON.parse(atob(token.split('.')[1])).unique_name : null;

  function onTestFormSubmit(e: Event) {
    e.preventDefault();
    testBackend();
  }

  async function onAddPatientFormSubmit(e: Event) {
    e.preventDefault();

    const name = (e.target as any).name.value;
    const date_of_birth = (e.target as any).date_of_birth.value;

    const patient = await addPatient(name, date_of_birth);
    setPatients([...patients, patient]);
  }

  function onLoginFormSubmit(e: Event) {
    e.preventDefault();
    if (token) {
      delete localStorage['access_token'];
      setToken('');
      setPatients([]);
    } else {
      login();
    }
  };

  async function onDeletePatient(id: string) {
    await deletePatient(id);
    setPatients(patients.filter(p => p.id !== id));
  }

  function onStartEditPatient(patient: Patient) {
    setEditingId(patient.id);
    setEditingName(patient.name);
    setEditingDateOfBirth(patient.date_of_birth);
  }

  function onCancelEditPatient() {
    setEditingId(null);
    setEditingName(null);
    setEditingDateOfBirth(null);
  }

  async function onSaveEditPatient(e: Event) {
    e.preventDefault();

    const patient = await updatePatient({
      id: editingId!,
      name: editingName!,
      date_of_birth: editingDateOfBirth!
    });

    setPatients(patients =>
      patients.map(p =>
        p.id === editingId ? patient : p
      )
    );

    setEditingId(null);
    setEditingName(null);
    setEditingBirthDate(null);
  }

  async function onSharePatient(id: string) {
    const token = await sharePatient(id);
    prompt("Share this link:", `${window.location.origin}/demo/share?token=${token}`);
  }

	return (
		<div id="app" class="container">
      {token ?
        <>  
          <h3 id="sub">
            {name ? `Logged in as: ${name}` : ''}
          </h3>
          <hr />
          <form onSubmit={onTestFormSubmit}>
            <input type="submit" value="Test Backend" />
          </form>
          <hr />
          <table>
            <thead>
              <tr>
                <td>Name</td>
                <td>Birth Date</td>
                <td></td>
              </tr>
            </thead>
            <tbody>
              {patients.map(patient => (
                <tr key={patient.id}>
                  <td>
                    {editingId === patient.id ? (
                      <form onSubmit={onSaveEditPatient}>
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
                    {editingId === patient.id ? (
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
                    {editingId === patient.id ? (
                      <>
                        <button onClick={onSaveEditPatient}>
                          Save
                        </button>
                        <button class="secondary" onClick={onCancelEditPatient}>
                          Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        <button onClick={() => onStartEditPatient(patient)}>
                          Edit
                        </button>
                        <button onClick={() => onSharePatient(patient.id)}>Share</button>
                        <button
                          class="pico-background-red"
                          onClick={() => onDeletePatient(patient.id)}>
                            Delete
                        </button>
                      </>
                    )}
                   </td>
                </tr>
              ))}
            </tbody>
          </table>
          <form onSubmit={onAddPatientFormSubmit}>
            <h4>Add new patient</h4>
            <input type="text" name="name" placeholder="Name" value="" required />
            <input type="date" name="date_of_birth" placeholder="Birth Date" value="1970-01-01" required />
            <input type="submit" value="Add Patient" />
          </form>
          <hr />
        </>
      : ''}
			<form onSubmit={onLoginFormSubmit}>
				<input type="submit" value={token ? 'Logout' : 'Login'} />
			</form>
			</div>
	);
}