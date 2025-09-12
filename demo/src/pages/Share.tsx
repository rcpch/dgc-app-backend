import { useState, useEffect } from "preact/hooks";
import { addSharedPatient, getShareDetails, ShareDetails } from "../api";

const shareToken = new URL(window.location.href).searchParams.get("token")!;

async function onAddSharedPatient() {
  await addSharedPatient(shareToken);
  window.location.href = '/demo/';
}

export function Share() {
  const [shareDetails, setShareDetails] = useState<ShareDetails | null>(null);

  useEffect(() => {
    getShareDetails(shareToken).then(setShareDetails);
  }, []);

  return (
    <div class="container">
      {shareDetails ? (
        <div>
          <p>{shareDetails.sharer_name} has shared a patient with you: {shareDetails.patient_name}</p>
          <button onClick={onAddSharedPatient}>Add Patient</button>
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}