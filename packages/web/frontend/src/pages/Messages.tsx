import { useState, useMemo, useCallback, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, Link } from "react-router-dom";
import { api, type Folder } from "../api/client";
import Table from "../components/Table";
import FolderSidebar from "../components/FolderSidebar";
import FolderModal from "../components/FolderModal";

const TOPIC_COLORS: Record<string, string> = {
  Цены: "bg-green-100 text-green-700",
  Заказ: "bg-blue-100 text-blue-700",
  Жалоба: "bg-red-100 text-red-700",
  График: "bg-yellow-100 text-yellow-700",
  Другое: "bg-gray-100 text-gray-600",
};

const CATEGORY_COLORS: Record<string, string> = {
  ЗАКАЗ: "bg-blue-100 text-blue-700",
  ВОПРОС: "bg-green-100 text-green-700",
  ПРЕДЛОЖЕНИЕ: "bg-gray-100 text-gray-600",
  ЖАЛОБА: "bg-red-100 text-red-700",
  ФЛУД: "bg-orange-100 text-orange-700",
};

const SORTABLE_KEYS = new Set(["id", "topic", "text", "extracted_name", "source", "received_at"]);

function formatDate(d: string) {
  if (!d) return "";
  const dt = new Date(d);
  const dd = String(dt.getDate()).padStart(2, "0");
  const mm = String(dt.getMonth() + 1).padStart(2, "0");
  const yyyy = dt.getFullYear();
  const hh = String(dt.getHours()).padStart(2, "0");
  const mi = String(dt.getMinutes()).padStart(2, "0");
  return `${dd}.${mm}.${yyyy} ${hh}:${mi}`;
}

