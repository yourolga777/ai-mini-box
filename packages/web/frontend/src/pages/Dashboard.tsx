import { useState, useEffect, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { formatPrice } from "../helpers";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line, Bar, Doughnut } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler);

const PERIODS = [
  { label: "7 дней", value: 7 },
  { label: "30 дней", value: 30 },
  { label: "90 дней", value: 90 },
  { label: "Всё время", value: 0 },
];

function Skeleton() {
  return <div className="animate-pulse bg-gray-100 rounded h-32" />;
}

function WidgetError({ onRetry }: { onRetry: () => void }) {
  return <div className="text-sm text-red-500 p-4 text-center">Ошибка загрузки <button className="underline ml-2" onClick={onRetry}>Повторить</button></div>;
}

function formatShortDate(d: string) {
  const parts = d.split("-");
  if (parts.length < 3) return d;
  return `${parts[2]}.${parts[1]}`;
}

export default function Dashboard() {
  const qc = useQueryClient();
  const [period, setPeriod] = useState(30);

  const summaryQ = useQuery({
    queryKey: ["analytics-summary", period],
    queryFn: () => api.getAnalytics<any>("summary", { days: period }),
  });
  const messagesQ = useQuery({
    queryKey: ["analytics-messages", period],
    queryFn: () => api.getAnalytics<{ date: string; count: number }[]>("messages", { days: period }),
  });
  const ordersQ = useQuery({
    queryKey: ["analytics-orders", period],
    queryFn: () => api.getAnalytics<{ date: string; count: number }[]>("orders", { days: period }),
  });
  const revenueQ = useQuery({
    queryKey: ["analytics-revenue", period],
    queryFn: () => api.getAnalytics<{ date: string; total_kopecks: number }[]>("revenue", { days: period }),
  });
  const channelsQ = useQuery({
    queryKey: ["analytics-channels", period],
    queryFn: () => api.getAnalytics<{ source: string; count: number }[]>("channels", { days: period }),
  });
  const topContactsQ = useQuery({
    queryKey: ["analytics-top-contacts", period],
    queryFn: () => api.getAnalytics<{ id: number; name: string; total_spent: number; order_count: number }[]>("top-contacts", { limit: 10, days: period }),
  });
  const funnelQ = useQuery({
    queryKey: ["analytics-funnel", period],
    queryFn: () => api.getAnalytics<{ steps: { label: string; count: number }[] }>("funnel", { days: period }),
  });
  const forecastQ = useQuery({
    queryKey: ["analytics-forecast", period],
    queryFn: () => api.getAnalytics<{ predicted: { date: string; predicted: number; lower_bound: number; upper_bound: number }[] | null }>("forecast", { days: period }),
  });

  useEffect(() => {
    const interval = setInterval(() => {
      qc.invalidateQueries({ queryKey: ["analytics-summary"] });
    }, 60000);
    return () => clearInterval(interval);
  }, [qc]);

  const handleRefresh = useCallback(() => {
    qc.invalidateQueries({ queryKey: ["analytics"] });
  }, [qc]);

  const summary = summaryQ.data;

  const lineLabels = (messagesQ.data ?? []).map((r) => formatShortDate(r.date));
  const lineData = {
    labels: lineLabels,
    datasets: [
      {
        label: "Сообщения",
        data: (messagesQ.data ?? []).map((r) => r.count),
        borderColor: "#3b82f6",
        backgroundColor: "transparent",
        tension: 0.3,
      },
      {
        label: "Заказы",
        data: (ordersQ.data ?? []).map((r) => r.count),
        borderColor: "#10b981",
        backgroundColor: "transparent",
        tension: 0.3,
      },
      {
        label: "Выручка (₽)",
        data: (revenueQ.data ?? []).map((r) => Math.round(r.total_kopecks / 100)),
        borderColor: "#f59e0b",
        backgroundColor: "transparent",
        tension: 0.3,
        yAxisID: "y1",
      },
    ],
  };

  const channelsData = {
    labels: (channelsQ.data ?? []).map((r) => r.source),
    datasets: [{
      data: (channelsQ.data ?? []).map((r) => r.count),
      backgroundColor: ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"],
    }],
  };

  const funnelSteps = funnelQ.data?.steps ?? [];

  const forecast = forecastQ.data?.predicted ?? null;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Панель управления</h1>
        <div className="flex items-center gap-2">
          <select
            className="border rounded px-2 py-1.5 text-sm"
            value={period}
            onChange={(e) => setPeriod(Number(e.target.value))}
          >
            {PERIODS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
          <button className="text-sm text-blue-600 underline" onClick={handleRefresh}>Обновить</button>
        </div>
      </div>

      {summaryQ.isLoading ? (
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} />)}
        </div>
      ) : summaryQ.error ? (
        <WidgetError onRetry={() => qc.invalidateQueries({ queryKey: ["analytics-summary"] })} />
      ) : (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded shadow p-4">
            <div className="text-gray-500 text-xs uppercase">Новые сообщения</div>
            <div className="text-2xl font-bold mt-1">{summary?.new_messages ?? "…"}</div>
          </div>
          <div className="bg-white rounded shadow p-4">
            <div className="text-gray-500 text-xs uppercase">Новые контакты</div>
            <div className="text-2xl font-bold mt-1">{summary?.new_contacts ?? "…"}</div>
          </div>
          <div className="bg-white rounded shadow p-4">
            <div className="text-gray-500 text-xs uppercase">Новые заказы</div>
            <div className="text-2xl font-bold mt-1">{summary?.new_orders ?? "…"}</div>
          </div>
          <div className="bg-white rounded shadow p-4">
            <div className="text-gray-500 text-xs uppercase">Выручка сегодня</div>
            <div className="text-2xl font-bold mt-1">{summary ? formatPrice(summary.revenue_today) : "…"}</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded shadow p-4">
          <h2 className="font-semibold text-sm mb-2">Динамика</h2>
          {messagesQ.isLoading ? <Skeleton /> : messagesQ.error ? <WidgetError onRetry={() => qc.invalidateQueries({ queryKey: ["analytics-messages"] })} /> : lineLabels.length === 0 ? <p className="text-sm text-gray-400">Нет данных</p> : (
            <Line data={lineData} options={{ responsive: true, scales: { y: { beginAtZero: true }, y1: { position: "right", beginAtZero: true, grid: { drawOnChartArea: false } } } }} />
          )}
        </div>

        <div className="bg-white rounded shadow p-4">
          <h2 className="font-semibold text-sm mb-2">Каналы</h2>
          {channelsQ.isLoading ? <Skeleton /> : channelsQ.error ? <WidgetError onRetry={() => qc.invalidateQueries({ queryKey: ["analytics-channels"] })} /> : (channelsQ.data ?? []).length === 0 ? <p className="text-sm text-gray-400">Нет данных</p> : (
            <div className="max-w-[200px] mx-auto"><Doughnut data={channelsData} /></div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded shadow p-4">
          <h2 className="font-semibold text-sm mb-2">Топ контактов</h2>
          {topContactsQ.isLoading ? <Skeleton /> : topContactsQ.error ? <WidgetError onRetry={() => qc.invalidateQueries({ queryKey: ["analytics-top-contacts"] })} /> : (topContactsQ.data ?? []).length === 0 ? <p className="text-sm text-gray-400">Нет данных</p> : (
            <ul className="text-sm space-y-2">
              {(topContactsQ.data ?? []).map((c, i) => (
                <li key={c.id} className="flex items-center justify-between">
                  <span>{i + 1}. {c.name}</span>
                  <span className="font-medium">{formatPrice(c.total_spent)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-white rounded shadow p-4">
          <h2 className="font-semibold text-sm mb-2">Воронка</h2>
          {funnelQ.isLoading ? <Skeleton /> : funnelQ.error ? <WidgetError onRetry={() => qc.invalidateQueries({ queryKey: ["analytics-funnel"] })} /> : funnelSteps.length === 0 ? <p className="text-sm text-gray-400">Нет данных</p> : (
            <Bar
              data={{
                labels: funnelSteps.map((s) => s.label),
                datasets: [{ label: "Количество", data: funnelSteps.map((s) => s.count), backgroundColor: ["#3b82f6", "#6366f1", "#8b5cf6", "#a855f7"] }],
              }}
              options={{ responsive: true, scales: { y: { beginAtZero: true } } }}
            />
          )}
        </div>
      </div>

      {forecast && (
        <div className="bg-white rounded shadow p-4 mb-6">
          <h2 className="font-semibold text-sm mb-2">Прогноз на 30 дней</h2>
          {forecastQ.isLoading ? <Skeleton /> : (
            <Line
              data={{
                labels: forecast.map((p) => formatShortDate(p.date)),
                datasets: [
                  { label: "Прогноз", data: forecast.map((p) => Math.round(p.predicted / 100)), borderColor: "#f59e0b", backgroundColor: "transparent", tension: 0.3 },
                  { label: "Верхняя граница", data: forecast.map((p) => Math.round(p.upper_bound / 100)), borderColor: "#f59e0b", backgroundColor: "rgba(245, 158, 11, 0.08)", pointRadius: 0, fill: "+1", tension: 0.3 },
                  { label: "Нижняя граница", data: forecast.map((p) => Math.round(p.lower_bound / 100)), borderColor: "#f59e0b", backgroundColor: "transparent", pointRadius: 0, tension: 0.3 },
                ],
              }}
              options={{ responsive: true, scales: { y: { beginAtZero: true } } }}
            />
          )}
        </div>
      )}
    </div>
  );
}
