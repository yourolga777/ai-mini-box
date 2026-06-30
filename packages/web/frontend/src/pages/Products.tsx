import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import Table from "../components/Table";

export default function Products() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["products"], queryFn: () => api.list<any>("products") });
  const [name, setName] = useState("");

  const create = useMutation({
    mutationFn: (body: any) => api.create("products", body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["products"] }); setName(""); },
  });

  const del = useMutation({
    mutationFn: (id: number) => api.delete("products", id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });

  const cols = [
    { key: "id", label: "#" },
    { key: "name", label: "Название" },
    { key: "price_kopecks", label: "Цена (к)" },
    { key: "stock", label: "Остаток" },
  ];

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Товары</h1>
      <div className="flex gap-2 mb-4">
        <input placeholder="Название" value={name} onChange={(e) => setName(e.target.value)}
          className="border rounded px-2 py-1 text-sm" />
        <button onClick={() => create.mutate({ name })}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm">
          Добавить
        </button>
      </div>
      {isLoading ? <p>Загрузка…</p> : <Table cols={cols} data={data ?? []} onDelete={(r) => del.mutate(r.id as number)} />}
    </div>
  );
}
