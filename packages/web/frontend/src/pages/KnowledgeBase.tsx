import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import Table from "../components/Table";

const TOPICS = ["Цены", "Заказ", "Жалоба", "График", "Другое"];

export default function KnowledgeBase() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["knowledge-base"],
    queryFn: () => api.list<any>("knowledge-base"),
  });

  const [topic, setTopic] = useState("");
  const [keywords, setKeywords] = useState("");
  const [answer, setAnswer] = useState("");
  const [editing, setEditing] = useState<any>(null);

  const save = useMutation({
    mutationFn: (body: any) =>
      editing
        ? api.update("knowledge-base", editing.id, body)
        : api.create("knowledge-base", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["knowledge-base"] });
      setTopic("");
      setKeywords("");
      setAnswer("");
      setEditing(null);
    },
  });

  const del = useMutation({
    mutationFn: (id: number) => api.delete("knowledge-base", id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["knowledge-base"] }),
  });

  const startEdit = (item: any) => {
    setEditing(item);
    setTopic(item.topic);
    setKeywords((item.question_keywords ?? []).join(", "));
    setAnswer(item.answer_text);
  };

  const handleSave = () => {
    const kw = keywords
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    save.mutate({ topic, question_keywords: kw, answer_text: answer });
  };

  const cols = [
    { key: "id", label: "#" },
    {
      key: "topic",
      label: "Topic",
      render: (r: any) => (
        <span className="bg-blue-100 text-blue-700 text-xs font-medium px-2 py-0.5 rounded">
          {r.topic}
        </span>
      ),
    },
    {
      key: "question_keywords",
      label: "Keywords",
      render: (r: any) => (r.question_keywords ?? []).join(", "),
    },
    {
      key: "answer_text",
      label: "Answer",
      render: (r: any) =>
        (r.answer_text ?? "").length > 80
          ? r.answer_text.slice(0, 80) + "…"
          : r.answer_text,
    },
    {
      key: "created_at",
      label: "Created",
      render: (r: any) =>
        r.created_at ? new Date(r.created_at).toLocaleDateString() : "",
    },
  ];

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Knowledge Base</h1>

      <div className="bg-white rounded shadow p-4 mb-4 space-y-3">
        <h2 className="font-semibold text-sm">
          {editing ? "Edit entry" : "New entry"}
        </h2>
        <div className="flex gap-3 flex-wrap">
          <select
            className="border rounded px-2 py-1.5 text-sm"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          >
            <option value="">Topic</option>
            {TOPICS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <input
            className="border rounded px-2 py-1.5 text-sm flex-1 min-w-[200px]"
            placeholder="Keywords (comma separated)"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
          />
        </div>
        <textarea
          className="w-full border rounded px-2 py-1.5 text-sm"
          rows={3}
          placeholder="Answer text"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
        />
        <div className="flex gap-2">
          <button
            className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
            disabled={!topic || !keywords || !answer || save.isPending}
            onClick={handleSave}
          >
            {save.isPending ? "Saving..." : editing ? "Update" : "Add"}
          </button>
          {editing && (
            <button
              className="text-gray-500 px-3 py-1.5 rounded text-sm hover:bg-gray-100"
              onClick={() => {
                setEditing(null);
                setTopic("");
                setKeywords("");
                setAnswer("");
              }}
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {isLoading ? (
        <p>Loading…</p>
      ) : (
        <Table
          cols={cols}
          data={data ?? []}
          onEdit={(r) => startEdit(r)}
          onDelete={(r) => del.mutate(r.id)}
        />
      )}
    </div>
  );
}
