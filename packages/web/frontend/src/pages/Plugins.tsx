import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";

export default function Plugins() {
  const { data, isLoading } = useQuery({ queryKey: ["plugins"], queryFn: () => api.list<any>("plugins") });

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Plugins</h1>
      {isLoading && <p>Loading…</p>}
      <div className="grid grid-cols-3 gap-4">
        {(data ?? []).map((p: any) => (
          <Link key={p.name} to={`/plugins/${p.name}`} className="block bg-white rounded shadow p-4 hover:shadow-md transition">
            <div className="flex items-center gap-2 mb-2">
              <span className={`w-2 h-2 rounded-full ${p.status === "running" ? "bg-green-500" : "bg-gray-400"}`} />
              <span className="font-medium">{p.name}</span>
            </div>
            <div className="text-xs text-gray-500">{p.module}</div>
            <div className="text-xs text-gray-400 mt-1">Status: {p.status}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
