import { useState } from "preact/hooks";
import { addSharedPatient } from "../api";

async function onAddSharedPatient() {
  await addSharedPatient(new URL(window.location.href).searchParams.get("token")!);
  window.location.href = '/demo/';
}

export function Share() {
  const [token, setToken] = useState(localStorage.access_token);

  return (
    <div class="container">
      <button onClick={onAddSharedPatient}>Add Patient</button>
    </div>
  );
}