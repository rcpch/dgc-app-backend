import { useState, useRef } from "preact/hooks";
import { Child, Organisation, Sex } from "../api";
import { organisationName } from "./ChildrenList";

type CreateChildRowProps = {
  organisations: Organisation[];
  onSave: (organisationId: string, child: Omit<Child, 'id' | 'organisation_ids'>) => void;
}

export function CreateChildRow({ organisations, onSave }: CreateChildRowProps) {
  const [name, setName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('1970-01-01');
  const [sex, setSex] = useState<Sex>('male');

  const [organisationId, setOrganisationId] = useState(organisations.length > 0 ? organisations[0].id : '');

  const formRef = useRef<HTMLFormElement>(null);

  function onOrganisationChange(e: Event) {
    const select = e.target as HTMLSelectElement;
    setOrganisationId(select.value);
  }

  function onSubmit(e: Event) {
    e.preventDefault();

    if(formRef.current!.reportValidity()) {
      onSave(organisationId, { name, date_of_birth: dateOfBirth, sex });
      setName('');
      setDateOfBirth('1970-01-01');
      setSex('male');
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
      <td>
        <select value={sex} onChange={e => setSex((e.target as HTMLSelectElement).value as Sex)}>
          <option value="male">Male</option>
          <option value="female">Female</option>
        </select>
      </td>
      <td>
        <select value={organisationId} onChange={onOrganisationChange}>
          {organisations.map(org => (
            <option key={org.id} value={org.id}>
              {organisationName(org)}
            </option>
          ))}
        </select>
      </td>
      <td style={{ display: 'flex', gap: '0.5em', justifyContent: 'flex-end' }}>
        <button onClick={onSubmit}>
          Save
        </button>
      </td>
    </tr>;
}