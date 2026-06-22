import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import Table from "../components/Table";

export default function Orders() {
  const { data, isLoading } = useQuery({ queryKey: ["orders"], queryFn: () => api.list<any>("orders") });

  const cols = [
    { key: "id", label: "#" },
    { key: "status", label: "Status" },
    { key: "total_kopecks", label: "Total (k)" },
    { key: "contact_id", label: "Contact" },
  ];

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Orders</h1>
      {isLoading ? <p>Loading…</p> : <Table cols={cols} data={data ?? []} />}
    </div>
  );
}
