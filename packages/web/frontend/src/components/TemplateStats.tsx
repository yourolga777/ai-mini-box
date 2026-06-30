import { useMemo } from "react";
import type { TemplateItem } from "../api/client";

interface Props {
  templates: TemplateItem[];
}

export default function TemplateStats({ templates }: Props) {
  const active = templates.filter((t) => t.is_active && !t.is_archived);

  const byCategory = useMemo(() => {
    const map: Record<string, number> = {};
    active.forEach((t) => { map[t.category] = (map[t.category] || 0) + 1; });
    return map;
  }, [active]);

  const topTemplates = useMemo(() =>
    [...active].sort((a, b) => b.usage_count - a.usage_count).slice(0, 5),
  [active]);

  const underperforming = useMemo(() =>
    active.filter((t) => t.usage_count > 0 && t.success_rate < 0.7),
  [active]);

  const maxCategoryCount = Math.max(...Object.values(byCategory), 1);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-semibold text-sm mb-2">По категориям</h3>
        <div className="space-y-1">
          {Object.entries(byCategory).map(([cat, count]) => (
            <div key={cat} className="flex items-center gap-2 text-sm">
              <span className="w-24 text-right text-gray-600">{cat}</span>
              <div className="flex-1 bg-gray-200 rounded h-5">
                <div
                  className="bg-blue-500 rounded h-5 transition-all"
                  style={{ width: `${(count / maxCategoryCount) * 100}%` }}
                />
              </div>
              <span className="text-xs text-gray-500 w-6">{count}</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="font-semibold text-sm mb-2">Топ-5 шаблонов</h3>
        <div className="bg-white rounded shadow text-sm">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-100 text-left">
                <th className="p-2">Название</th>
                <th className="p-2">Использовано</th>
                <th className="p-2">Успешность</th>
              </tr>
            </thead>
            <tbody>
              {topTemplates.map((t) => (
                <tr key={t.id} className="border-t">
                  <td className="p-2">{t.name}</td>
                  <td className="p-2">{t.usage_count}</td>
                  <td className="p-2">{(t.success_rate * 100).toFixed(0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {underperforming.length > 0 && (
        <div>
          <h3 className="font-semibold text-sm mb-2 text-red-700">Проблемные шаблоны (&lt; 70%)</h3>
          <div className="bg-white rounded shadow text-sm">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-100 text-left">
                  <th className="p-2">Название</th>
                  <th className="p-2">Использовано</th>
                  <th className="p-2">Успешность</th>
                </tr>
              </thead>
              <tbody>
                {underperforming.map((t) => (
                  <tr key={t.id} className="border-t">
                    <td className="p-2">{t.name}</td>
                    <td className="p-2">{t.usage_count}</td>
                    <td className="p-2 text-red-600">{(t.success_rate * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