export default function Messages() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [selectedFolder, setSelectedFolder] = useState<number | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editFolder, setEditFolder] = useState<Folder | null>(null);
  const [rawSearch, setRawSearch] = useState("");
  const [search, setSearch] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const [sortKey, setSortKey] = useState<string>("id");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [massFolderId, setMassFolderId] = useState<number | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [linkingMsgId, setLinkingMsgId] = useState<number | null>(null);
  const [contactSearch, setContactSearch] = useState("");
  const [folderDropdownMsgId, setFolderDropdownMsgId] = useState<number | null>(null);
  const [categoryFilter, setCategoryFilter] = useState("");
  const contactSearchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setSearch(rawSearch);
      setSortKey("id");
      setSortDir("desc");
    }, 300);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [rawSearch]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && selectedIds.size > 0) {
        setSelectedIds(new Set());
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selectedIds]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.contact-dropdown, .folder-dropdown, [data-dropdown-btn]')) {
        setLinkingMsgId(null);
        setFolderDropdownMsgId(null);
      }
    };
    window.addEventListener("mousedown", handler);
    return () => window.removeEventListener("mousedown", handler);
  }, []);

  const queryKey = ["messages", selectedFolder, search, categoryFilter];
  const { data: msgs, isLoading } = useQuery({
    queryKey,
    queryFn: async () => {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (selectedFolder !== null) params.set("category_id", String(selectedFolder));
      if (categoryFilter) params.set("category", categoryFilter);
      return api.list<any>(`messages?${params.toString()}`);
    },
  });

  const { data: foldersData, isLoading: foldersLoading } = useQuery({
    queryKey: ["folders"],
    queryFn: async () => {
      try { return await api.listFolders(); }
      catch { return null; }
    },
    retry: false,
  });
  const folders = foldersData as Folder[] | null;

  const saveFolder = useMutation({
    mutationFn: (data: { name: string; description: string; color: string }) =>
      editFolder
        ? api.updateFolder(editFolder.id, data)
        : api.createFolder(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["folders"] });
      setShowModal(false);
      setEditFolder(null);
    },
  });

  const deleteFolderMut = useMutation({
    mutationFn: ({ id, mode }: { id: number; mode: "move" | "delete_messages" }) =>
      api.deleteFolder(id, mode),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["folders"] });
      setShowModal(false);
      setEditFolder(null);
    },
  });

  const dropAssignMut = useMutation({
    mutationFn: ({ messageId, folderId }: { messageId: number; folderId: number }) =>
      api.assignMessageCategory(messageId, folderId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["folders"] });
      qc.invalidateQueries({ queryKey: ["messages"] });
    },
  });

  const batchAssignMut = useMutation({
    mutationFn: (folderId: number) =>
      api.batchAssignCategories({ message_ids: [...selectedIds], category_id: folderId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["folders"] });
      qc.invalidateQueries({ queryKey: ["messages"] });
      setSelectedIds(new Set());
      setMassFolderId(null);
      setToast(`Назначено ${selectedIds.size} сообщений`);
    },
    onError: () => {
      setToast("Ошибка при назначении");
    },
  });

  const assignAllMut = useMutation({
    mutationFn: (limit: number) => api.assignAllCategories(limit),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["folders"] });
      qc.invalidateQueries({ queryKey: ["messages"] });
      setToast(`✅ Обработано: ${data.checked}, назначено в папки: ${data.assigned}`);
    },
    onError: (err: any) => {
      const detail = err?.message ?? "";
      if (detail.includes("AutoProcessor")) {
        setToast("❌ ИИ-плагин не запущен. Включите его в разделе «Плагины».");
      } else {
        setToast("❌ Ошибка при распределении");
      }
    },
  });

  const { data: foundContacts } = useQuery({
    queryKey: ["contact-search", contactSearch],
    queryFn: () => api.list<any>(`contacts?search=${encodeURIComponent(contactSearch)}`),
    enabled: contactSearch.length > 0,
  });

  const linkContactMut = useMutation({
    mutationFn: ({ messageId, contactId }: { messageId: number; contactId: number }) =>
      fetch(`/api/messages/${messageId}/contact`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contact_id: contactId }),
      }).then((r) => { if (!r.ok) throw new Error("Failed to link"); return r.json(); }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["messages"] });
      setLinkingMsgId(null);
      setContactSearch("");
    },
  });

  const reorderFoldersMut = useMutation({
    mutationFn: (order: number[]) => api.reorderFolders(order),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["folders"] });
    },
  });

  const handleSort = useCallback((key: string) => {
    if (!SORTABLE_KEYS.has(key)) return;
    setSortDir((prev) => (sortKey === key && prev === "asc" ? "desc" : "asc"));
    setSortKey(key);
  }, [sortKey]);

  const handleCheck = useCallback((id: number, checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  }, []);

  const handleDrop = useCallback((messageId: number, folderId: number) => {
    dropAssignMut.mutate({ messageId, folderId });
  }, [dropAssignMut]);

  const sorted = useMemo(() => {
    const items = msgs ?? [];
    if (!sortKey) return items;
    return [...items].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [msgs, sortKey, sortDir]);

  const cols = [
    { key: "id", label: "#" },
    {
      key: "topic",
      label: "Тема",
      render: (r: any) =>
        r.topic ? (
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded ${TOPIC_COLORS[r.topic] ?? "bg-gray-100 text-gray-600"}`}
          >
            {r.topic}
          </span>
        ) : null,
    },
    {
      key: "category",
      label: "Категория",
      render: (r: any) => (
        <div className="flex items-center gap-1 flex-wrap">
          {r.category ? (
            <span className={`text-xs font-medium px-2 py-0.5 rounded ${CATEGORY_COLORS[r.category] ?? "bg-gray-100 text-gray-600"}`}>
              {r.category}
            </span>
          ) : null}
          {r.need_human ? (
            <span className="text-xs text-red-600 font-medium" title="Требует оператора">👤</span>
          ) : null}
          {r.auto_replied ? (
            <span className="text-xs text-green-600 font-medium" title="Автоответ">🤖</span>
          ) : null}
        </div>
      ),
    },
    {
      key: "text",
      label: "Текст",
      render: (r: any) => (r.text as string).slice(0, 60),
    },
    { key: "extracted_name", label: "Имя" },
    { key: "extracted_phone", label: "Телефон" },
    {
      key: "contact",
      label: "Контакт",
      render: (r: any) => {
        if (r.contact_id) {
          return <Link to={`/contacts/${r.contact_id}`} className="text-blue-600 text-xs underline">#{r.contact_id}</Link>;
        }
        return (
          <div className="relative contact-dropdown" onClick={(e) => e.stopPropagation()}>
            <button
              data-dropdown-btn="contact"
              className={`text-xs px-2 py-0.5 rounded ${linkingMsgId === r.id ? "bg-gray-200 text-gray-400" : "bg-blue-100 text-blue-700 hover:bg-blue-200"}`}
              onClick={() => { setLinkingMsgId(r.id); setContactSearch(""); }}
            >
              Привязать
            </button>
            {linkingMsgId === r.id && (
              <div className="absolute z-20 top-full left-0 mt-1 bg-white border rounded shadow-md w-64">
                <input
                  ref={contactSearchRef}
                  className="w-full border-b px-2 py-1.5 text-sm outline-none"
                  placeholder="Поиск контакта…"
                  value={contactSearch}
                  onChange={(e) => setContactSearch(e.target.value)}
                  autoFocus
                />
                <ul className="max-h-40 overflow-y-auto">
                  {(foundContacts ?? []).length === 0 && contactSearch.length > 0 && (
                    <li className="px-2 py-1.5 text-xs text-gray-400">Ничего не найдено</li>
                  )}
                  {(foundContacts ?? []).map((c: any) => (
                    <li
                      key={c.id}
                      className="px-2 py-1.5 text-sm hover:bg-blue-50 cursor-pointer"
                      onClick={() => linkContactMut.mutate({ messageId: r.id, contactId: c.id })}
                    >
                      {c.name} {c.phone && <span className="text-gray-400">({c.phone})</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );
      },
    },
    {
      key: "folder",
      label: "Папка",
      render: (r: any) => (
        <div className="relative folder-dropdown" onClick={(e) => e.stopPropagation()}>
          <button
            data-dropdown-btn="folder"
            className="text-xs text-gray-500 hover:text-gray-700"
            onClick={() => setFolderDropdownMsgId(folderDropdownMsgId === r.id ? null : r.id)}
          >
            📁
          </button>
          {folderDropdownMsgId === r.id && folders && (
            <div className="absolute z-20 top-full left-0 mt-1 bg-white border rounded shadow-md w-48">
              {folders.length === 0 ? (
                <div className="px-2 py-1.5 text-xs text-gray-400">Нет папок</div>
              ) : (
                <ul className="max-h-40 overflow-y-auto">
                  {folders.map((f) => (
                    <li
                      key={f.id}
                      className="px-2 py-1.5 text-sm hover:bg-blue-50 cursor-pointer flex items-center gap-2"
                      onClick={() => {
                        dropAssignMut.mutate({ messageId: r.id, folderId: f.id });
                        setFolderDropdownMsgId(null);
                      }}
                    >
                      <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: f.color }} />
                      {f.name}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      ),
    },
    {
      key: "sent_response",
      label: "Отправлено",
      render: (r: any) =>
        r.sent_response ? (
          <span className="text-green-600 text-xs font-medium">Да</span>
        ) : (
          <span className="text-gray-400 text-xs">Нет</span>
        ),
    },
    {
      key: "received_at",
      label: "Дата",
      render: (r: any) => formatDate(r.received_at),
    },
    { key: "source", label: "Источник" },
  ];

  const getRowId = useCallback((r: any) => r.id, []);

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Сообщения</h1>
      <div className="flex gap-4">
        {folders && (
          <FolderSidebar
            folders={folders}
            selectedId={selectedFolder}
            onSelect={(id) => setSelectedFolder(id)}
            onCreate={() => { setEditFolder(null); setShowModal(true); }}
            loading={foldersLoading}
            onDropMessage={handleDrop}
            onReorder={(order) => reorderFoldersMut.mutate(order)}
          />
        )}
        <div className="flex-1 min-w-0">
          <div className="mb-3 flex items-center gap-2">
            <input
              className="flex-1 border rounded px-3 py-2 text-sm"
              placeholder="Поиск по тексту сообщения…"
              value={rawSearch}
              onChange={(e) => setRawSearch(e.target.value)}
            />
            <button
              className="bg-purple-600 text-white px-3 py-2 rounded text-sm hover:bg-purple-700 disabled:opacity-50 whitespace-nowrap"
              onClick={() => assignAllMut.mutate(50)}
              disabled={assignAllMut.isPending}
            >
              {assignAllMut.isPending ? "Распределяю…" : "Распределить всё"}
            </button>
            <select
              className="text-sm border rounded px-2 py-1.5"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="">Все категории</option>
              <option value="ЗАКАЗ">ЗАКАЗ</option>
              <option value="ВОПРОС">ВОПРОС</option>
              <option value="ПРЕДЛОЖЕНИЕ">ПРЕДЛОЖЕНИЕ</option>
              <option value="ЖАЛОБА">ЖАЛОБА</option>
              <option value="ФЛУД">ФЛУД</option>
            </select>
            {selectedIds.size >= 2 && folders && (
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-500">{selectedIds.size} выбр.</span>
                <select
                  className="text-xs border rounded px-2 py-1.5"
                  value={massFolderId ?? ""}
                  disabled={batchAssignMut.isPending}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val) {
                      const fid = Number(val);
                      setMassFolderId(fid);
                      batchAssignMut.mutate(fid);
                    }
                  }}
                >
                  <option value="">Назначить папку</option>
                  {folders.map((f) => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </select>
                {batchAssignMut.isPending && (
                  <span className="text-xs text-blue-600">назначение…</span>
                )}
              </div>
            )}
          </div>
          {isLoading ? (
            <p>Загрузка…</p>
          ) : (
            <Table
              cols={cols}
              data={sorted}
              onClickRow={(r) => navigate(`/messages/${r.id}`)}
              sortKey={sortKey}
              sortDir={sortDir}
              onSort={handleSort}
              onCheckChange={handleCheck}
              checkedIds={selectedIds}
              getRowId={getRowId}
              enableDrag
              onDragStart={getRowId}
              onTouchDrop={(ids, folderId) => {
                ids.forEach((mid) => dropAssignMut.mutate({ messageId: mid, folderId }));
              }}
            />
          )}
        </div>
      </div>

      {toast && (
        <div className="fixed bottom-4 right-4 bg-gray-800 text-white px-4 py-2 rounded shadow text-sm z-50 animate-fade-in">
          {toast}
          <button className="ml-3 text-gray-300 hover:text-white" onClick={() => setToast(null)}>&times;</button>
        </div>
      )}
      {showModal && (
        <FolderModal
          folder={editFolder}
          onSave={(data) => saveFolder.mutate(data)}
          onClose={() => { setShowModal(false); setEditFolder(null); }}
          saving={saveFolder.isPending}
          onDelete={(id, mode) => deleteFolderMut.mutate({ id, mode })}
          deleting={deleteFolderMut.isPending}
        />
      )}
    </div>
  );
}