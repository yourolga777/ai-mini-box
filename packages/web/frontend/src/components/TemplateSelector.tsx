import { useQuery } from "@tanstack/react-query";
import { api, type TemplateItem } from "../api/client";

interface Props {
  messageText: string;
  onSelect: (text: string, templateId: string) => void;
}

export default function TemplateSelector({ messageText, onSelect }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["template-suggest", messageText],
    queryFn: () => api.suggestTemplates(messageText),
    enabled: !!messageText,
    staleTime: 60_000,
  });

  if (isLoading) {
    return <div className="text-xs text-gray-400 mb-2">Подбор шаблонов…</div>;
  }

  const templates = data?.templates ?? [];

  if (templates.length === 0) {
    return null;
  }

  return (
    <div className="mb-2">
      <div className="text-xs text-gray-500 mb-1">Предложенные шаблоны:</div>
      <div className="flex flex-col gap-1">
        {templates.map((t: TemplateItem) => (
          <button
            key={t.id}
            className="text-left text-xs bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded px-2 py-1.5 transition"
            onClick={() => onSelect(t.text, t.id)}
          >
            <span className="font-medium">{t.name}</span>
            <span className="text-gray-400 ml-2">{(t.success_rate * 100).toFixed(0)}%</span>
            <p className="text-gray-600 truncate">{t.text}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
