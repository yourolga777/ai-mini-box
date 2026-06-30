import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api, type Order, type OrderItem } from "../api/client";
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

const STATUS_COLORS: Record<string, string> = {
  new: "bg-blue-100 text-blue-700",
  processing: "bg-yellow-100 text-yellow-700",
  completed: "bg-green-100 text-green-700",
  cancelled: "bg-red-100 text-red-700",
};

export default function OrderDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [newStatus, setNewStatus] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editItem, setEditItem] = useState<OrderItem | null>(null);
  const [productSearch, setProductSearch] = useState("");
  const [itemProductName, setItemProductName] = useState("");
  const [itemQuantity, setItemQuantity] = useState("1");
  const [itemPrice, setItemPrice] = useState("");

  const orderId = Number(id);

  const { data: order, isLoading, error } = useQuery({
    queryKey: ["order", id],
    queryFn: () => api.get<Order>("orders", orderId),
  });

  const { data: contact } = useQuery({
    queryKey: ["contact", order?.contact_id],
    queryFn: () => api.get<any>("contacts", order!.contact_id!),
    enabled: !!order?.contact_id,
  });

  const { data: items } = useQuery({
    queryKey: ["order-items", id],
    queryFn: () => api.getOrderItems(orderId),
    enabled: !!order,
  });

  const { data: products } = useQuery({
    queryKey: ["product-search", productSearch],
    queryFn: () => api.searchProducts(productSearch),
    enabled: productSearch.length > 0,
  });

  const updateStatusMut = useMutation({
    mutationFn: (status: string) => api.updateOrder(orderId, { status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["order", id] });
      setNewStatus(null);
    },
  });

  const deleteMut = useMutation({
    mutationFn: () => api.deleteOrder(orderId),
    onSuccess: () => navigate("/orders"),
  });

  const addItemMut = useMutation({
    mutationFn: (data: { product_name: string; quantity: number; price_kopecks: number }) =>
      api.createOrderItem(orderId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["order-items", id] });
      qc.invalidateQueries({ queryKey: ["order", id] });
      closeModal();
    },
  });

  const updateItemMut = useMutation({
    mutationFn: ({ itemId, data }: { itemId: number; data: any }) =>
      api.updateOrderItem(orderId, itemId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["order-items", id] });
      qc.invalidateQueries({ queryKey: ["order", id] });
      closeModal();
    },
  });

  const deleteItemMut = useMutation({
    mutationFn: (itemId: number) => api.deleteOrderItem(orderId, itemId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["order-items", id] });
      qc.invalidateQueries({ queryKey: ["order", id] });
    },
  });

  const [notes, setNotes] = useState("");
  const notesRef = useRef(notes);
  notesRef.current = notes;

  const saveNotesMut = useMutation({
    mutationFn: (text: string) => api.updateOrder(orderId, { notes: text }),
  });

  useEffect(() => {
    if (order) setNotes(order.notes ?? "");
  }, [order]);

  const handleNotesBlur = () => {
    if (notesRef.current !== (order?.notes ?? "")) {
      saveNotesMut.mutate(notesRef.current);
    }
  };

  const openAddModal = (item?: OrderItem) => {
    if (item) {
      setEditItem(item);
      setItemProductName(item.product_name);
      setItemQuantity(String(item.quantity));
      setItemPrice(String(item.price_kopecks));
    } else {
      setEditItem(null);
      setItemProductName("");
      setItemQuantity("1");
      setItemPrice("");
    }
    setProductSearch("");
    setShowAddModal(true);
  };

  const closeModal = () => {
    setShowAddModal(false);
    setEditItem(null);
    setProductSearch("");
  };

  const handleSaveItem = () => {
    const qty = parseInt(itemQuantity) || 1;
    const price = parseInt(itemPrice) || 0;
    if (!itemProductName.trim()) return;
    if (editItem) {
      updateItemMut.mutate({ itemId: editItem.id, data: { product_name: itemProductName, quantity: qty, price_kopecks: price } });
    } else {
      addItemMut.mutate({ product_name: itemProductName, quantity: qty, price_kopecks: price });
    }
  };

  const totalKopecks = items?.reduce((sum, i) => sum + i.quantity * i.price_kopecks, 0) ?? 0;

  if (isLoading) return <div className="animate-pulse space-y-4"><div className="h-8 bg-gray-200 rounded w-1/3" /><div className="h-32 bg-gray-200 rounded" /></div>;
  if (error) return <p className="text-red-600">Ошибка загрузки: {(error as any).message}. <button onClick={() => qc.invalidateQueries({ queryKey: ["order", id] })} className="text-blue-600 underline">Повторить</button></p>;
  if (!order) return <p>Заказ не найден. <Link to="/orders" className="text-blue-600 underline">Назад к заказам</Link></p>;

  return (
    <div>
      <Link to="/orders" className="text-blue-600 text-sm">&larr; Назад к заказам</Link>

      <div className="bg-white rounded shadow p-4 mt-2 mb-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-bold">Заказ #{order.id}</h1>
          <div className="flex items-center gap-2">
            {newStatus !== null ? (
              <div className="flex items-center gap-1">
                <select
                  className="text-xs border rounded px-2 py-1"
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  autoFocus
                >
                  <option value="new">Новый</option>
                  <option value="processing">В обработке</option>
                  <option value="completed">Выполнен</option>
                  <option value="cancelled">Отменён</option>
                </select>
                <button className="text-xs bg-blue-600 text-white px-2 py-1 rounded" onClick={() => updateStatusMut.mutate(newStatus)} disabled={updateStatusMut.isPending}>OK</button>
                <button className="text-xs text-gray-500" onClick={() => setNewStatus(null)}>Отмена</button>
              </div>
            ) : (
              <>
                <span className={`text-xs font-medium px-2 py-0.5 rounded ${STATUS_COLORS[order.status] ?? "bg-gray-100"}`}>
                  {statusLabel(order.status)}
                </span>
                <button className="text-xs text-blue-600 underline" onClick={() => setNewStatus(order.status)}>Изменить</button>
                {!showDeleteConfirm ? (
                  <button className="text-xs text-red-500 underline" onClick={() => setShowDeleteConfirm(true)}>Удалить</button>
                ) : (
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-red-600">Удалить?</span>
                    <button className="text-xs bg-red-600 text-white px-2 py-0.5 rounded" onClick={() => deleteMut.mutate()} disabled={deleteMut.isPending}>Да</button>
                    <button className="text-xs text-gray-500" onClick={() => setShowDeleteConfirm(false)}>Нет</button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm mb-4">
          <div>
            <span className="text-gray-500">Клиент:</span>{" "}
            {contact ? (
              <Link to={`/contacts/${contact.id}`} className="text-blue-600 underline">{contact.name}</Link>
            ) : (
              <span className="text-gray-400">Не привязан</span>
            )}
          </div>
          <div>
            <span className="text-gray-500">Сообщение:</span>{" "}
            {order.source_message_id ? (
              <Link to={`/messages/${order.source_message_id}`} className="text-blue-600 underline">№{order.source_message_id}</Link>
            ) : (
              <span className="text-gray-400">Создан вручную</span>
            )}
          </div>
          <div>
            <span className="text-gray-500">Создан:</span> {formatDate(order.created_at)}
          </div>
          <div>
            <span className="text-gray-500">Обновлён:</span> {formatDate((order as any).updated_at || order.created_at)}
          </div>
        </div>

        <section className="mb-4">
          <h2 className="font-semibold text-sm mb-2">Позиции заказа</h2>
          {!items ? (
            <p className="text-xs text-gray-400">Загрузка...</p>
          ) : items.length === 0 ? (
            <p className="text-xs text-gray-400">Нет позиций</p>
          ) : (
            <table className="w-full text-sm mb-2">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="py-1 pr-2">Товар</th>
                  <th className="py-1 pr-2">Кол-во</th>
                  <th className="py-1 pr-2">Цена</th>
                  <th className="py-1 pr-2">Сумма</th>
                  <th className="py-1 w-8" />
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className="border-b">
                    <td className="py-1 pr-2">{item.product_name}</td>
                    <td className="py-1 pr-2">{item.quantity}</td>
                    <td className="py-1 pr-2">{formatPrice(item.price_kopecks)}</td>
                    <td className="py-1 pr-2 font-medium">{formatPrice(item.quantity * item.price_kopecks)}</td>
                    <td className="py-1">
                      <button className="text-red-500 hover:text-red-700 text-xs" onClick={() => deleteItemMut.mutate(item.id)}>&times;</button>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="font-semibold">
                  <td className="py-1 pr-2" colSpan={3}>Итого:</td>
                  <td className="py-1 pr-2">{formatPrice(totalKopecks)}</td>
                  <td />
                </tr>
              </tfoot>
            </table>
          )}
          <button className="text-blue-600 text-sm underline" onClick={() => openAddModal()}>+ Добавить позицию</button>
        </section>

        <div>
          <h2 className="font-semibold text-sm mb-1">Заметки</h2>
          <textarea
            className="w-full border rounded px-3 py-2 text-sm"
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            onBlur={handleNotesBlur}
          />
          {saveNotesMut.isPending && <span className="text-xs text-gray-400">Сохранение...</span>}
        </div>
      </div>

      {showAddModal && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" onClick={closeModal}>
          <div className="bg-white rounded shadow-lg p-4 w-96 max-w-full" onClick={(e) => e.stopPropagation()}>
            <h2 className="font-semibold mb-3">{editItem ? "Редактировать" : "Добавить"} позицию</h2>

            <div className="space-y-2">
              <div>
                <label className="text-xs text-gray-500">Товар</label>
                <input
                  className="w-full border rounded px-2 py-1.5 text-sm"
                  placeholder="Поиск или ввод..."
                  value={productSearch || itemProductName}
                  onChange={(e) => {
                    const v = e.target.value;
                    setProductSearch(v);
                    setItemProductName(v);
                  }}
                />
                {productSearch.length > 0 && products && products.length > 0 && (
                  <ul className="border rounded mt-1 max-h-32 overflow-y-auto text-sm">
                    {products.map((p) => (
                      <li
                        key={p.id}
                        className="px-2 py-1 hover:bg-blue-50 cursor-pointer"
                        onClick={() => {
                          setItemProductName(p.name);
                          setItemPrice(String(p.price_kopecks));
                          setProductSearch("");
                        }}
                      >
                        {p.name} — {formatPrice(p.price_kopecks)}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div>
                <label className="text-xs text-gray-500">Количество</label>
                <input
                  className="w-full border rounded px-2 py-1.5 text-sm"
                  type="number"
                  min={1}
                  value={itemQuantity}
                  onChange={(e) => setItemQuantity(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">Цена (коп.)</label>
                <input
                  className="w-full border rounded px-2 py-1.5 text-sm"
                  type="number"
                  min={0}
                  value={itemPrice}
                  onChange={(e) => setItemPrice(e.target.value)}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-4">
              <button className="bg-gray-200 px-3 py-1.5 rounded text-sm" onClick={closeModal}>Отмена</button>
              <button
                className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm disabled:opacity-50"
                disabled={!itemProductName.trim() || addItemMut.isPending || updateItemMut.isPending}
                onClick={handleSaveItem}
              >
                {addItemMut.isPending || updateItemMut.isPending ? "..." : "Сохранить"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
