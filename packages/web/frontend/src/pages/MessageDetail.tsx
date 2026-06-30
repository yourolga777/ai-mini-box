import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { api, type Folder } from "../api/client";
import { formatPrice, statusLabel } from "../helpers";
import TemplateSelector from "../components/TemplateSelector";

interface Message {
  id: number;
  source: string;
  chat_id: string | null;
  contact_id: number | null;
  text: string;
  topic: string | null;
  extracted_phone: string | null;
  extracted_name: string | null;
  draft_response: string | null;
  sent_response: boolean;
  received_at: string;
  category: string | null;
  subcategory: string | null;
  need_human: boolean;
  auto_replied: boolean;
  auto_reply_text: string | null;
  operator_context: string | null;
}

interface FolderAssign {
  category_id: number;
  category_name: string;
  color: string;
}

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

export default function MessageDetail() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [replyText, setReplyText] = useState("");
  const [saveToKb, setSaveToKb] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [contactSearch, setContactSearch] = useState("");
  const [showContactDropdown, setShowContactDropdown] = useState(false);

  const { data: msg, isLoading } = useQuery({
    queryKey: ["message", id],
    queryFn: () => api.get<Message>("messages", Number(id)),
  });

  const { data: contact } = useQuery({
    queryKey: ["contact", msg?.contact_id],
    queryFn: () => api.get<any>("contacts", msg!.contact_id!),
    enabled: !!msg?.contact_id,
  });

  const { data: foundContacts } = useQuery({
    queryKey: ["contact-search", contactSearch],
    queryFn: () => api.list<any>(`contacts?search=${encodeURIComponent(contactSearch)}`),
    enabled: contactSearch.length > 0,
  });

  const { data: folders } = useQuery({
    queryKey: ["folders"],
    queryFn: async () => {
      try { return await api.listFolders(); }
      catch { return null; }
    },
    retry: false,
  });
  const folderList = folders as Folder[] | null;

  const { data: msgFolderIds } = useQuery({
    queryKey: ["msg-folders", id],
    queryFn: async () => {
      const cats = await api.getMessageCategories(Number(id));
      return cats.map((c: any) => ({ category_id: c.id, category_name: c.name, color: c.color }));
    },
    enabled: !!id,
  });

  const [showCreateOrder, setShowCreateOrder] = useState(false);
  const [orderTotal, setOrderTotal] = useState("");
  const [orderNotes, setOrderNotes] = useState("");

  const mid = Number(id);

  const assignMut = useMutation({
    mutationFn: (folderId: number) => api.assignMessageCategory(mid, folderId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["msg-folders", id] }),
  });

  const unassignMut = useMutation({
    mutationFn: (folderId: number) => api.unassignMessageCategory(mid, folderId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["msg-folders", id] }),
  });

  const linkContactMut = useMutation({
    mutationFn: (contactId: number) =>
      fetch(`/api/messages/${id}/contact`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contact_id: contactId }),
      }).then((r) => { if (!r.ok) throw new Error("Failed to link"); return r.json(); }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["message", id] });
      qc.invalidateQueries({ queryKey: ["contact"] });
      setShowContactDropdown(false);
      setContactSearch("");
    },
  });

  const { data: linkedOrder } = useQuery({
    queryKey: ["message-order", id],
    queryFn: () => api.getMessageOrder(mid),
    enabled: !!id,
  });

  const createOrderMut = useMutation({
    mutationFn: (data: { total_kopecks: number; notes: string }) =>
      api.createOrder(mid, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["message-order", id] });
      setShowCreateOrder(false);
      setOrderTotal("");
      setOrderNotes("");
    },
  });

  const sendReply = useMutation({
    mutationFn: (body: { text: string; save_to_kb: boolean }) =>
      fetch(`/api/messages/${id}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }).then((r) => r.json()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["message", id] });
      qc.invalidateQueries({ queryKey: ["messages"] });
      qc.invalidateQueries({ queryKey: ["knowledge-base"] });
      if (selectedTemplateId) {
        const edited = replyText !== (msg?.draft_response ?? "");
        templateUseMut.mutate({ template_id: selectedTemplateId, operator_edited: edited });
      }
      setReplyText("");
      setSaveToKb(false);
      setSelectedTemplateId(null);
    },
  });

  const reprocessMut = useMutation({
    mutationFn: () => api.reprocessMessage(mid),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["message", id] });
    },
  });

  const templateUseMut = useMutation({
    mutationFn: (data: { template_id: string; operator_edited: boolean }) =>
      api.useTemplate(data.template_id, {
        message_id: String(mid),
        operator_approved: !data.operator_edited,
        operator_edited: data.operator_edited,
        final_text: replyText || undefined,
      }),
  });

  const [toast, setToast] = useState<string | null>(null);

  if (isLoading) return <p>Загрузка…</p>;
  if (!msg) return <p>Сообщение не найдено.</p>;

  const topicColor = TOPIC_COLORS[msg.topic ?? ""] ?? "bg-gray-100 text-gray-600";
  const unassignedFolders = folderList
    ? folderList.filter((f) => !(msgFolderIds ?? []).some((a: FolderAssign) => a.category_id === f.id))
    : [];

  return (
    <div>
      <Link to="/messages" className="text-blue-600 text-sm">
        &larr; Назад к сообщениям
      </Link>

      <div className="bg-white rounded shadow p-4 mt-2 mb-4">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-lg font-bold">
            Сообщение №{msg.id}
          </h1>
          <div className="flex items-center gap-2">
            {msg.category && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded ${CATEGORY_COLORS[msg.category] ?? "bg-gray-100 text-gray-600"}`}>
                {msg.category}{msg.subcategory ? ` / ${msg.subcategory}` : ""}
              </span>
            )}
            {msg.topic && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded ${topicColor}`}>
                {msg.topic}
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm mb-4">
          <div>
            <span className="text-gray-500">Источник:</span> {msg.source}
          </div>
          {msg.extracted_name && (
            <div>
              <span className="text-gray-500">Имя:</span> {msg.extracted_name}
            </div>
          )}
          {msg.extracted_phone && (
            <div>
              <span className="text-gray-500">Телефон:</span> {msg.extracted_phone}
            </div>
          )}
          {msg.chat_id && (
            <div>
              <span className="text-gray-500">ID чата:</span> {msg.chat_id}
            </div>
          )}

          {msg.contact_id && contact ? (
            <div className="col-span-2">
              <span className="text-gray-500">Контакт:</span>{" "}
              <Link to={`/contacts/${contact.id}`} className="text-blue-600 underline">
                {contact.name}
              </Link>
            </div>
          ) : !msg.contact_id && (
            <div className="col-span-2 relative">
              <span className="text-gray-500">Контакт:</span>{" "}
              <button
                className="text-blue-600 text-xs underline ml-1"
                onClick={() => setShowContactDropdown(!showContactDropdown)}
              >
                Привязать к контакту
              </button>
              {showContactDropdown && (
                <div className="absolute z-10 top-full left-0 mt-1 bg-white border rounded shadow-md w-72">
                  <input
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
                        onClick={() => linkContactMut.mutate(c.id)}
                      >
                        {c.name} {c.phone && <span className="text-gray-400">({c.phone})</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {linkContactMut.error && (
                <span className="text-red-600 text-xs ml-2">
                  Ошибка: {(linkContactMut.error as any).message}
                </span>
              )}
            </div>
          )}

          <div>
            <span className="text-gray-500">Дата:</span>{" "}
            {formatDate(msg.received_at)}
          </div>
          <div>
            <span className="text-gray-500">Отправлено:</span>{" "}
            {msg.sent_response ? "Да" : "Нет"}
          </div>
        </div>

        {msg.auto_replied && msg.auto_reply_text && (
          <div className="bg-green-50 border border-green-200 rounded p-3 mb-4">
            <div className="text-sm font-medium text-green-700 mb-1">🤖 Автоматический ответ отправлен</div>
            <div className="text-sm text-green-600 whitespace-pre-wrap">{msg.auto_reply_text}</div>
          </div>
        )}

        {msg.need_human && (
          <div className="bg-red-50 border border-red-200 rounded p-3 mb-4">
            <div className="text-sm font-medium text-red-700">👤 Требует внимания оператора</div>
            {msg.operator_context && (
              <div className="text-xs text-red-500 mt-1">{msg.operator_context}</div>
            )}
          </div>
        )}

        <button
          className="text-xs bg-gray-200 hover:bg-gray-300 px-3 py-1.5 rounded mb-4 disabled:opacity-50"
          disabled={reprocessMut.isPending}
          onClick={() => {
            reprocessMut.mutate(undefined, {
              onSuccess: (data) => {
                setToast(`✅ Переобработано: категория «${data.category || "—"}»${data.auto_replied ? ", отправлен автоответ" : ""}`);
              },
              onError: (err: any) => {
                setToast("❌ Ошибка: " + (err?.message ?? ""));
              },
            });
          }}
        >
          {reprocessMut.isPending ? "Обработка…" : "🔄 Переобработать через ИИ"}
        </button>

        <div className="border rounded p-4 mb-4">
          <h3 className="font-bold mb-2">Заказ</h3>
          {!msg.contact_id ? (
            <div className="text-sm text-gray-500">
              Привяжите контакт, чтобы создать заказ.{" "}
              <button
                className="text-blue-600 underline ml-1"
                onClick={() => setShowContactDropdown(!showContactDropdown)}
              >
                Привязать контакт
              </button>
            </div>
          ) : linkedOrder ? (
            <>
              <p className="text-sm">Статус: {statusLabel(linkedOrder.status)}</p>
              <p className="text-sm">Сумма: {formatPrice(linkedOrder.total_kopecks)}</p>
              <Link to={`/orders/${linkedOrder.id}`} className="text-blue-600 text-sm">Открыть заказ →</Link>
            </>
          ) : (
            <>
              {showCreateOrder ? (
                <div className="space-y-2">
                  <input
                    className="w-full border rounded px-2 py-1 text-sm"
                    placeholder="Сумма (коп.)"
                    type="number"
                    value={orderTotal}
                    onChange={(e) => setOrderTotal(e.target.value)}
                  />
                  <textarea
                    className="w-full border rounded px-2 py-1 text-sm"
                    rows={2}
                    placeholder="Примечание"
                    value={orderNotes}
                    onChange={(e) => setOrderNotes(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <button
                      className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                      disabled={createOrderMut.isPending}
                      onClick={() => createOrderMut.mutate({ total_kopecks: Number(orderTotal) || 0, notes: orderNotes || msg.text })}
                    >
                      {createOrderMut.isPending ? "Создание..." : "Создать"}
                    </button>
                    <button
                      className="bg-gray-300 px-3 py-1 rounded text-sm hover:bg-gray-400"
                      onClick={() => setShowCreateOrder(false)}
                    >
                      Отмена
                    </button>
                  </div>
                  {createOrderMut.error && (
                    <p className="text-red-600 text-xs">{(createOrderMut.error as any).message}</p>
                  )}
                </div>
              ) : (
                <button
                  className="text-blue-600 text-sm underline"
                  onClick={() => setShowCreateOrder(true)}
                >
                  Создать заказ
                </button>
              )}
            </>
          )}
        </div>

        {folderList && (
          <div className="mb-4">
            <div className="flex items-center gap-2 flex-wrap">
              {(msgFolderIds ?? []).map((a: FolderAssign) => (
                <span
                  key={a.category_id}
                  className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded"
                  style={{ backgroundColor: a.color + "20", color: a.color }}
                >
                  {a.category_name}
                  <button
                    className="ml-0.5 hover:opacity-60"
                    onClick={() => unassignMut.mutate(a.category_id)}
                  >
                    &times;
                  </button>
                </span>
              ))}
              {unassignedFolders.length > 0 && (
                <select
                  className="text-xs border rounded px-1.5 py-0.5 text-gray-500"
                  value=""
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val) assignMut.mutate(Number(val));
                  }}
                >
                  <option value="">+ папка</option>
                  {unassignedFolders.map((f) => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </select>
              )}
            </div>
          </div>
        )}

        <div className="bg-gray-50 border rounded p-3 text-sm mb-4 whitespace-pre-wrap">
          {msg.text}
        </div>

        {msg.draft_response && !msg.sent_response && (
          <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
            <span className="text-xs font-semibold text-yellow-700">
              Предложенный ответ из Базы знаний
            </span>
            <p className="text-sm mt-1 text-gray-700">{msg.draft_response}</p>
          </div>
        )}

        {msg.sent_response && msg.draft_response && (
          <div className="bg-green-50 border border-green-200 rounded p-3 mb-4">
            <span className="text-xs font-semibold text-green-700">
              Отправленный ответ
            </span>
            <p className="text-sm mt-1 text-gray-700">{msg.draft_response}</p>
          </div>
        )}

        {!msg.sent_response && (
          <div className="border-t pt-4 space-y-3">
            <h2 className="font-semibold text-sm">Ответ</h2>
            {msg.text && (
              <TemplateSelector
                messageText={msg.text}
                onSelect={(text, templateId) => {
                  setReplyText(text);
                  setSelectedTemplateId(templateId);
                }}
              />
            )}
            <textarea
              className="w-full border rounded px-3 py-2 text-sm"
              rows={4}
              placeholder="Введите ответ…"
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
            />
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={saveToKb}
                onChange={(e) => setSaveToKb(e.target.checked)}
              />
              Сохранить ответ в Базу знаний
            </label>
            <button
              className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
              disabled={!replyText.trim() || sendReply.isPending}
              onClick={() =>
                sendReply.mutate({ text: replyText, save_to_kb: saveToKb })
              }
            >
              {sendReply.isPending ? "Отправка..." : "Отправить"}
            </button>
            {sendReply.error && (
              <div className="text-sm text-red-600">
                Ошибка: {(sendReply.error as any).message}
              </div>
            )}
          </div>
        )}
      </div>

      {toast && (
        <div className="fixed bottom-4 right-4 bg-gray-800 text-white px-4 py-2 rounded shadow text-sm z-50 animate-fade-in">
          {toast}
          <button className="ml-3 text-gray-300 hover:text-white" onClick={() => setToast(null)}>&times;</button>
        </div>
      )}
    </div>
  );
}