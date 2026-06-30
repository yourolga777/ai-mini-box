import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { EmailConfig, EmailStatus, EmailTestRequest } from "../api/client";

const DEFAULT_FORM: EmailConfig = {
  imap_host: "",
  imap_port: 993,
  imap_ssl: true,
  smtp_host: "",
  smtp_port: 587,
  smtp_ssl: true,
  email_address: "",
  email_password: "",
  folder: "INBOX",
  max_per_cycle: 50,
  mark_as_seen: true,
  poll_interval_seconds: 60,
};

const PROVIDER_PRESETS: Record<string, {
  label: string;
  imap_host: string;
  imap_port: number;
  imap_ssl: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_ssl: boolean;
  appPasswordUrl: string;
  instructions: string;
} | null> = {
  gmail: {
    label: "Gmail",
    imap_host: "imap.gmail.com",
    imap_port: 993,
    imap_ssl: true,
    smtp_host: "smtp.gmail.com",
    smtp_port: 587,
    smtp_ssl: true,
    appPasswordUrl: "https://support.google.com/accounts/answer/185833",
    instructions: "Используйте пароль приложения Google (обычный пароль не подходит).",
  },
  yandex: {
    label: "Яндекс",
    imap_host: "imap.yandex.ru",
    imap_port: 993,
    imap_ssl: true,
    smtp_host: "smtp.yandex.ru",
    smtp_port: 465,
    smtp_ssl: true,
    appPasswordUrl: "https://id.yandex.ru/security/app-passwords",
    instructions: "В настройках почты включите IMAP. Используйте пароль приложения.",
  },
  mailru: {
    label: "Mail.ru",
    imap_host: "imap.mail.ru",
    imap_port: 993,
    imap_ssl: true,
    smtp_host: "smtp.mail.ru",
    smtp_port: 465,
    smtp_ssl: true,
    appPasswordUrl: "https://mail.ru/security",
    instructions: "Создайте пароль для внешнего приложения в настройках безопасности.",
  },
  custom: null,
};

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex items-center gap-3 text-sm">
      <span className="w-36 shrink-0 text-gray-600">{label}</span>
      {children}
    </label>
  );
}

function Skeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-5 w-48 bg-gray-200 rounded" />
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div key={i} className="flex gap-3 items-center">
          <div className="h-4 w-36 bg-gray-200 rounded" />
          <div className="h-9 flex-1 bg-gray-200 rounded" />
        </div>
      ))}
    </div>
  );
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded shadow p-4 mb-4">
      <h2 className="text-sm font-semibold text-gray-700 mb-3">{title}</h2>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

