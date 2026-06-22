import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";

export default function PluginDetail() {
  const { name } = useParams<{ name: string }>();
  const { data: plugin, isLoading } = useQuery({
    queryKey: ["plugin", name],
    queryFn: () => api.get<any>("plugins", name as any),
    enabled: !!name,
  });
  const { data: logs } = useQuery({
    queryKey: ["plugin-logs", name],
    queryFn: () => api.get<any>("plugins", name as any).then(() => fetch(`/api/plugins/${name}/logs`).then((r) => r.json())),
    enabled: !!name,
  });

  if (isLoading) return <p>Loading…</p>;
  if (!plugin) return <p>Plugin not found.</p>;

  return (
    <div>
      <Link to="/plugins" className="text-blue-600 text-sm">&larr; Back to plugins</Link>
      <h1 className="text-xl font-bold mt-2 mb-4">{plugin.name}</h1>
      <div className="bg-white rounded shadow p-4 mb-4">
        <div className="text-sm text-gray-500">Module</div>
        <div className="font-mono text-sm">{plugin.module}</div>
        <div className="text-sm text-gray-500 mt-2">Status</div>
        <div className="flex items-center gap-2 mt-1">
          <span className={`w-2 h-2 rounded-full ${plugin.status === "running" ? "bg-green-500" : "bg-gray-400"}`} />
          <span>{plugin.status}</span>
        </div>
      </div>
      <div className="bg-white rounded shadow p-4">
        <h2 className="font-bold mb-2">Logs</h2>
        <pre className="bg-gray-900 text-green-300 text-xs p-3 rounded max-h-64 overflow-auto">
          {((logs?.lines as string[]) ?? []).join("\n") || "(no logs)"}
        </pre>
      </div>
    </div>
  );
}
