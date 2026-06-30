import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type CatalogPlugin } from "../api/client";
import InstallModal from "../components/InstallModal";

type Tab = "installed" | "available";

function statusLabel(status: string): string {
  return status === "running" ? "Работает" : "Остановлен";
}

export default function Plugins() {
  const [tab, setTab] = useState<Tab>("installed");
  const [showInstall, setShowInstall] = useState(false);
  const [updating, setUpdating] = useState<string | null>(null);
  const [updateLog, setUpdateLog] = useState<string | null>(null);
  const [catalogRefreshing, setCatalogRefreshing] = useState(false);
  const qc = useQueryClient();

  const { data: plugins, isLoading: pluginsLoading } = useQuery({
    queryKey: ["plugins"],
    queryFn: () => api.list<any>("plugins"),
  });

  const { data: catalog, isLoading: catalogLoading, refetch: refetchCatalog } = useQuery({
    queryKey: ["catalog"],
    queryFn: () => api.catalogPlugins(),
  });

  const startMut = useMutation({
    mutationFn: (name: string) => api.startPlugin(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plugins"] }),
  });

  const stopMut = useMutation({
    mutationFn: (name: string) => api.stopPlugin(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plugins"] }),
  });

  const deleteMut = useMutation({
    mutationFn: (name: string) => api.uninstallPlugin(name),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["plugins"] });
      qc.invalidateQueries({ queryKey: ["catalog"] });
    },
  });

  const handleRefreshCatalog = async () => {
    setCatalogRefreshing(true);
    await refetchCatalog();
    setCatalogRefreshing(false);
  };

  const handleUpdate = async (name: string) => {
    setUpdating(name);
    setUpdateLog(null);
    try {
      const res = await api.updatePlugin(name);
      setUpdateLog(res.output);
      qc.invalidateQueries({ queryKey: ["plugins"] });
      qc.invalidateQueries({ queryKey: ["catalog"] });
    } catch (e: any) {
      setUpdateLog(e.message);
    } finally {
      setUpdating(null);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Плагины</h1>
        <button
          className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700"
          onClick={() => setShowInstall(true)}
        >
          + Установить плагин
        </button>
      </div>

      <div className="flex gap-2 mb-4 border-b pb-2">
        <button
          className={`px-3 py-1.5 rounded-t text-sm font-medium ${tab === "installed" ? "bg-blue-600 text-white" : "text-gray-500 hover:text-gray-700"}`}
          onClick={() => setTab("installed")}
        >
          Установленные
        </button>
        <button
          className={`px-3 py-1.5 rounded-t text-sm font-medium ${tab === "available" ? "bg-blue-600 text-white" : "text-gray-500 hover:text-gray-700"}`}
          onClick={() => setTab("available")}
        >
          Доступные
        </button>
      </div>

      {tab === "installed" && (
        <>
          {pluginsLoading ? (
            <p>Загрузка…</p>
          ) : !plugins || plugins.length === 0 ? (
            <p className="text-gray-500">Нет установленных плагинов</p>
          ) : (
            <div className="grid grid-cols-3 gap-4">
              {plugins.map((p: any) => (
                <Link key={p.name} to={`/plugins/${p.name}`} className="bg-white rounded shadow p-4 block cursor-pointer hover:shadow-md">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`w-2 h-2 rounded-full ${p.status === "running" ? "bg-green-500" : "bg-gray-400"}`} />
                    <span className="font-medium">{p.name}</span>
                  </div>
                  {p.description && <div className="text-xs text-gray-500 mb-1">{p.description}</div>}
                  {(() => {
                    const iv = p.installed_version;
                    const lv = p.version;
                    if (iv && lv && iv !== lv) return <div className="text-xs text-gray-400 mb-1">v{iv} → v{lv}</div>;
                    if (iv) return <div className="text-xs text-gray-400 mb-1">v{iv}</div>;
                    if (lv) return <div className="text-xs text-gray-400 mb-1">v{lv}</div>;
                    return null;
                  })()}
                  <div className="text-xs text-gray-400 mb-2">Статус: {statusLabel(p.status)}</div>
                  <div className="flex flex-wrap gap-1.5" onClick={(e) => e.stopPropagation()}>
                    {p.status === "running" ? (
                      <button
                        className="text-xs bg-yellow-500 text-white px-2 py-1 rounded hover:bg-yellow-600 disabled:opacity-50"
                        onClick={() => stopMut.mutate(p.name)}
                        disabled={stopMut.isPending}
                      >
                        Остановить
                      </button>
                    ) : (
                      <button
                        className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700 disabled:opacity-50"
                        onClick={() => startMut.mutate(p.name)}
                        disabled={startMut.isPending}
                      >
                        Запустить
                      </button>
                    )}
                    {p.has_update && (
                      <button
                        className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700 disabled:opacity-50"
                        onClick={() => handleUpdate(p.name)}
                        disabled={updating === p.name}
                      >
                        {updating === p.name ? "..." : "Обновить"}
                      </button>
                    )}
                    <button
                      className="text-xs bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600 disabled:opacity-50"
                      onClick={() => { if (confirm(`Удалить плагин ${p.name}?`)) deleteMut.mutate(p.name); }}
                      disabled={deleteMut.isPending}
                    >
                      Удалить
                    </button>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </>
      )}

      {tab === "available" && (
        <>
          <div className="flex items-center justify-between mb-2">
            {catalogLoading ? <p>Загрузка…</p> : <span />}
            <button
              className="text-xs bg-gray-200 text-gray-700 px-3 py-1.5 rounded hover:bg-gray-300 disabled:opacity-50"
              onClick={handleRefreshCatalog}
              disabled={catalogRefreshing || catalogLoading}
            >
              {catalogRefreshing ? "Загружаю…" : "Обновить каталог"}
            </button>
          </div>
          {catalogLoading ? null : !catalog || catalog.length === 0 ? (
            <p className="text-gray-500">Нет доступных плагинов</p>
          ) : (
            <div className="grid grid-cols-3 gap-4">
              {catalog.map((p: CatalogPlugin) => (
                <Link key={p.name} to={`/plugins/${p.name}`} className="bg-white rounded shadow p-4 block cursor-pointer hover:shadow-md">
                  <div className="font-medium mb-1">{p.name}</div>
                  {p.description && <div className="text-xs text-gray-500 mb-1">{p.description}</div>}
                  {p.version && <div className="text-xs text-gray-400 mb-2">v{p.version}</div>}
                  {p.installed ? (
                    <span className="text-xs text-green-600">Установлено v{p.installed_version}</span>
                  ) : (
                    <button
                      className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
                      onClick={(e) => { e.stopPropagation(); setShowInstall(true); }}
                    >
                      Установить
                    </button>
                  )}
                </Link>
              ))}
            </div>
          )}
        </>
      )}

      {updateLog && (
        <div className="mt-4">
          <pre className="bg-gray-900 text-green-300 text-xs p-3 rounded max-h-40 overflow-auto">{updateLog}</pre>
        </div>
      )}

      {showInstall && <InstallModal onClose={() => setShowInstall(false)} />}
    </div>
  );
}