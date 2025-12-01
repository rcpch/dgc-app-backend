import { useState, useRef } from "preact/hooks";

type CreateChildRowProps = {
  onSave: (name: string, date_of_birth: string) => void;
}

export function CreateChildRow({ onSave }: CreateChildRowProps) {
  const [name, setName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('1970-01-01');

  const formRef = useRef<HTMLFormElement>(null);

  function onSubmit(e: Event) {
    e.preventDefault();

    if(formRef.current!.reportValidity()) {
      onSave(name, dateOfBirth);
      setName('');
      setDateOfBirth('1970-01-01');
    }
  }

  return <tr key='create'>
      <td>
        <form onSubmit={onSubmit} ref={formRef}>
          <input
            required
            type="text"
            value={name}
            title="Name"
            placeholder="Name"
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