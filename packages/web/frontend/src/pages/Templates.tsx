import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type TemplateItem } from "../api/client";
import TemplateEditor from "../components/TemplateEditor";
import TemplateStats from "../components/TemplateStats";

const SCOPE_TABS = [
  { key: "business", label: "Бизнес" },
  { key: "system", label: "Системные" },
  { key: "learned", label: "Обученные" },
];

const CATEGORY_OPTIONS = ["заказы", "вопросы", "жалобы", "предложения", "приветствия", "прощания"];

export default function Templates() {
  const qc = useQueryClient();
  const [scope, setScope] = useState("business");
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [editorOpen, setEditorOpen] = useState(false);
  const [editTemplate, setEditTemplate] = useState<TemplateItem | null>(null);
  const [showStats, setShowStats] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const { data: templates, isLoading } = useQuery({
    queryKey: ["templates", scope, category, search],
    queryFn: () => {
      const params: Record<string, string | number | boolean> = {};
      params.scope = scope;
      if (category) params.category = category;
      if (search) params.search = search;
      return api.listTemplates(params);
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.deleteTemplate(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["templates"] });
      setToast("Шаблон удалён");
    },
    onError: (err: any) => setToast("Ошибка: " + (err?.message ?? "")),
  });

  const approveMut = useMutation({
    mutationFn: (id: string) => api.approveTemplate(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["templates"] });
      setToast("Шаблон одобрен");
    },
    onError: (err: any) => setToast("Ошибка: " + (err?.message ?? "")),
  });

  const handleSave = () => {
    qc.invalidateQueries({ queryKey: ["templates"] });
    setEditorOpen(false);
    setEditTemplate(null);
  };

  const stats = templates
    ? { total: templates.length, active: templates.filter((t) => t.is_active).length, used: templates.filter((t) => t.usage_count > 0).length }
    : null;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Шаблоны ответов</h1>
        <div className="flex gap-2">
          <button
            className="text-sm bg-gray-200 hover:bg-gray-300 px-3 py-1.5 rounded"
            onClick={() => setShowStats(!showStats)}
          >
            {showStats ? "Список" : "Статистика"}
          </button>
          {scope !== "system" && (
            <button
              className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700"
              onClick={() => { setEditTemplate(null); setEditorOpen(true); }}
            >
              + Новый шаблон
            </button>
          )}
        </div>
      </div>

      <div className="flex gap-1 mb-3">
        {SCOPE_TABS.map((tab) => (
          <button
            key={tab.key}
            className={`px-3 py-1.5 text-sm rounded ${scope === tab.key ? "bg-blue-600 text-white" : "bg-gray-200 hover:bg-gray-300"}`}
            onClick={() => setScope(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {stats && (
        <div className="text-sm text-gray-500 mb-3">
          Всего: {stats.total} | Активных: {stats.active} | Используется: {stats.used}
        </div>
      )}

      {showStats && templates ? (
        <TemplateStats templates={templates} />
      ) : (
        <>
          <div className="flex gap-2 mb-3">
            <input
              className="flex-1 border rounded px-3 py-2 text-sm"
              placeholder="Поиск по названию и тексту…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              className="text-sm border rounded px-2 py-1.5"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">Все категории</option>
              {CATEGORY_OPTIONS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {isLoading ? (
            <p>Загрузка…</p>
          ) : !templates || templates.length === 0 ? (
            <p className="text-gray-500 text-sm">Нет шаблонов.</p>
          ) : (
            <div className="bg-white rounded shadow overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-100 text-left">
                    <th className="p-2 font-medium">Категория</th>
                    <th className="p-2 font-medium">Название</th>
                    <th className="p-2 font-medium">Текст</th>
                    <th className="p-2 font-medium">Использовано</th>
                    <th className="p-2 font-medium">Успешность</th>
                    <th className="p-2 font-medium">Статус</th>
                    <th className="p-2" />
                  </tr>
                </thead>
                <tbody>
                  {templates.map((t) => (
                    <tr
                      key={t.id}
                      className={`border-t hover:bg-gray-50 ${t.scope === "system" ? "text-gray-400" : "cursor-pointer"}`}
                      onClick={() => {
                        if (t.scope !== "system") {
                          setEditTemplate(t);
                          setEditorOpen(true);
                        }
                      }}
                    >
                      <td className="p-2">{t.category}</td>
                      <td className="p-2 font-medium">{t.name}</td>
                      <td className="p-2 max-w-xs truncate">{t.text}</td>
                      <td className="p-2">{t.usage_count}</td>
                      <td className="p-2">{(t.success_rate * 100).toFixed(0)}%</td>
                      <td className="p-2">
                        {t.scope === "learned" ? (
                          <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded">
                            На модерации
                          </span>
                        ) : t.is_active ? (
                          <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                            Активен
                          </span>
                        ) : (
                          <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">
                            Неактивен
                          </span>
                        )}
                      </td>
                      <td className="p-2 flex gap-1">
                        {t.scope === "learned" && (
                          <button
                            className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
                            onClick={(e) => { e.stopPropagation(); approveMut.mutate(t.id); }}
                            disabled={approveMut.isPending}
                          >
                            Одобрить
                          </button>
                        )}
                        {t.scope !== "system" && (
                          <button
                            className="text-xs text-red-600 hover:underline"
                            onClick={(e) => { e.stopPropagation(); if (confirm("Удалить шаблон?")) deleteMut.mutate(t.id); }}
                          >
                            Удалить
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {editorOpen && (
        <TemplateEditor
          template={editTemplate}
          onSave={handleSave}
          onClose={() => { setEditorOpen(false); setEditTemplate(null); }}
        />
      )}

      {toast && (
        <div className="fixed bottom-4 right-4 bg-gray-800 text-white px-4 py-2 rounded shadow text-sm z-50 animate-fade-in">
          {toast}
          <button className="ml-3 text-gray-300 hover:text-white" onClick={() => setToast(null)}>&times;</button>
        </div>
      )}
    </div>
  );
}
