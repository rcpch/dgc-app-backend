import { useState } from "preact/hooks";

type CreatePatientRowProps = {
  onSave: (name: string, date_of_birth: string) => void;
}

export function CreatePatientRow({ onSave }: CreatePatientRowProps) {
  const [name, setName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('1970-01-01');

  function onSubmit(e: Event) {
    e.preventDefault();
    onSave(name, dateOfBirth);
    setName('');
    setDateOfBirth('1970-01-01');
  }

  return <tr key='create'>
    <td>
      <form onSubmit={onSubmit}>
        <input
          type="text"
          value={name}
          onChange={e => setName((e.target as HTMLInputElement).value)}
        />
      </form>
    </td>
    <td>
       <input
        type="date"
        value={dateOfBirth}
        onChange={e => setDateOfBirth((e.target as HTMLInputElement).value)}
      />
    </td>
    <td style={{ display: 'flex', gap: '0.5em', justifyContent: 'flex-end' }}>
      <button onClick={onSubmit}>
        Save
      </button>
    </td>
  </tr>;
}