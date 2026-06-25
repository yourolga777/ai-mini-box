import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import Table from "../components/Table";

const TOPIC_COLORS: Record<string, string> = {
  Цены: "bg-green-100 text-green-700",
  Заказ: "bg-blue-100 text-blue-700",
  Жалоба: "bg-red-100 text-red-700",
  График: "bg-yellow-100 text-yellow-700",
  Другое: "bg-gray-100 text-gray-600",
};

export default function Messages() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ["messages"],
    queryFn: () => api.list<any>("messages"),
  });

  const cols = [
    { key: "id", label: "#" },
    {
      key: "topic",
      label: "Topic",
      render: (r: any) =>
        r.topic ? (
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded ${TOPIC_COLORS[r.topic] ?? "bg-gray-100 text-gray-600"}`}
          >
            {r.topic}
          </span>
        ) : null,
    },
    {
      key: "text",
      label: "Text",
      render: (r: any) => (r.text as string).slice(0, 60),
    },
    { key: "extracted_name", label: "Name" },
    { key: "extracted_phone", label: "Phone" },
    {
      key: "sent_response",
      label: "Sent",
      render: (r: any) =>
        r.sent_response ? (
          <span className="text-green-600 text-xs font-medium">Yes</span>
        ) : (
          <span className="text-gray-400 text-xs">No</span>
        ),
    },
    { key: "source", label: "Source" },
  ];

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Messages</h1>
      {isLoading ? (
        <p>Loading…</p>
      ) : (
        <Table
          cols={cols}
          data={data ?? []}
          onClickRow={(r) => navigate(`/messages/${r.id}`)}
        />
      )}
    </div>
  );
}
