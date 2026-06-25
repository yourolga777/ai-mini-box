import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { useState } from "react";
import { api } from "../api/client";

interface Message {
  id: number;
  source: string;
  chat_id: string | null;
  contact_id: number | null;
  text: string;
  topic: string | null;
  extracted_phone: string | null;
  extracted_name: string | null;
  draft_response: string | null;
  sent_response: boolean;
  received_at: string;
}

const TOPIC_COLORS: Record<string, string> = {
  Цены: "bg-green-100 text-green-700",
  Заказ: "bg-blue-100 text-blue-700",
  Жалоба: "bg-red-100 text-red-700",
  График: "bg-yellow-100 text-yellow-700",
  Другое: "bg-gray-100 text-gray-600",
};

export default function MessageDetail() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [replyText, setReplyText] = useState("");
  const [saveToKb, setSaveToKb] = useState(false);

  const { data: msg, isLoading } = useQuery({
    queryKey: ["message", id],
    queryFn: () => api.get<Message>("messages", Number(id)),
  });

  const sendReply = useMutation({
    mutationFn: (body: { text: string; save_to_kb: boolean }) =>
      fetch(`/api/messages/${id}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }).then((r) => r.json()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["message", id] });
      qc.invalidateQueries({ queryKey: ["messages"] });
      qc.invalidateQueries({ queryKey: ["knowledge-base"] });
      setReplyText("");
      setSaveToKb(false);
    },
  });

  if (isLoading) return <p>Loading…</p>;
  if (!msg) return <p>Message not found.</p>;

  const topicColor = TOPIC_COLORS[msg.topic ?? ""] ?? "bg-gray-100 text-gray-600";

  return (
    <div>
      <Link to="/messages" className="text-blue-600 text-sm">
        &larr; Back to messages
      </Link>

      <div className="bg-white rounded shadow p-4 mt-2 mb-4">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-lg font-bold">
            Message #{msg.id}
          </h1>
          {msg.topic && (
            <span className={`text-xs font-medium px-2 py-0.5 rounded ${topicColor}`}>
              {msg.topic}
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm mb-4">
          <div>
            <span className="text-gray-500">Source:</span> {msg.source}
          </div>
          {msg.extracted_name && (
            <div>
              <span className="text-gray-500">Name:</span> {msg.extracted_name}
            </div>
          )}
          {msg.extracted_phone && (
            <div>
              <span className="text-gray-500">Phone:</span> {msg.extracted_phone}
            </div>
          )}
          {msg.chat_id && (
            <div>
              <span className="text-gray-500">Chat ID:</span> {msg.chat_id}
            </div>
          )}
          <div>
            <span className="text-gray-500">Date:</span>{" "}
            {new Date(msg.received_at).toLocaleString()}
          </div>
          <div>
            <span className="text-gray-500">Sent:</span>{" "}
            {msg.sent_response ? "Yes" : "No"}
          </div>
        </div>

        <div className="bg-gray-50 border rounded p-3 text-sm mb-4 whitespace-pre-wrap">
          {msg.text}
        </div>

        {msg.draft_response && !msg.sent_response && (
          <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
            <span className="text-xs font-semibold text-yellow-700">
              Suggested answer from Knowledge Base
            </span>
            <p className="text-sm mt-1 text-gray-700">{msg.draft_response}</p>
          </div>
        )}

        {msg.sent_response && msg.draft_response && (
          <div className="bg-green-50 border border-green-200 rounded p-3 mb-4">
            <span className="text-xs font-semibold text-green-700">
              Sent reply
            </span>
            <p className="text-sm mt-1 text-gray-700">{msg.draft_response}</p>
          </div>
        )}

        {!msg.sent_response && (
          <div className="border-t pt-4 space-y-3">
            <h2 className="font-semibold text-sm">Reply</h2>
            <textarea
              className="w-full border rounded px-3 py-2 text-sm"
              rows={4}
              placeholder="Type your reply…"
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
            />
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={saveToKb}
                onChange={(e) => setSaveToKb(e.target.checked)}
              />
              Save answer to Knowledge Base
            </label>
            <button
              className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
              disabled={!replyText.trim() || sendReply.isPending}
              onClick={() =>
                sendReply.mutate({ text: replyText, save_to_kb: saveToKb })
              }
            >
              {sendReply.isPending ? "Sending..." : "Send"}
            </button>
            {sendReply.error && (
              <div className="text-sm text-red-600">
                Error: {(sendReply.error as any).message}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
