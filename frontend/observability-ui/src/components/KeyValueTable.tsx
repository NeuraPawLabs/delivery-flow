type Entry = {
  label: string;
  value: string | number | null | undefined;
};

type KeyValueTableProps = {
  entries: Entry[];
};

export function KeyValueTable({ entries }: KeyValueTableProps) {
  return (
    <table className="key-value-table">
      <tbody>
        {entries.map((entry) => (
          <tr key={entry.label}>
            <th>{entry.label}</th>
            <td>{entry.value ?? "n/a"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
