import { useState, useEffect } from "react";
import type { Folder } from "../api/client";

const COLORS = [
  "#2563eb", "#16a34a", "#dc2626", "#ca8a04", "#8b5cf6", "#ec4899",
  "#f97316", "#14b8a6", "#6366f1", "#84cc16", "#06b6d4", "#e11d48",
];

interface Props {
  folder?: Folder | null;
  onSave: (data: { name: string; description: string; color: string }) => void;
  onClose: () => void;
  saving?: boolean;
  onDelete?: (id: number, mode: "move" | "delete_messages") => void;
  deleting?: boolean;
}

export default function FolderModal({ folder, onSave, onClose, saving, onDelete, deleting }: Props) {
  const [name, setName] = useState(folder?.name ?? "");
  const [description, setDescription] = useState(folder?.description ?? "");
  const [color, setColor] = useState(folder?.color ?? COLORS[0]);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleteMode, setDeleteMode] = useState<"move" | "delete_messages">("move");

  useEffect(() => {
    if (folder) {
      setName(folder.name);
      setDescription(folder.description);
      setColor(folder.color);
    }
  }, [folder]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    onSave({ name: name.trim(), description: description.trim(), color });
  };

  const isSystem = folder?.is_system;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold">{folder ? "Редактировать папку" : "Создать папку"}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Название</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm"
              placeholder="Название папки"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              maxLength={50}
              disabled={isSystem}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
            <textarea
              className="w-full border rounded px-3 py-2 text-sm"
              rows={2}
              placeholder="Описание папки (необязательно)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Цвет</label>
            <div className="flex flex-wrap gap-2">
              {COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  className={`w-7 h-7 rounded-full border-2 ${color === c ? "border-gray-800 ring-2 ring-offset-1 ring-gray-400" : "border-transparent"}`}
                  style={{ backgroundColor: c }}
                  onClick={() => setColor(c)}
                />
              ))}
            </div>
          </div>

          <div className="flex justify-between items-center pt-2">
            <div>
              {folder && onDelete && !isSystem && !confirmDelete && (
                <button
                  type="button"
                  className="text-red-500 text-xs hover:text-red-700"
                  onClick={() => setConfirmDelete(true)}
                >
                  Удалить папку
                </button>
              )}
              {folder && confirmDelete && (
                <div className="flex items-center gap-2">
                  <select
                    className="text-xs border rounded px-1 py-0.5"
                    value={deleteMode}
                    onChange={(e) => setDeleteMode(e.target.value as any)}
                  >
                    <option value="move">Перенести во входящие</option>
                    <option value="delete_messages">Удалить сообщения</option>
                  </select>
                  <button
                    type="button"
                    className="text-xs text-red-600 font-medium hover:text-red-800"
                    disabled={deleting}
                    onClick={() => onDelete?.(folder.id, deleteMode)}
                  >
                    {deleting ? "Удаление..." : "Подтвердить"}
                  </button>
                  <button
                    type="button"
                    className="text-xs text-gray-500"
                    onClick={() => setConfirmDelete(false)}
                  >
                    Отмена
                  </button>
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                className="px-4 py-2 rounded text-sm text-gray-600 hover:bg-gray-100"
                onClick={onClose}
              >
                Отмена
              </button>
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                disabled={!name.trim() || saving}
              >
                {saving ? "Сохранение..." : folder ? "Сохранить" : "Создать"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}