import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import Table from "../components/Table";

export default function Contacts() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["contacts"], queryFn: () => api.list<any>("contacts") });
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");

  const create = useMutation({
    mutationFn: (body: any) => api.create("contacts", body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["contacts"] }); setName(""); setPhone(""); },
  });

  const del = useMutation({
    mutationFn: (id: number) => api.delete("contacts", id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["contacts"] }),
  });

  const cols = [
    { key: "id", label: "#" },
    { key: "name", label: "Name" },
    { key: "phone", label: "Phone" },
    { key: "email", label: "Email" },
  ];

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Contacts</h1>
      <div className="flex gap-2 mb-4">
        <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)}
          className="border rounded px-2 py-1 text-sm" />
        <input placeholder="Phone" value={phone} onChange={(e) => setPhone(e.target.value)}
          className="border rounded px-2 py-1 text-sm" />
        <button onClick={() => create.mutate({ name, phone })}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm">
          Add
        </button>
      </div>
      {isLoading ? <p>Loading…</p> : <Table cols={cols} data={data ?? []} onDelete={(r) => del.mutate(r.id as number)} />}
    </div>
  );
}
