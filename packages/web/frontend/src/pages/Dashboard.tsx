import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

function StatCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="bg-white rounded shadow p-4">
      <div className="text-gray-500 text-xs uppercase">{title}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const { data: contacts } = useQuery({ queryKey: ["contacts"], queryFn: () => api.list("contacts") });
  const { data: products } = useQuery({ queryKey: ["products"], queryFn: () => api.list("products") });
  const { data: messages } = useQuery({ queryKey: ["messages"], queryFn: () => api.list("messages") });
  const { data: orders } = useQuery({ queryKey: ["orders"], queryFn: () => api.list("orders") });

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Dashboard</h1>
      <div className="grid grid-cols-4 gap-4">
        <StatCard title="Contacts" value={String(contacts?.length ?? "…")} />
        <StatCard title="Products" value={String(products?.length ?? "…")} />
        <StatCard title="Messages" value={String(messages?.length ?? "…")} />
        <StatCard title="Orders" value={String(orders?.length ?? "…")} />
      </div>
    </div>
  );
}
