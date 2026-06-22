import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import Table from "../components/Table";

export default function Messages() {
  const { data, isLoading } = useQuery({ queryKey: ["messages"], queryFn: () => api.list<any>("messages") });

  const cols = [
    { key: "id", label: "#" },
    { key: "source", label: "Source" },
    { key: "text", label: "Text", render: (r: any) => (r.text as string).slice(0, 60) },
    { key: "topic", label: "Topic" },
  ];

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Messages</h1>
      {isLoading ? <p>Loading…</p> : <Table cols={cols} data={data ?? []} />}
    </div>
  );
}
