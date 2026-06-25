type Col = { key: string; label: string; render?: (row: any) => React.ReactNode };

export default function Table({
  cols,
  data,
  onDelete,
  onEdit,
  onClickRow,
}: {
  cols: Col[];
  data: any[];
  onDelete?: (row: any) => void;
  onEdit?: (row: any) => void;
  onClickRow?: (row: any) => void;
}) {
  const actions = onDelete || onEdit;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-200 text-left">
            {cols.map((c) => (
              <th key={c.key} className="p-2 font-medium">{c.label}</th>
            ))}
            {actions && <th className="p-2" />}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={i}
              className={`border-t hover:bg-gray-100 ${onClickRow ? "cursor-pointer" : ""}`}
              onClick={() => onClickRow?.(row)}
            >
              {cols.map((c) => (
                <td key={c.key} className="p-2">
                  {c.render ? c.render(row) : String(row[c.key] ?? "")}
                </td>
              ))}
              {actions && (
                <td className="p-2 flex gap-2">
                  {onEdit && (
                    <button
                      onClick={(e) => { e.stopPropagation(); onEdit(row); }}
                      className="text-blue-600 hover:underline text-xs"
                    >
                      Edit
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={(e) => { e.stopPropagation(); onDelete(row); }}
                      className="text-red-500 hover:underline text-xs"
                    >
                      Delete
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
