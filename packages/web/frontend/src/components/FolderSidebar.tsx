import { useState } from "react";
import type { Folder } from "../api/client";

interface Props {
  folders: Folder[];
  selectedId: number | null;
  onSelect: (id: number | null) => void;
  onCreate: () => void;
  loading: boolean;
  onDropMessage?: (messageId: number, folderId: number) => void;
  onReorder?: (order: number[]) => void;
}

export default function FolderSidebar({ folders, selectedId, onSelect, onCreate, loading, onDropMessage, onReorder }: Props) {
  const [dragOverId, setDragOverId] = useState<number | null>(null);
  const [reorderDragId, setReorderDragId] = useState<number | null>(null);

  const handleDragOver = (e: React.DragEvent, folderId: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDragOverId(folderId);
  };

  const handleDragLeave = () => {
    setDragOverId(null);
  };

  const handleDrop = (e: React.DragEvent, folderId: number) => {
    e.preventDefault();
    setDragOverId(null);
    try {
      const ids = JSON.parse(e.dataTransfer.getData("text/plain")) as number[];
      if (Array.isArray(ids) && onDropMessage) {
        ids.forEach((mid) => onDropMessage(mid, folderId));
        return;
      }
    } catch {}
    const raw = e.dataTransfer.getData("text/plain");
    const messageId = Number(raw);
    if (!isNaN(messageId) && onDropMessage) {
      onDropMessage(messageId, folderId);
    }
  };

  const handleFolderDragStart = (e: React.DragEvent, folderId: number) => {
    e.dataTransfer.setData("application/folder-id", String(folderId));
    e.dataTransfer.effectAllowed = "move";
    setReorderDragId(folderId);
  };

  const handleFolderDragOver = (e: React.DragEvent, folderId: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (reorderDragId !== null && reorderDragId !== folderId) {
      setDragOverId(folderId);
    }
  };

  const handleFolderDrop = (e: React.DragEvent, targetId: number) => {
    e.preventDefault();
    setDragOverId(null);
    setReorderDragId(null);
    const raw = e.dataTransfer.getData("application/folder-id");
    if (!raw || !onReorder) return;
    const draggedId = Number(raw);
    if (draggedId === targetId) return;
    const ids = folders.map((f) => f.id);
    const fromIdx = ids.indexOf(draggedId);
    const toIdx = ids.indexOf(targetId);
    if (fromIdx === -1 || toIdx === -1) return;
    ids.splice(fromIdx, 1);
    ids.splice(toIdx, 0, draggedId);
    onReorder(ids);
  };

  return (
    <div className="w-56 bg-white rounded shadow p-3 flex-shrink-0">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-bold text-gray-600 uppercase tracking-wide">Папки</h2>
        <button
          className="text-blue-600 hover:text-blue-800 text-lg leading-none"
          onClick={onCreate}
          title="Создать папку"
        >
          +
        </button>
      </div>

      {loading ? (
        <p className="text-xs text-gray-400">Загрузка...</p>
      ) : (
        <ul className="space-y-0.5">
          <li>
            <button
              className={`w-full text-left px-2 py-1.5 rounded text-sm flex items-center gap-2 ${selectedId === null ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-600 hover:bg-gray-50"}`}
              onClick={() => onSelect(null)}
            >
              <span className="w-3 h-3 rounded-full bg-gray-400 flex-shrink-0" />
              <span>Все сообщения</span>
            </button>
          </li>
          {folders.map((f) => (
            <li
              key={f.id}
              data-folder-id={f.id}
              draggable
              onDragStart={(e) => handleFolderDragStart(e, f.id)}
              onDragOver={(e) => {
                handleDragOver(e, f.id);
                handleFolderDragOver(e, f.id);
              }}
              onDragLeave={handleDragLeave}
              onDrop={(e) => {
                if (e.dataTransfer.types.includes("application/folder-id")) {
                  handleFolderDrop(e, f.id);
                } else {
                  handleDrop(e, f.id);
                }
              }}
            >
              <button
                className={`w-full text-left px-2 py-1.5 rounded text-sm flex items-center gap-2 ${selectedId === f.id ? "bg-blue-50 text-blue-700 font-medium" : dragOverId === f.id ? "bg-blue-100 ring-2 ring-blue-400" : "text-gray-600 hover:bg-gray-50"}`}
                onClick={() => onSelect(f.id)}
              >
                <span
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: f.color }}
                />
                <span className="flex-1 truncate">{f.name}</span>
                <span className="text-xs text-gray-400">{f.message_count}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
