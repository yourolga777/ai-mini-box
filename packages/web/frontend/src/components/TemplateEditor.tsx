import { useState } from "react";
import { api, type TemplateItem, type TemplateCreateBody } from "../api/client";

const AVAILABLE_VARIABLES = ["name", "order", "date", "address", "product", "price", "company"];

const CATEGORY_OPTIONS = ["заказы", "вопросы", "жалобы", "предложения", "приветствия", "прощания"];

interface Props {
  template: TemplateItem | null;
  onSave: () => void;
  onClose: () => void;
}

export default function TemplateEditor({ template, onSave, onClose }: Props) {
  const isNew = !template;
  const [name, setName] = useState(template?.name ?? "");
  const [category, setCategory] = useState(template?.category ?? CATEGORY_OPTIONS[0]);
  const [text, setText] = useState(template?.text ?? "");
  const [triggers, setTriggers] = useState<string[]>(template?.triggers ?? []);
  const [triggerInput, setTriggerInput] = useState("");
  const [confidenceMin, setConfidenceMin] = useState(template?.confidence_min ?? 0.6);
  const [isActive, setIsActive] = useState(template?.is_active ?? true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const previewText = text.replace(/\{\{(\w+)\}\}/g, (_, key) => {
    const samples: Record<string, string> = { name: "Иван", order: "12345", date: "01.01.2026", address: "ул. Ленина, 1", product: "Товар", price: "1000", company: "ООО Пример" };
    return samples[key] ?? `{{${key}}}`;
  });

  const insertVariable = (v: string) => {
    setText((prev) => prev + `{{${v}}}`);
  };

  const addTrigger = () => {
    const val = triggerInput.trim().toLowerCase();
    if (val && !triggers.includes(val)) {
      setTriggers([...triggers, val]);
    }
    setTriggerInput("");
  };

  const removeTrigger = (idx: number) => {
    setTriggers(triggers.filter((_, i) => i !== idx));
  };

  const handleSave = async () => {
    if (!name.trim()) { setError("Название обязательно"); return; }
    if (!text.trim()) { setError("Текст шаблона обязателен"); return; }
    setSaving(true);
    setError(null);
    try {
      if (isNew) {
        const body: TemplateCreateBody = {
          category,
          name: name.trim(),
          text: text.trim(),
          triggers,
          confidence_min: confidenceMin,
        };
        await api.createTemplate(body);
      } else {
        await api.updateTemplate(template.id, {
          category,
          name: name.trim(),
          text: text.trim(),
          triggers,
          confidence_min: confidenceMin,
          is_active: isActive,
        });
      }
      onSave();
    } catch (err: any) {
      setError(err?.message ?? "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold">{isNew ? "Новый шаблон" : "Редактировать шаблон"}</h2>
          <button className="text-gray-500 hover:text-gray-700 text-xl" onClick={onClose}>&times;</button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Название</label>
            <input className="w-full border rounded px-3 py-2 text-sm" value={name} onChange={(e) => setName(e.target.value)} placeholder="Название шаблона" />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Категория</label>
            <select className="w-full border rounded px-3 py-2 text-sm" value={category} onChange={(e) => setCategory(e.target.value)}>
              {CATEGORY_OPTIONS.map((c) => (<option key={c} value={c}>{c}</option>))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Текст шаблона</label>
            <textarea
              className="w-full border rounded px-3 py-2 text-sm font-mono"
              rows={5}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Здравствуйте, {{name}}! Ваш заказ №{{order}} готов."
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Вставка переменных</label>
            <div className="flex gap-1 flex-wrap">
              {AVAILABLE_VARIABLES.map((v) => (
                <button key={v} className="text-xs bg-gray-200 hover:bg-gray-300 px-2 py-1 rounded" onClick={() => insertVariable(v)}>
                  {'{{' + v + '}}'}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-gray-50 border rounded p-3">
            <label className="block text-sm font-medium mb-1">Предпросмотр</label>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{previewText}</p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Триггеры (ключевые слова)</label>
            <div className="flex gap-1 flex-wrap mb-1">
              {triggers.map((t, i) => (
                <span key={i} className="inline-flex items-center gap-1 text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                  {t}
                  <button className="hover:text-red-600" onClick={() => removeTrigger(i)}>&times;</button>
                </span>
              ))}
            </div>
            <div className="flex gap-1">
              <input className="flex-1 border rounded px-2 py-1 text-sm" placeholder="Добавить триггер…" value={triggerInput} onChange={(e) => setTriggerInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addTrigger(); } }} />
              <button className="bg-gray-200 hover:bg-gray-300 px-2 py-1 rounded text-sm" onClick={addTrigger}>+</button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Минимальная уверенность: {confidenceMin.toFixed(1)}</label>
            <input type="range" min="0" max="1" step="0.1" value={confidenceMin} onChange={(e) => setConfidenceMin(Number(e.target.value))} className="w-full" />
          </div>

          {!isNew && (
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Активен</label>
              <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
            </div>
          )}
        </div>

        {error && <p className="text-red-600 text-sm mt-3">{error}</p>}

        <div className="flex justify-end gap-2 mt-6">
          <button className="bg-gray-300 hover:bg-gray-400 px-4 py-2 rounded text-sm" onClick={onClose}>Отмена</button>
          <button className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50" onClick={handleSave} disabled={saving}>
            {saving ? "Сохранение…" : isNew ? "Создать" : "Сохранить"}
          </button>
        </div>
      </div>
    </div>
  );
}
