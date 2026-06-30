import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { api } from "../api/client";

type ViewMode = "day" | "week" | "month" | "year";

type TaskItem = {
  id: number;
  title: string;
  description?: string;
  due_date: string;
  due_time?: string;
  priority: "low" | "medium" | "high";
  status: string;
  contact_id?: number;
  assignee?: string;
};

const MONTHS = [
  "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
];

const DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

  const PRIORITY_LABELS: Record<string, string> = {
    high: "Высокий",
    medium: "Средний",
    low: "Низкий",
  };

  const PRIORITY_COLORS: Record<string, string> = {
    high: "bg-red-500",
    medium: "bg-yellow-500",
    low: "bg-green-500",
  };

function formatDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function addDays(d: Date, n: number): Date {
  const r = new Date(d);
  r.setDate(r.getDate() + n);
  return r;
}

function startOfWeek(d: Date): Date {
  const r = new Date(d);
  const day = r.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  r.setDate(r.getDate() + diff);
  return r;
}

function daysInMonth(y: number, m: number): number {
  return new Date(y, m + 1, 0).getDate();
}

function startDayOfWeek(y: number, m: number): number {
  const d = new Date(y, m, 1);
  return d.getDay() === 0 ? 6 : d.getDay() - 1;
}

export default function Calendar() {
  const qc = useQueryClient();
  const [view, setView] = useState<ViewMode>("month");
  const [cursor, setCursor] = useState(() => new Date());
  const [showPopup, setShowPopup] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [newTime, setNewTime] = useState("");
  const [newPriority, setNewPriority] = useState<"low" | "medium" | "high">("medium");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [modalTitle, setModalTitle] = useState("");
  const [modalDate, setModalDate] = useState(formatDate(new Date()));
  const [modalTime, setModalTime] = useState("");
  const [modalPriority, setModalPriority] = useState<"low" | "medium" | "high">("medium");
  const [monthPopupDay, setMonthPopupDay] = useState<string | null>(null);

  const monthStr = `${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, "0")}`;

  const { data: tasks = [] } = useQuery({
    queryKey: ["tasks", view === "year" ? `${cursor.getFullYear()}` : monthStr],
    queryFn: () => {
      if (view === "year") {
        return api.list<TaskItem>("tasks");
      }
      return api.list<TaskItem>(`tasks?month=${monthStr}`);
    },
  });

  const createTask = useMutation({
    mutationFn: (body: any) => api.create("tasks", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
      setNewTitle("");
      setNewTime("");
      setNewPriority("medium");
    },
  });

  const updateTask = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => api.update("tasks", id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });

  const deleteTask = useMutation({
    mutationFn: (id: number) => api.delete("tasks", id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });

  const today = formatDate(new Date());

  function nav(delta: number) {
    const c = new Date(cursor);
    if (view === "day") c.setDate(c.getDate() + delta);
    else if (view === "week") c.setDate(c.getDate() + delta * 7);
    else if (view === "month") c.setMonth(c.getMonth() + delta);
    else if (view === "year") c.setFullYear(c.getFullYear() + delta);
    setCursor(c);
  }

  function navToday() {
    setCursor(new Date());
  }

  const tasksByDate = useMemo(() => {
    const map: Record<string, TaskItem[]> = {};
    for (const t of tasks) {
      const d = t.due_date;
      if (!map[d]) map[d] = [];
      map[d].push(t);
    }
    return map;
  }, [tasks]);

  function handleAddTask(dateStr: string) {
    if (!newTitle.trim()) return;
    createTask.mutate({
      title: newTitle.trim(),
      due_date: dateStr,
      due_time: newTime || null,
      priority: newPriority,
    });
    setShowPopup(null);
  }

  function handleCreateFromModal() {
    if (!modalTitle.trim()) return;
    createTask.mutate({
      title: modalTitle.trim(),
      due_date: modalDate,
      due_time: modalTime || null,
      priority: modalPriority,
    });
    setShowCreateModal(false);
    setModalTitle("");
    setModalTime("");
    setModalPriority("medium");
  }

  function handleToggleTask(task: TaskItem) {
    updateTask.mutate({
      id: task.id,
      data: { status: task.status === "completed" ? "pending" : "completed" },
    });
  }

  // --- Day View ---
  if (view === "day") {
    const dateStr = formatDate(cursor);
    const dayTasks = tasksByDate[dateStr] || [];
    return (
      <>
        <CalendarShell view={view} onView={setView} cursor={cursor} onNav={nav} onToday={navToday} onAddTask={() => { setShowCreateModal(true); }}>
          <div className="text-lg font-semibold mb-4">{cursor.toLocaleDateString("ru-RU", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}</div>
          <div className="space-y-2">
            {dayTasks.length === 0 && <p className="text-gray-400 text-sm">Нет задач</p>}
            {dayTasks.map((t) => (
              <TaskCard key={t.id} task={t} onToggle={handleToggleTask} onDelete={(id) => deleteTask.mutate(id)} />
            ))}
          </div>
          <QuickAdd dateStr={dateStr} onAdd={handleAddTask} title={newTitle} onTitle={setNewTitle} time={newTime} onTime={setNewTime} priority={newPriority} onPriority={setNewPriority} />
        </CalendarShell>
        <NewTaskModal show={showCreateModal} title={modalTitle} onTitle={setModalTitle} date={modalDate} onDate={setModalDate} time={modalTime} onTime={setModalTime} priority={modalPriority} onPriority={setModalPriority} onCreate={handleCreateFromModal} onClose={() => setShowCreateModal(false)} busy={createTask.isPending} />
      </>
    );
  }

  // --- Week View ---
  if (view === "week") {
    const start = startOfWeek(cursor);
    const days = Array.from({ length: 7 }, (_, i) => addDays(start, i));
    return (
      <>
        <CalendarShell view={view} onView={setView} cursor={cursor} onNav={nav} onToday={navToday} onAddTask={() => { setModalDate(formatDate(cursor)); setShowCreateModal(true); }}>
          <div className="grid grid-cols-7 gap-2">
            {days.map((d) => {
              const ds = formatDate(d);
              const dayTasks = tasksByDate[ds] || [];
              const isToday = ds === today;
              return (
                <div key={ds} className={`border rounded p-2 min-h-[120px] ${isToday ? "border-blue-500 bg-blue-50" : "border-gray-200"}`}>
                  <div className="text-sm font-semibold mb-1 text-center">{d.getDate()} {MONTHS[d.getMonth()].slice(0, 3)}</div>
                  {dayTasks.map((t) => (
                    <div key={t.id} className={`text-xs p-1 mb-1 rounded cursor-pointer ${t.status === "completed" ? "line-through opacity-50" : ""} ${PRIORITY_COLORS[t.priority]} text-white`}
                      onClick={() => handleToggleTask(t)}>
                      {t.due_time && <span className="font-mono">{t.due_time} </span>}
                      {t.title}
                    </div>
                  ))}
                  <button className="text-xs text-blue-500 mt-1" onClick={() => { setShowPopup(ds); setNewTitle(""); setNewTime(""); }}>+</button>
                  {showPopup === ds && (
                    <QuickAdd dateStr={ds} onAdd={handleAddTask} title={newTitle} onTitle={setNewTitle} time={newTime} onTime={setNewTime} priority={newPriority} onPriority={setNewPriority} />
                  )}
                </div>
              );
            })}
          </div>
        </CalendarShell>
        <NewTaskModal show={showCreateModal} title={modalTitle} onTitle={setModalTitle} date={modalDate} onDate={setModalDate} time={modalTime} onTime={setModalTime} priority={modalPriority} onPriority={setModalPriority} onCreate={handleCreateFromModal} onClose={() => setShowCreateModal(false)} busy={createTask.isPending} />
      </>
    );
  }

  // --- Month View ---
  if (view === "month") {
    const y = cursor.getFullYear();
    const m = cursor.getMonth();
    const dim = daysInMonth(y, m);
    const sdow = startDayOfWeek(y, m);
    const cells: (number | null)[] = Array(sdow).fill(null);
    for (let d = 1; d <= dim; d++) cells.push(d);
    while (cells.length % 7 !== 0) cells.push(null);
    const popupTasks = monthPopupDay ? tasksByDate[monthPopupDay] || [] : [];
    return (
      <>
        <CalendarShell view={view} onView={setView} cursor={cursor} onNav={nav} onToday={navToday} onAddTask={() => { setModalDate(formatDate(cursor)); setShowCreateModal(true); }}>
          <div className="grid grid-cols-7 text-center text-sm font-semibold text-gray-500 mb-1">
            {DAYS.map((d) => (<div key={d} className="py-1">{d}</div>))}
          </div>
          <div className="grid grid-cols-7 gap-1">
            {cells.map((day, i) => {
              if (day === null) return <div key={`e-${i}`} />;
              const ds = formatDate(new Date(y, m, day));
              const dayTasks = tasksByDate[ds] || [];
              const isToday = ds === today;
              return (
                <div key={ds}
                  className={`border rounded p-1 min-h-[80px] cursor-pointer hover:bg-gray-100 transition ${isToday ? "border-blue-500 bg-blue-50" : "border-gray-200"}`}
                  onClick={() => setMonthPopupDay(monthPopupDay === ds ? null : ds)}>
                  <div className="text-xs font-semibold mb-1">{day}</div>
                  {dayTasks.slice(0, 3).map((t) => (
                    <div key={t.id} className={`text-[10px] px-1 rounded mb-0.5 truncate text-white ${PRIORITY_COLORS[t.priority]} ${t.status === "completed" ? "line-through opacity-50" : ""}`}>
                      {t.title}
                    </div>
                  ))}
                  {dayTasks.length > 3 && <div className="text-[10px] text-gray-400">+{dayTasks.length - 3}</div>}
                </div>
              );
            })}
          </div>

          {monthPopupDay && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setMonthPopupDay(null)}>
              <div className="bg-white rounded shadow-lg p-4 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-bold">
                    {new Date(monthPopupDay).toLocaleDateString("ru-RU", { day: "numeric", month: "long" })}
                  </h3>
                  <button className="text-gray-400 hover:text-gray-600 text-lg" onClick={() => setMonthPopupDay(null)}>&times;</button>
                </div>
                {popupTasks.length === 0 ? (
                  <p className="text-sm text-gray-400 mb-3">Нет задач</p>
                ) : (
                  <div className="space-y-1 mb-3 max-h-48 overflow-y-auto">
                    {popupTasks.map((t) => (
                      <div key={t.id} className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={t.status === "completed"} onChange={() => handleToggleTask(t)} className="cursor-pointer" />
                        <span className={`flex-1 ${t.status === "completed" ? "line-through text-gray-400" : ""}`}>
                          {t.due_time && <span className="font-mono text-xs mr-1">{t.due_time}</span>}
                          {t.title}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded text-white ${PRIORITY_COLORS[t.priority]}`}>{PRIORITY_LABELS[t.priority]}</span>
                      </div>
                    ))}
                  </div>
                )}
                <div className="border-t pt-3">
                  <QuickAdd dateStr={monthPopupDay} onAdd={(d) => { handleAddTask(d); setMonthPopupDay(null); }}
                    title={newTitle} onTitle={setNewTitle} time={newTime} onTime={setNewTime}
                    priority={newPriority} onPriority={setNewPriority} />
                </div>
              </div>
            </div>
          )}
        </CalendarShell>
        <NewTaskModal show={showCreateModal} title={modalTitle} onTitle={setModalTitle} date={modalDate} onDate={setModalDate} time={modalTime} onTime={setModalTime} priority={modalPriority} onPriority={setModalPriority} onCreate={handleCreateFromModal} onClose={() => setShowCreateModal(false)} busy={createTask.isPending} />
      </>
    );
  }

  // --- Year View ---
  if (view === "year") {
    const y = cursor.getFullYear();
    return (
      <>
        <CalendarShell view={view} onView={setView} cursor={cursor} onNav={nav} onToday={navToday} onAddTask={() => { setModalDate(formatDate(cursor)); setShowCreateModal(true); }}>
          <div className="grid grid-cols-3 gap-4">
            {Array.from({ length: 12 }, (_, m) => {
              const dim = daysInMonth(y, m);
              return (
                <div key={m} className="border rounded p-2">
                  <div className="text-sm font-semibold mb-1">{MONTHS[m]}</div>
                  <div className="grid grid-cols-7 text-[10px] text-gray-400 mb-1">
                    {DAYS.map((d) => (<div key={d} className="text-center">{d[0]}</div>))}
                  </div>
                  <div className="grid grid-cols-7 text-[10px] gap-0.5">
                    {Array.from({ length: startDayOfWeek(y, m) }, (_, i) => <div key={`p-${i}`} />)}
                    {Array.from({ length: dim }, (_, d) => {
                      const ds = formatDate(new Date(y, m, d + 1));
                      const hasTasks = (tasksByDate[ds]?.length ?? 0) > 0;
                      const isToday = ds === today;
                      return (
                        <div key={d + 1}
                          className={`text-center rounded cursor-pointer hover:bg-gray-200 ${isToday ? "bg-blue-500 text-white" : ""} ${hasTasks ? "font-bold" : ""}`}
                          onClick={() => { setCursor(new Date(y, m, d + 1)); setView("day"); }}>
                          {d + 1}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </CalendarShell>
        <NewTaskModal show={showCreateModal} title={modalTitle} onTitle={setModalTitle} date={modalDate} onDate={setModalDate} time={modalTime} onTime={setModalTime} priority={modalPriority} onPriority={setModalPriority} onCreate={handleCreateFromModal} onClose={() => setShowCreateModal(false)} busy={createTask.isPending} />
      </>
    );
  }

  return null;
}

// --- Sub-components ---

function CalendarShell({ view, onView, cursor, onNav, onToday, onAddTask, children }: {
  view: ViewMode;
  onView: (v: ViewMode) => void;
  cursor: Date;
  onNav: (d: number) => void;
  onToday: () => void;
  onAddTask: () => void;
  children: React.ReactNode;
}) {
  const views: ViewMode[] = ["day", "week", "month", "year"];
  const title =
    view === "year"
      ? `${cursor.getFullYear()}`
      : `${MONTHS[cursor.getMonth()]} ${cursor.getFullYear()}`;
  return (
    <div>
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <button onClick={() => onNav(-1)} className="px-3 py-1 border rounded text-sm hover:bg-gray-100">◀</button>
        <button onClick={onToday} className="px-3 py-1 border rounded text-sm hover:bg-gray-100 font-semibold">Сегодня</button>
        <button onClick={() => onNav(1)} className="px-3 py-1 border rounded text-sm hover:bg-gray-100">▶</button>
        <span className="text-lg font-bold flex-1">{title}</span>
        <button onClick={onAddTask} className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">+ Новая задача</button>
        <div className="flex gap-1">
          {views.map((v) => (
            <button key={v} onClick={() => onView(v)}
              className={`px-3 py-1 rounded text-sm capitalize ${view === v ? "bg-blue-600 text-white" : "border hover:bg-gray-100"}`}>
              {v === "day" ? "День" : v === "week" ? "Неделя" : v === "month" ? "Месяц" : "Год"}
            </button>
          ))}
        </div>
      </div>
      {children}
    </div>
  );
}

function TaskCard({ task, onToggle, onDelete }: { task: TaskItem; onToggle: (t: TaskItem) => void; onDelete: (id: number) => void }) {
  const [showDel, setShowDel] = useState(false);
  return (
    <div className={`flex items-center gap-2 p-2 border rounded transition ${task.status === "completed" ? "bg-gray-100 opacity-60" : "bg-white"}`}>
      <input type="checkbox" checked={task.status === "completed"} onChange={() => onToggle(task)} className="cursor-pointer" />
      <div className={`flex-1 ${task.status === "completed" ? "line-through" : ""}`}>
        <span className="font-medium">{task.title}</span>
        {task.due_time && <span className="text-gray-500 ml-2 text-sm">{task.due_time}</span>}
        {task.assignee && <span className="text-gray-400 ml-2 text-sm">@{task.assignee}</span>}
        <span className={`ml-2 text-xs px-1.5 py-0.5 rounded text-white ${PRIORITY_COLORS[task.priority]}`}>{PRIORITY_LABELS[task.priority]}</span>
      </div>
      <button onClick={() => { if (showDel || window.confirm(`Удалить "${task.title}"?`)) { onDelete(task.id); } else { setShowDel(true); } }}
        className="text-red-500 text-sm hover:text-red-700">✕</button>
    </div>
  );
}

function QuickAdd({ dateStr, onAdd, title, onTitle, time, onTime, priority, onPriority }: {
  dateStr: string;
  onAdd: (d: string) => void;
  title: string;
  onTitle: (v: string) => void;
  time: string;
  onTime: (v: string) => void;
  priority: "low" | "medium" | "high";
  onPriority: (v: "low" | "medium" | "high") => void;
}) {
  return (
    <div className="mt-4 p-3 border rounded bg-gray-50">
      <div className="flex gap-2 mb-2">
        <input value={title} onChange={(e) => onTitle(e.target.value)}
          placeholder="Новая задача..." className="flex-1 border rounded px-2 py-1 text-sm" />
        <input value={time} onChange={(e) => onTime(e.target.value)} placeholder="00:00"
          className="w-16 border rounded px-2 py-1 text-sm" />
        <select value={priority} onChange={(e) => onPriority(e.target.value as any)}
          className="border rounded px-2 py-1 text-sm">
          <option value="low">Низкий</option>
          <option value="medium">Средний</option>
          <option value="high">Высокий</option>
        </select>
        <button onClick={() => onAdd(dateStr)} className="bg-blue-600 text-white px-3 py-1 rounded text-sm">+</button>
      </div>
    </div>
  );
}

function NewTaskModal({ show, title, onTitle, date, onDate, time, onTime, priority, onPriority, onCreate, onClose, busy }: {
  show: boolean;
  title: string;
  onTitle: (v: string) => void;
  date: string;
  onDate: (v: string) => void;
  time: string;
  onTime: (v: string) => void;
  priority: "low" | "medium" | "high";
  onPriority: (v: "low" | "medium" | "high") => void;
  onCreate: () => void;
  onClose: () => void;
  busy: boolean;
}) {
  if (!show) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="bg-white rounded shadow-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold">Новая задача</h3>
          <button className="text-gray-400 hover:text-gray-600 text-lg" onClick={onClose}>&times;</button>
        </div>
        <div className="space-y-3">
          <input value={title} onChange={(e) => onTitle(e.target.value)}
            placeholder="Название задачи" className="w-full border rounded px-3 py-2 text-sm" autoFocus />
          <input value={date} onChange={(e) => onDate(e.target.value)}
            type="date" className="w-full border rounded px-3 py-2 text-sm" />
          <input value={time} onChange={(e) => onTime(e.target.value)}
            type="time" className="w-full border rounded px-3 py-2 text-sm" />
          <select value={priority} onChange={(e) => onPriority(e.target.value as any)}
            className="w-full border rounded px-3 py-2 text-sm">
            <option value="low">Низкий приоритет</option>
            <option value="medium">Средний приоритет</option>
            <option value="high">Высокий приоритет</option>
          </select>
          <button onClick={onCreate} disabled={!title.trim() || busy}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50">
            {busy ? "Создание..." : "Создать"}
          </button>
        </div>
      </div>
    </div>
  );
}
