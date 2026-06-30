import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, type Order } from "../api/client";
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

const STATUS_OPTIONS = [
  { value: "", label: "Все статусы" },
  { value: "new", label: "Новый" },
  { value: "processing", label: "В обработке" },
  { value: "completed", label: "Выполнен" },
  { value: "cancelled", label: "Отменён" },
];

export default function Orders() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState("");
  const [contactFilter, setContactFilter] = useState<number | "">("");
  const [searchNotes, setSearchNotes] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["orders", statusFilter, contactFilter],
    queryFn: () => {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (contactFilter !== "") params.set("contact_id", String(contactFilter));
      return api.list<Order>(`orders?${params.toString()}`);
    },
  });

  const { data: contacts } = useQuery({
    queryKey: ["contacts"],
    queryFn: () => api.list<any>("contacts"),
    staleTime: 60000,
  });
  const contactMap = useMemo(() => {
    const map: Record<number, string> = {};
    (contacts ?? []).forEach((c: any) => { map[c.id] = c.name; });
    return map;
  }, [contacts]);

  const contactOptions = useMemo(() => {
    return [...(contacts ?? [])]
      .sort((a: any, b: any) => (a.name ?? "").localeCompare(b.name ?? ""))
      .map((c: any) => ({ id: c.id, name: c.name }));
  }, [contacts]);

  const filtered = useMemo(() => {
    if (!searchNotes.trim()) return data ?? [];
    const q = searchNotes.toLowerCase();
    return (data ?? []).filter((o) => (o.notes ?? "").toLowerCase().includes(q));
  }, [data, searchNotes]);

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Заказы</h1>
      <div className="mb-3 flex items-center gap-2">
        <select
          className="border rounded px-2 py-1.5 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <select
          className="border rounded px-2 py-1.5 text-sm min-w-[140px]"
          value={contactFilter}
          onChange={(e) => setContactFilter(e.target.value === "" ? "" : Number(e.target.value))}
        >
          <option value="">Все контакты</option>
          {contactOptions.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <input
          className="border rounded px-2 py-1.5 text-sm flex-1"
          placeholder="Поиск по заметкам..."
          value={searchNotes}
          onChange={(e) => setSearchNotes(e.target.value)}
        />
      </div>
      {isLoading ? (
        <p>Загрузка…</p>
      ) : filtered.length === 0 ? (
        <p className="text-sm text-gray-500">Заказы не найдены</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-200 text-left">
                <th className="p-2">#</th>
                <th className="p-2">Статус</th>
                <th className="p-2">Сумма</th>
                <th className="p-2">Клиент</th>
                <th className="p-2">Дата</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((o) => (
                <tr
                  key={o.id}
                  className="border-t hover:bg-gray-100 cursor-pointer"
                  onClick={() => navigate(`/orders/${o.id}`)}
                >
                  <td className="p-2">{o.id}</td>
                  <td className="p-2">{statusLabel(o.status)}</td>
                  <td className="p-2">{formatPrice(o.total_kopecks)}</td>
                  <td className="p-2">{contactMap[o.contact_id ?? -1] ?? "-"}</td>
                  <td className="p-2">{formatDate(o.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