export default function EmailSettings() {
  const qc = useQueryClient();
  const [form, setForm] = useState<EmailConfig>(DEFAULT_FORM);
  const [dirty, setDirty] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [provider, setProvider] = useState<string>("");

  const { data: status, isLoading, isError, error } = useQuery<EmailStatus>({
    queryKey: ["email-status"],
    queryFn: api.emailStatus,
    refetchInterval: 30_000,
  });

  useEffect(() => {
    if (status?.configured && !dirty) {
      setForm((prev) => ({
        imap_host: (status as any).imap_host ?? prev.imap_host,
        imap_port: (status as any).imap_port ?? prev.imap_port,
        imap_ssl: (status as any).imap_ssl ?? prev.imap_ssl,
        smtp_host: (status as any).smtp_host ?? prev.smtp_host,
        smtp_port: (status as any).smtp_port ?? prev.smtp_port,
        smtp_ssl: (status as any).smtp_ssl ?? prev.smtp_ssl,
        email_address: (status as any).email_address ?? prev.email_address,
        email_password: (status as any).email_password ?? prev.email_password,
        folder: (status as any).folder ?? prev.folder,
        max_per_cycle: (status as any).max_per_cycle ?? prev.max_per_cycle,
        mark_as_seen: (status as any).mark_as_seen ?? prev.mark_as_seen,
        poll_interval_seconds: (status as any).poll_interval_seconds ?? prev.poll_interval_seconds,
      }));
    }
  }, [status, dirty]);

  const set = <K extends keyof EmailConfig>(key: K, value: EmailConfig[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setDirty(true);
  };

  const handleProviderChange = (val: string) => {
    setProvider(val);
    const preset = PROVIDER_PRESETS[val];
    if (preset) {
      setForm((prev) => ({
        ...prev,
        imap_host: preset.imap_host,
        imap_port: preset.imap_port,
        imap_ssl: preset.imap_ssl,
        smtp_host: preset.smtp_host,
        smtp_port: preset.smtp_port,
        smtp_ssl: preset.smtp_ssl,
      }));
    }
  };

  const validate = (): string | null => {
    if (!form.imap_host.trim()) return "IMAP сервер не может быть пустым";
    if (!form.smtp_host.trim()) return "SMTP сервер не может быть пустым";
    if (form.imap_port < 1 || form.imap_port > 65535) return "IMAP порт должен быть от 1 до 65535";
    if (form.smtp_port < 1 || form.smtp_port > 65535) return "SMTP порт должен быть от 1 до 65535";
    if (!/.+@.+\..+/.test(form.email_address)) return "Некорректный email адрес";
    if (!form.email_password) return "Пароль не может быть пустым";
    if (form.max_per_cycle < 1) return "Максимум за цикл: минимум 1";
    if (form.poll_interval_seconds < 5) return "Интервал проверки: минимум 5 секунд";
    return null;
  };

  const saveMutation = useMutation({
    mutationFn: (data: EmailConfig) => api.emailSaveConfig(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["email-status"] });
      setDirty(false);
      setToast("Настройки сохранены");
    },
    onError: (e: Error) => setToast(e.message),
  });

  const testMutation = useMutation({
    mutationFn: (data: EmailTestRequest) => api.emailTest(data),
    onSuccess: (res) => {
      if (res.success) {
        setToast("Подключение успешно");
      } else {
        setToast(res.message || "Ошибка подключения");
      }
    },
    onError: (e: Error) => setToast(e.message),
  });

  const handleSave = () => {
    const err = validate();
    if (err) { setToast(err); return; }
    saveMutation.mutate(form);
  };

  const handleTest = () => {
    const err = validate();
    if (err) { setToast(err); return; }
    testMutation.mutate({
      imap_host: form.imap_host,
      imap_port: form.imap_port,
      imap_ssl: form.imap_ssl,
      smtp_host: form.smtp_host,
      smtp_port: form.smtp_port,
      smtp_ssl: form.smtp_ssl,
      email_address: form.email_address,
      email_password: form.email_password,
    });
  };

  if (isLoading) {
    return <div className="max-w-xl mx-auto"><Skeleton /></div>;
  }

  if (isError) {
    return (
      <div className="max-w-xl mx-auto">
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded p-3">
          {(error as Error)?.message || "Ошибка загрузки статуса"}
        </div>
      </div>
    );
  }

  const isSaving = saveMutation.isPending;
  const isTesting = testMutation.isPending;

  return (
    <div className="max-w-xl mx-auto space-y-4">
      <h1 className="text-lg font-bold">Email-интеграция</h1>

      <SectionCard title="Провайдер">
        <Field label="Почтовый сервис">
          <select className="w-full border rounded px-3 py-2 text-sm bg-white"
            value={provider} onChange={(e) => handleProviderChange(e.target.value)}>
            <option value="">— Выберите провайдера —</option>
            {Object.entries(PROVIDER_PRESETS).map(([key, p]) => (
              <option key={key} value={key}>{p ? p.label : "Свой провайдер"}</option>
            ))}
          </select>
        </Field>
        {provider && provider !== "custom" && PROVIDER_PRESETS[provider] && (
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800 space-y-2">
            <div className="flex items-start gap-2">
              <span className="text-blue-500 mt-0.5 shrink-0">ⓘ</span>
              <span>{PROVIDER_PRESETS[provider]!.instructions}</span>
            </div>
            <a href={PROVIDER_PRESETS[provider]!.appPasswordUrl}
              target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-blue-700 underline hover:text-blue-900">
              Как получить пароль →
            </a>
          </div>
        )}
      </SectionCard>

      <SectionCard title="IMAP">
        <Field label="Сервер">
          <input className="w-full border rounded px-3 py-2 text-sm" value={form.imap_host}
            onChange={(e) => set("imap_host", e.target.value)} placeholder="imap.gmail.com" />
        </Field>
        <Field label="Порт">
          <input className="w-full border rounded px-3 py-2 text-sm" type="number" value={form.imap_port}
            onChange={(e) => set("imap_port", Number(e.target.value))} />
        </Field>
        <Field label="SSL">
          <input type="checkbox" className="w-4 h-4" checked={form.imap_ssl}
            onChange={(e) => set("imap_ssl", e.target.checked)} />
        </Field>
      </SectionCard>

      <SectionCard title="SMTP">
        <Field label="Сервер">
          <input className="w-full border rounded px-3 py-2 text-sm" value={form.smtp_host}
            onChange={(e) => set("smtp_host", e.target.value)} placeholder="smtp.gmail.com" />
        </Field>
        <Field label="Порт">
          <input className="w-full border rounded px-3 py-2 text-sm" type="number" value={form.smtp_port}
            onChange={(e) => set("smtp_port", Number(e.target.value))} />
        </Field>
        <Field label="SSL/TLS">
          <input type="checkbox" className="w-4 h-4" checked={form.smtp_ssl}
            onChange={(e) => set("smtp_ssl", e.target.checked)} />
        </Field>
      </SectionCard>

      <SectionCard title="Учётные данные">
        <Field label="Email">
          <input className="w-full border rounded px-3 py-2 text-sm" type="email" value={form.email_address}
            onChange={(e) => set("email_address", e.target.value)} placeholder="my@email.com" />
        </Field>
        <Field label="Пароль">
          <input className="w-full border rounded px-3 py-2 text-sm" type="password" value={form.email_password}
            onChange={(e) => set("email_password", e.target.value)} />
        </Field>
      </SectionCard>

      <SectionCard title="Дополнительно">
        <Field label="IMAP папка">
          <input className="w-full border rounded px-3 py-2 text-sm" value={form.folder}
            onChange={(e) => set("folder", e.target.value)} />
        </Field>
        <Field label="За цикл макс">
          <input className="w-full border rounded px-3 py-2 text-sm" type="number" value={form.max_per_cycle}
            onChange={(e) => set("max_per_cycle", Number(e.target.value))} />
        </Field>
        <Field label="Отмечать прочитанным">
          <input type="checkbox" className="w-4 h-4" checked={form.mark_as_seen}
            onChange={(e) => set("mark_as_seen", e.target.checked)} />
        </Field>
        <Field label="Интервал проверки">
          <input className="w-full border rounded px-3 py-2 text-sm" type="number" value={form.poll_interval_seconds}
            onChange={(e) => set("poll_interval_seconds", Number(e.target.value))} />
          <span className="text-gray-500 text-xs">сек</span>
        </Field>
      </SectionCard>

      <div className="flex gap-3">
        <button className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
          disabled={isSaving || isTesting} onClick={handleSave}>
          {isSaving ? "Сохранение..." : "Сохранить"}
        </button>
        <button className="bg-white text-gray-700 border border-gray-300 px-4 py-2 rounded text-sm hover:bg-gray-50 disabled:opacity-50"
          disabled={isSaving || isTesting} onClick={handleTest}>
          {isTesting ? (
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 border-2 border-gray-500 border-t-transparent rounded-full animate-spin" />
              Проверка...
            </span>
          ) : "Проверить подключение"}
        </button>
      </div>

      {status && (
        <div className="bg-white rounded shadow p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-2">Статус</h2>
          <div className="flex items-center gap-2 text-sm">
            {status.connected ? (
              <span className="w-3 h-3 bg-green-500 rounded-full" title="Подключено" />
            ) : status.configured ? (
              <span className="w-3 h-3 bg-red-500 rounded-full" title={`Ошибка: ${status.last_error || ""}`} />
            ) : (
              <span className="w-2 h-2 rounded-full bg-gray-400" />
            )}
            {status.connected ? "Подключено" : status.last_error ? `Ошибка: ${status.last_error}` : "Не настроено"}
          </div>
          <div className="text-xs text-gray-500 mt-1 space-y-0.5">
            <div>Последняя проверка: {status.last_poll_at ? new Date(status.last_poll_at).toLocaleTimeString() : "—"}</div>
            <div>Получено сегодня: {status.messages_fetched_today} писем</div>
          </div>
        </div>
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
