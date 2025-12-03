import { useState, useRef } from "preact/hooks";
import { ObservationType } from "../api";

type CreateObservationRowProps = {
  onSave: (observationDate: Date, observationType: ObservationType, observationValue: number) => void;
}

export function CreateObservationRow({ onSave }: CreateObservationRowProps) {
  const [observationDate, setObservationDate] = useState('1971-01-01');
  const [observationType, setObservationType] = useState<ObservationType>('height');
  const [observationValue, setObservationValue] = useState(70.0);

  const formRef = useRef<HTMLFormElement>(null);

  function onSubmit(e: Event) {
    e.preventDefault();

    if(formRef.current!.reportValidity()) {
      onSave(new Date(observationDate), observationType, observationValue);
      setObservationDate('1971-01-01');
    }
  }

  return <tr key='create'>
      <td>
        <input
          type="date"
          value={observationDate}
          onChange={e => setObservationDate((e.target as HTMLInputElement).value)}
        />
      </td>
      <td>
        <select
          value={observationType}
          onChange={e => setObservationType((e.target as HTMLSelectElement).value as ObservationType)}>
          <option value="height">Height</option>
          <option value="weight">Weight</option>
          <option value="ofc">Head Circumference</option>
        </select>
      </td>
      <td>
        <form onSubmit={onSubmit} ref={formRef}>
              <input
                type="number"
                step="0.01"
                value={observationValue}
                onChange={e => setObservationValue(parseFloat((e.target as HTMLInputElement).value))}
              />
        </form>
      </td>
       <td>
        <button onClick={onSubmit}>
          Add
        </button>
      </td>
    </tr>;
}