import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type BusinessConfig } from "../api/client";

interface FAQItem {
  question: string;
  answer: string;
}

const defaultConfig: BusinessConfig = {
  company_name: "",
  work_hours: "",
  delivery_info: "",
  return_policy: "",
  payment_methods: "",
  contacts: "",
  faq: [],
};

export default function BusinessSettings() {
  const qc = useQueryClient();
  const [form, setForm] = useState<BusinessConfig>(defaultConfig);
  const [loaded, setLoaded] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const { isLoading } = useQuery({
    queryKey: ["business-config"],
    queryFn: async () => {
      const data = await api.getBusinessConfig();
      setForm(data);
      setLoaded(true);
      return data;
    },
  });

  const saveMut = useMutation({
    mutationFn: (data: Partial<BusinessConfig>) => api.updateBusinessConfig(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["business-config"] });
      setToast("Сохранено");
    },
    onError: (err: any) => {
      setToast("Ошибка: " + (err?.message ?? "неизвестная"));
    },
  });

  const update = (key: keyof BusinessConfig, value: any) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const addFaq = () => {
    setForm((prev) => ({
      ...prev,
      faq: [...prev.faq, { question: "", answer: "" }],
    }));
  };

  const removeFaq = (idx: number) => {
    setForm((prev) => ({
      ...prev,
      faq: prev.faq.filter((_, i) => i !== idx),
    }));
  };

  const updateFaq = (idx: number, key: keyof FAQItem, value: string) => {
    setForm((prev) => {
      const faq = [...prev.faq];
      faq[idx] = { ...faq[idx], [key]: value };
      return { ...prev, faq };
    });
  };

  const handleSave = () => {
    saveMut.mutate(form);
  };

  const handleReset = () => {
    if (loaded) {
      setForm((prev) => ({ ...prev }));
      qc.invalidateQueries({ queryKey: ["business-config"] }).then(() => {
        const data = qc.getQueryData<BusinessConfig>(["business-config"]);
        if (data) setForm(data);
      });
    }
  };

  if (isLoading) return <p>Загрузка…</p>;

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Настройки бизнеса</h1>
      <div className="bg-white rounded shadow p-4 max-w-2xl space-y-4">
        <Field label="Название компании" value={form.company_name} onChange={(v) => update("company_name", v)} />
        <Field label="Часы работы" value={form.work_hours} onChange={(v) => update("work_hours", v)} />
        <Field label="Условия доставки" value={form.delivery_info} onChange={(v) => update("delivery_info", v)} textarea />
        <Field label="Условия возврата" value={form.return_policy} onChange={(v) => update("return_policy", v)} textarea />
        <Field label="Способы оплаты" value={form.payment_methods} onChange={(v) => update("payment_methods", v)} textarea />
        <Field label="Контакты" value={form.contacts} onChange={(v) => update("contacts", v)} textarea />

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">FAQ</label>
            <button
              className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
              onClick={addFaq}
            >
              + Добавить вопрос
            </button>
          </div>
          <div className="space-y-2">
            {form.faq.length === 0 && (
              <p className="text-xs text-gray-400">Нет вопросов</p>
            )}
            {form.faq.map((item, idx) => (
              <div key={idx} className="flex gap-2 items-start border rounded p-2">
                <div className="flex-1 space-y-1">
                  <input
                    className="w-full border rounded px-2 py-1 text-sm"
                    placeholder="Вопрос"
                    value={item.question}
                    onChange={(e) => updateFaq(idx, "question", e.target.value)}
                  />
                  <textarea
                    className="w-full border rounded px-2 py-1 text-sm"
                    rows={2}
                    placeholder="Ответ"
                    value={item.answer}
                    onChange={(e) => updateFaq(idx, "answer", e.target.value)}
                  />
                </div>
                <button
                  className="text-red-500 hover:text-red-700 text-lg leading-none mt-1"
                  onClick={() => removeFaq(idx)}
                >
                  &times;
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
            disabled={saveMut.isPending}
            onClick={handleSave}
          >
            {saveMut.isPending ? "Сохранение..." : "Сохранить"}
          </button>
          <button
            className="bg-gray-300 px-4 py-2 rounded text-sm hover:bg-gray-400"
            onClick={handleReset}
          >
            Отмена
          </button>
        </div>
      </div>

      {toast && (
        <div className="fixed bottom-4 right-4 bg-gray-800 text-white px-4 py-2 rounded shadow text-sm z-50 animate-fade-in">
          {toast}
          <button className="ml-3 text-gray-300 hover:text-white" onClick={() => setToast(null)}>&times;</button>
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  textarea,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  textarea?: boolean;
}) {
  return (
    <div>
      <label className="text-sm font-medium text-gray-700 block mb-1">{label}</label>
      {textarea ? (
        <textarea
          className="w-full border rounded px-3 py-2 text-sm"
          rows={3}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : (
        <input
          className="w-full border rounded px-3 py-2 text-sm"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </div>
  );
}
