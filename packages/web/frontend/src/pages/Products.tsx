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
    { key: "name", label: "Name" },
    { key: "price_kopecks", label: "Price (k)" },
    { key: "stock", label: "Stock" },
  ];

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Products</h1>
      <div className="flex gap-2 mb-4">
        <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)}
          className="border rounded px-2 py-1 text-sm" />
        <button onClick={() => create.mutate({ name })}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm">
          Add
        </button>
      </div>
      {isLoading ? <p>Loading…</p> : <Table cols={cols} data={data ?? []} onDelete={(r) => del.mutate(r.id as number)} />}
    </div>
  );
}
