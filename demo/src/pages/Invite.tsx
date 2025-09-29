import { useState, useEffect } from "preact/hooks";
import { addSharedPatient, getInviteDetails, InviteDetails } from "../api";

const shareToken = new URL(window.location.href).searchParams.get("token")!;

async function onAddSharedPatient() {
  await addSharedPatient(shareToken);
  window.location.href = '/demo/';
}

export function Invite() {
  const [inviteDetails, setInviteDetails] = useState<InviteDetails | null>(null);

  useEffect(() => {
    const params = new URL(window.location.href).searchParams;

    const invite_id = params.get("invite_id")!;
    const token = params.get("token")!;

    getInviteDetails(invite_id, token).then(setInviteDetails);
  }, []);

  return (
    <div class="container">
      {inviteDetails ? (
        <div>
          <p>Invite to join {inviteDetails.organisation_name ?? inviteDetails.organisation_id} with {inviteDetails.patient_count} patients.</p>
          <p>{inviteDetails.users.map(user => user.name).join(", ")}</p>
          <button onClick={onAddSharedPatient}>Join</button>
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}