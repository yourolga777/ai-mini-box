type Col<T> = { key: string; label: string; render?: (row: T) => React.ReactNode };

export default function Table<T extends Record<string, unknown>>({
  cols,
  data,
  onDelete,
}: {
  cols: Col<T>[];
  data: T[];
  onDelete?: (row: T) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-200 text-left">
            {cols.map((c) => (
              <th key={c.key} className="p-2 font-medium">{c.label}</th>
            ))}
            {onDelete && <th className="p-2" />}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i} className="border-t hover:bg-gray-100">
              {cols.map((c) => (
                <td key={c.key} className="p-2">
                  {c.render ? c.render(row) : String(row[c.key] ?? "")}
                </td>
              ))}
              {onDelete && (
                <td className="p-2">
                  <button onClick={() => onDelete(row)} className="text-red-500 hover:underline text-xs">
                    Delete
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
