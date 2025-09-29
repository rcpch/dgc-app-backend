import { useState, useEffect } from "preact/hooks";
import { redeemInvite, getInviteDetails, InviteDetails } from "../api";

const params = new URL(window.location.href).searchParams;

const invite_id = params.get("invite_id")!;
const token = params.get("token")!;

export function Invite() {
  const [inviteDetails, setInviteDetails] = useState<InviteDetails | null>(null);

  useEffect(() => {
    getInviteDetails(invite_id, token).then(setInviteDetails);
  }, []);

  async function onAddSharedPatient() {
    await redeemInvite(invite_id, token);
    window.location.href = '/demo/';
  }

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