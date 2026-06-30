import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { formatPrice, statusLabel } from "../helpers";

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

const TOPIC_COLORS: Record<string, string> = {
  Цены: "bg-green-100 text-green-700",
  Заказ: "bg-blue-100 text-blue-700",
  Жалоба: "bg-red-100 text-red-700",
  График: "bg-yellow-100 text-yellow-700",
  Другое: "bg-gray-100 text-gray-600",
};

export default function ContactDetail() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [replyText, setReplyText] = useState("");
  const [localReplies, setLocalReplies] = useState<Record<number, string>>({});
  const chatEndRef = useRef<HTMLDivElement>(null);

  const { data: contact, isLoading } = useQuery({
    queryKey: ["contact", id],
    queryFn: () => api.get<any>("contacts", Number(id)),
  });

  const { data: rawMessages } = useQuery({
    queryKey: ["contact-messages", id],
    queryFn: async () => {
      const res = await fetch(`/api/messages?contact_id=${id}&limit=100`);
      return res.json();
    },
    enabled: !!contact,
  });

  const messages: any[] = (rawMessages ?? []).slice().sort(
    (a: any, b: any) => new Date(a.received_at).getTime() - new Date(b.received_at).getTime()
  );

  const lastWithoutReply = [...messages].reverse().find(
    (m: any) => !m.sent_response
  );
  const { data: orders } = useQuery({
    queryKey: ["contact-orders", id],
    queryFn: () => api.getContactOrders(Number(id)),
    enabled: !!contact,
  });

  const targetId = lastWithoutReply?.id ?? messages[messages.length - 1]?.id;

  const sendMut = useMutation({
    mutationFn: (body: { text: string }) =>
      fetch(`/api/messages/${targetId}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: body.text, save_to_kb: false }),
      }).then((r) => {
        if (!r.ok) throw new Error("Ошибка отправки");
        return r.json();
      }),
    onSuccess: (data) => {
      setLocalReplies((prev) => ({ ...prev, [data.id]: replyText }));
      setReplyText("");
      qc.invalidateQueries({ queryKey: ["contact-messages", id] });
    },
  });

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, localReplies]);

  if (isLoading) return <p>Загрузка…</p>;
  if (!contact) return <p>Контакт не найден.</p>;

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)]">
      <Link to="/contacts" className="text-blue-600 text-sm mb-2">&larr; Назад к контактам</Link>

      <div className="bg-white rounded shadow p-4 mb-2">
        <h1 className="text-lg font-bold">{contact.name}</h1>
        <div className="text-xs text-gray-500 mt-1">
          {contact.phone && <span className="mr-3">📞 {contact.phone}</span>}
          {contact.email && <span className="mr-3">✉ {contact.email}</span>}
          {contact.telegram && <span>💬 @{contact.telegram}</span>}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto bg-white rounded shadow p-4 mb-2 space-y-3">
        {messages.length === 0 ? (
          <p className="text-sm text-gray-500 text-center mt-8">Нет сообщений.</p>
        ) : (
          messages.map((msg: any) => (
            <div key={msg.id}>
              <div className="flex justify-start">
                <div className="max-w-[75%] bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-2 text-sm">
                  {msg.topic && (
                    <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded mb-1 ${TOPIC_COLORS[msg.topic] ?? "bg-gray-100 text-gray-600"}`}>
                      {msg.topic}
                    </span>
                  )}
                  <div className="whitespace-pre-wrap">{msg.text}</div>
                  <div className="text-xs text-gray-400 mt-1">{formatDate(msg.received_at)}</div>
                </div>
              </div>

              {(msg.sent_response && msg.draft_response) || localReplies[msg.id] ? (
                <div className="flex justify-end mt-2">
                  <div className="max-w-[75%] bg-blue-500 text-white rounded-2xl rounded-br-sm px-4 py-2 text-sm">
                    <div className="whitespace-pre-wrap">{localReplies[msg.id] || msg.draft_response}</div>
                    <div className="flex items-center justify-end gap-1 text-xs text-blue-200 mt-1">
                      <span>{formatDate(msg.received_at)}</span>
                      {msg.sent_response && <span>✓</span>}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          ))
        )}
        <div ref={chatEndRef} />
      </div>

      <section className="bg-white rounded shadow p-4 mb-2">
        <h2 className="text-lg font-bold mb-2">Заказы</h2>
        {!orders ? (
          <p className="text-sm text-gray-500">Загрузка...</p>
        ) : orders.length === 0 ? (
          <p className="text-sm text-gray-500">Нет заказов</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="py-1 pr-2">ID</th>
                <th className="py-1 pr-2">Статус</th>
                <th className="py-1 pr-2">Сумма</th>
                <th className="py-1">Дата</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="border-b">
                  <td className="py-1 pr-2"><Link to={`/orders/${o.id}`} className="text-blue-600">#{o.id}</Link></td>
                  <td className="py-1 pr-2">{statusLabel(o.status)}</td>
                  <td className="py-1 pr-2">{formatPrice(o.total_kopecks)}</td>
                  <td className="py-1">{formatDate(o.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {messages.length > 0 && (
        <div className="bg-white rounded shadow p-3">
          {sendMut.error && (
            <div className="text-xs text-red-600 mb-1">Ошибка: {(sendMut.error as any).message}</div>
          )}
          <div className="flex gap-2">
            <textarea
              className="flex-1 border rounded px-3 py-2 text-sm resize-none"
              rows={2}
              placeholder="Введите ответ…"
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
            />
            <button
              className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50 self-end"
              disabled={!replyText.trim() || sendMut.isPending}
              onClick={() => sendMut.mutate({ text: replyText })}
            >
              {sendMut.isPending ? "..." : "Отправить"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

