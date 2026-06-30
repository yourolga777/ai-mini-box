import { useState, useMemo, type ReactNode, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../api/client";

interface SchemaProp {
  type: string;
  title?: string;
  format?: string;
  default?: any;
  enum?: string[];
}

interface Props {
  pluginName: string;
  schema: Record<string, any>;
  initialValues: Record<string, any>;
  onSaved?: () => void;
}

export default function PluginConfigForm({ pluginName, schema, initialValues, onSaved }: Props) {
  const [values, setValues] = useState<Record<string, any>>(() => {
    const v: Record<string, any> = {};
    for (const [key, prop] of Object.entries(schema.properties ?? {})) {
      const p = prop as SchemaProp;
      v[key] = initialValues[key] ?? p.default ?? "";
    }
    return v;
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const saveMut = useMutation({
    mutationFn: (data: Record<string, any>) => api.setPluginConfig(pluginName, data),
    onSuccess: () => {
      setErrors({});
      onSaved?.();
    },
    onError: (err: any) => {
      setErrors({ _form: err?.message ?? "Ошибка сохранения" });
    },
  });

  const requiredSet = useMemo(() => new Set(schema.required ?? []), [schema.required]);
  const fieldOrder = useMemo(() => Object.keys(schema.properties), [schema.properties]);

  const setField = (key: string, value: any) => {
    setValues((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};
    for (const key of fieldOrder) {
      if (requiredSet.has(key) && (values[key] === "" || values[key] == null)) {
        newErrors[key] = "Обязательное поле";
      }
    }
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    saveMut.mutate(values);
  };

  const renderField = (key: string, prop: SchemaProp): ReactNode => {
    const val = values[key];
    const err = errors[key];
    const isRequired = requiredSet.has(key);
    const label = prop.title ?? key;
    const baseCls = "w-full border rounded px-2 py-1.5 text-sm";

    let input: React.ReactNode;

    if (prop.type === "boolean") {
      input = (
        <input
          type="checkbox"
          checked={!!val}
          onChange={(e) => setField(key, e.target.checked)}
          className="rounded"
        />
      );
    } else if (prop.enum) {
      input = (
        <select
          className={`${baseCls} ${err ? "border-red-400" : ""}`}
          value={val ?? ""}
          onChange={(e) => setField(key, e.target.value)}
        >
          <option value="">—</option>
          {prop.enum.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      );
    } else if (prop.type === "integer" || prop.type === "number") {
      input = (
        <input
          type="number"
          className={`${baseCls} ${err ? "border-red-400" : ""}`}
          value={val ?? ""}
          onChange={(e) => setField(key, e.target.value === "" ? "" : Number(e.target.value))}
        />
      );
    } else if (prop.format === "password") {
      input = (
        <input
          type="password"
          className={`${baseCls} ${err ? "border-red-400" : ""}`}
          value={val ?? ""}
          onChange={(e) => setField(key, e.target.value)}
        />
      );
    } else if (prop.format === "uri" || prop.format === "url") {
      input = (
        <input
          type="url"
          className={`${baseCls} ${err ? "border-red-400" : ""}`}
          value={val ?? ""}
          onChange={(e) => setField(key, e.target.value)}
        />
      );
    } else {
      input = (
        <input
          type="text"
          className={`${baseCls} ${err ? "border-red-400" : ""}`}
          value={val ?? ""}
          onChange={(e) => setField(key, e.target.value)}
        />
      );
    }

    return (
      <div key={key} className="mb-3">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {isRequired && <span className="text-red-500 ml-1">*</span>}
        </label>
        {input}
        {err && <p className="text-xs text-red-500 mt-0.5">{err}</p>}
      </div>
    );
  };

  if (fieldOrder.length === 0) return null;

  return (
    <form onSubmit={handleSubmit}>
      {fieldOrder.map((key) => renderField(key, schema.properties[key]))}
      {errors._form && (
        <p className="text-sm text-red-600 mb-3">{errors._form}</p>
      )}
      <button
        type="submit"
        className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
        disabled={saveMut.isPending}
      >
        {saveMut.isPending ? "Сохранение…" : "Сохранить"}
      </button>
      {saveMut.isSuccess && (
        <span className="text-sm text-green-600 ml-3">✓ Сохранено</span>
      )}
    </form>
  );
}
