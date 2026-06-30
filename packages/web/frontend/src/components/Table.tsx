import { useRef } from "react";

type Col = { key: string; label: string; render?: (row: any) => React.ReactNode };

export default function Table({
  cols,
  data,
  onDelete,
  onEdit,
  onClickRow,
  sortKey,
  sortDir,
  onSort,
  onCheckChange,
  checkedIds,
  getRowId,
  enableDrag,
  onDragStart,
  onTouchDrop,
}: {
  cols: Col[];
  data: any[];
  onDelete?: (row: any) => void;
  onEdit?: (row: any) => void;
  onClickRow?: (row: any) => void;
  sortKey?: string;
  sortDir?: "asc" | "desc";
  onSort?: (key: string) => void;
  onCheckChange?: (id: number, checked: boolean) => void;
  checkedIds?: Set<number>;
  getRowId?: (row: any) => number;
  enableDrag?: boolean;
  onDragStart?: (row: any) => string | number;
  onTouchDrop?: (ids: number[], folderId: number) => void;
}) {
  const actions = onDelete || onEdit;
  const hasCheckbox = !!onCheckChange && !!getRowId;
  const hasDrag = enableDrag && !!getRowId;
  const touchDragRef = useRef<{ ids: number[]; el: HTMLDivElement } | null>(null);

  const allChecked = hasCheckbox && data.length > 0 && data.every((r) => checkedIds?.has(getRowId!(r)));

  const handleTouchStart = (rowId: number, e: React.TouchEvent) => {
    if (!hasDrag || !onTouchDrop) return;
    const touch = e.touches[0];
    const ids = checkedIds && checkedIds.size >= 2 && checkedIds.has(rowId)
      ? [...checkedIds] : [rowId];

    const el = document.createElement("div");
    el.textContent = ids.length > 1 ? `${ids.length} сообщений` : `#${rowId}`;
    el.style.cssText = "position:fixed;pointer-events:none;background:rgba(59,130,246,0.9);color:#fff;padding:4px 8px;border-radius:6px;font-size:12px;z-index:9999";
    el.style.left = `${touch.clientX + 10}px`;
    el.style.top = `${touch.clientY - 20}px`;
    document.body.appendChild(el);
    touchDragRef.current = { ids, el };
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!touchDragRef.current) return;
    const touch = e.touches[0];
    touchDragRef.current.el.style.left = `${touch.clientX + 10}px`;
    touchDragRef.current.el.style.top = `${touch.clientY - 20}px`;

    const el = document.elementFromPoint(touch.clientX, touch.clientY);
    const folderLi = el?.closest("[data-folder-id]");
    const fid = folderLi ? Number((folderLi as HTMLElement).dataset.folderId) : null;
    document.querySelectorAll("[data-folder-id]").forEach((li) => {
      (li as HTMLElement).style.outline = Number((li as HTMLElement).dataset.folderId) === fid
        ? "2px solid #3b82f6" : "";
    });
  };

  const handleTouchEnd = () => {
    if (!touchDragRef.current || !onTouchDrop) return;
    touchDragRef.current.el.remove();
    const el = document.elementFromPoint(
      parseInt(touchDragRef.current.el.style.left) - 10,
      parseInt(touchDragRef.current.el.style.top) + 20,
    );
    const folderLi = el?.closest("[data-folder-id]");
    if (folderLi) {
      const fid = Number((folderLi as HTMLElement).dataset.folderId);
      onTouchDrop(touchDragRef.current.ids, fid);
    }
    document.querySelectorAll("[data-folder-id]").forEach((li) => {
      (li as HTMLElement).style.outline = "";
    });
    touchDragRef.current = null;
  };

  return (
    <div className="overflow-x-auto" onTouchMove={handleTouchMove} onTouchEnd={handleTouchEnd}>
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-200 text-left">
            {hasCheckbox && (
              <th className="p-2 w-8">
                <input
                  type="checkbox"
                  checked={allChecked}
                  onChange={() => {
                    if (!onCheckChange || !getRowId) return;
                    if (allChecked) {
                      data.forEach((r) => onCheckChange(getRowId(r), false));
                    } else {
                      data.forEach((r) => onCheckChange(getRowId(r), true));
                    }
                  }}
                />
              </th>
            )}
            {cols.map((c) => (
              <th
                key={c.key}
                className={`p-2 font-medium ${onSort ? "cursor-pointer select-none hover:bg-gray-300" : ""}`}
                onClick={() => onSort?.(c.key)}
              >
                {c.label}
                {sortKey === c.key && (
                  <span className="ml-1 text-xs">{sortDir === "asc" ? "▲" : "▼"}</span>
                )}
              </th>
            ))}
            {actions && <th className="p-2" />}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => {
            const rowId = getRowId ? getRowId(row) : i;
            return (
              <tr
                key={i}
                className={`border-t hover:bg-gray-100 ${onClickRow ? "cursor-pointer" : ""}`}
                onClick={() => onClickRow?.(row)}
                draggable={hasDrag}
                onDragStart={(e) => {
                  if (!hasDrag || !onDragStart) return;
                  const ids = checkedIds && checkedIds.size >= 2 && checkedIds.has(rowId)
                    ? [...checkedIds] : [Number(onDragStart(row))];
                  e.dataTransfer.setData("text/plain", JSON.stringify(ids));

                  const canvas = document.createElement("canvas");
                  canvas.width = 200;
                  canvas.height = 40;
                  const ctx = canvas.getContext("2d")!;
                  ctx.fillStyle = "rgba(59,130,246,0.9)";
                  ctx.beginPath();
                  ctx.roundRect(0, 0, 200, 40, 6);
                  ctx.fill();
                  ctx.fillStyle = "#fff";
                  ctx.font = "14px sans-serif";
                  ctx.fillText(ids.length > 1 ? `${ids.length} сообщений` : `#${ids[0]}`, 10, 26);
                  e.dataTransfer.setDragImage(canvas, 10, 10);
                  e.dataTransfer.effectAllowed = "copy";
                }}
                onTouchStart={(e) => handleTouchStart(rowId, e)}
              >
                {hasCheckbox && (
                  <td className="p-2" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={checkedIds?.has(rowId) ?? false}
                      onChange={() => onCheckChange?.(rowId, !checkedIds?.has(rowId))}
                    />
                  </td>
                )}
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
                        Редакт.
                      </button>
                    )}
                    {onDelete && (
                      <button
                        onClick={(e) => { e.stopPropagation(); onDelete(row); }}
                        className="text-red-500 hover:underline text-xs"
                      >
                        Удалить
                      </button>
                    )}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
