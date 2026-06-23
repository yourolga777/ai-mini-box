import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function PluginDetail() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [uninstalling, setUninstalling] = useState(false);
  const [confirmUninstall, setConfirmUninstall] = useState(false);
  const [tokenInput, setTokenInput] = useState("");
  const [tokenSource, setTokenSource] = useState<"existing" | "new">("existing");
  const [setupBusy, setSetupBusy] = useState(false);
  const [setupError, setSetupError] = useState("");
  const [actionBusy, setActionBusy] = useState("");
  const [actionResult, setActionResult] = useState("");

  const { data: plugin, isLoading } = useQuery({
    queryKey: ["plugin", name],
    queryFn: () => api.get<any>("plugins", name as any),
    enabled: !!name,
    refetchInterval: 3000,
  });

  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: () => api.getConfig(),
  });
  const hasToken = !!(config as any)?.telegram_token;
  const { data: logs } = useQuery({
    queryKey: ["plugin-logs", name],
    queryFn: () =>
      api.get<any>("plugins", name as any).then(() =>
        fetch(`/api/plugins/${name}/logs`).then((r) => r.json())
      ),
    enabled: !!name,
  });

  // refresh plugin status every 3s so daemon state updates
  useQuery({
    queryKey: ["plugin-status", name],
    queryFn: () => api.get<any>("plugins", name as any),
    enabled: !!name,
    refetchInterval: 3000,
  } as any);

  const doUninstall = async () => {
    setUninstalling(true);
    try {
      await api.uninstallPlugin(name!);
      qc.invalidateQueries({ queryKey: ["plugins"] });
      navigate("/plugins");
    } catch (e: any) {
      alert(e.message);
    } finally {
      setUninstalling(false);
      setConfirmUninstall(false);
    }
  };

  const saveToken = async () => {
    setSetupBusy(true);
    setSetupError("");
    try {
      await api.setConfig("telegram_token", tokenInput.trim());
      qc.invalidateQueries({ queryKey: ["plugin", name] });
      setTokenInput("");
    } catch (e: any) {
      setSetupError(e.message);
    } finally {
      setSetupBusy(false);
    }
  };

  const runAction = async (action: string) => {
    setActionBusy(action);
    setActionResult("");
    try {
      const r = await api.pluginAction(name!, action);
      setActionResult(r.output);
    } catch (e: any) {
      setActionResult(e.message);
    } finally {
      setActionBusy(action === "poll" ? "poll" : "");
    }
  };

  const toggleDaemon = async () => {
    if (plugin?.status === "running") {
      setActionBusy("stop");
      try {
        await api.stopPlugin(name!);
        qc.invalidateQueries({ queryKey: ["plugin", name] });
        setActionResult("Daemon stopped");
      } catch (e: any) {
        setActionResult(e.message);
      } finally {
        setActionBusy("");
      }
    } else {
      setActionBusy("start");
      try {
        await api.startPlugin(name!);
        qc.invalidateQueries({ queryKey: ["plugin", name] });
        setActionResult("Daemon started");
      } catch (e: any) {
        setActionResult(e.message);
      } finally {
        setActionBusy("");
      }
    }
  };

  if (isLoading) return <p>Loading…</p>;
  if (!plugin) return <p>Plugin not found.</p>;

  const isTelegram = plugin.name === "telegram";

  return (
    <div>
      <Link to="/plugins" className="text-blue-600 text-sm">
        &larr; Back to plugins
      </Link>
      <div className="flex items-center justify-between mt-2 mb-4">
        <h1 className="text-xl font-bold">{plugin.name}</h1>
        <div className="flex gap-2">
          {!confirmUninstall ? (
            <button
              className="text-red-600 border border-red-300 px-3 py-1.5 rounded text-sm hover:bg-red-50 disabled:opacity-50"
              onClick={() => setConfirmUninstall(true)}
              disabled={uninstalling}
            >
              Uninstall
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm text-red-600">Are you sure?</span>
              <button
                className="bg-red-600 text-white px-3 py-1.5 rounded text-sm hover:bg-red-700 disabled:opacity-50"
                onClick={doUninstall}
                disabled={uninstalling}
              >
                {uninstalling ? "Uninstalling..." : "Yes, uninstall"}
              </button>
              <button
                className="text-gray-500 px-3 py-1.5 rounded text-sm hover:bg-gray-100"
                onClick={() => setConfirmUninstall(false)}
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Token setup — only for telegram when no token */}
      {isTelegram && !hasToken && (
        <div className="bg-white rounded shadow p-4 mb-4 border border-blue-200">
          <h2 className="font-bold mb-3">🤖 Telegram Bot Setup</h2>

          <div className="flex gap-4 mb-4">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="radio"
                name="tokenSource"
                checked={tokenSource === "existing"}
                onChange={() => setTokenSource("existing")}
              />
              I already have a token
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="radio"
                name="tokenSource"
                checked={tokenSource === "new"}
                onChange={() => setTokenSource("new")}
              />
              Create a new bot
            </label>
          </div>

          {tokenSource === "existing" ? (
            <div className="space-y-3">
              <div className="text-sm text-gray-600 space-y-1">
                <p>1. Open <a href="https://t.me/BotFather" target="_blank" className="text-blue-600 underline">@BotFather</a> in Telegram</p>
                <p>2. Send <code className="bg-gray-100 px-1 rounded">/mybots</code></p>
                <p>3. Select your bot from the list</p>
                <p>4. Tap <strong>API Token</strong> button</p>
                <p>5. Copy the token and paste below</p>
              </div>
              <input
                className="w-full border rounded px-3 py-2 text-sm font-mono"
                placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                disabled={setupBusy}
              />
            </div>
          ) : (
            <div className="text-sm text-gray-600 space-y-1 mb-3">
              <p>1. Open <a href="https://t.me/BotFather" target="_blank" className="text-blue-600 underline">@BotFather</a> in Telegram</p>
              <p>2. Send <code className="bg-gray-100 px-1 rounded">/newbot</code></p>
              <p>3. Choose a name and username</p>
              <p>4. Copy the token and paste below</p>
              <input
                className="w-full border rounded px-3 py-2 text-sm font-mono mt-2"
                placeholder="Paste your token here"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                disabled={setupBusy}
              />
            </div>
          )}

          {setupError && (
            <div className="text-sm text-red-600 mt-2">{setupError}</div>
          )}

          <button
            className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50 mt-3"
            disabled={!tokenInput.trim() || setupBusy}
            onClick={saveToken}
          >
            {setupBusy ? "Saving..." : "Save Token"}
          </button>
        </div>
      )}

      {/* Plugin info card */}
      <div className="bg-white rounded shadow p-4 mb-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-500">Module</div>
            <div className="font-mono text-sm">{plugin.module}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Status</div>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`w-2 h-2 rounded-full ${plugin.status === "running" ? "bg-green-500" : "bg-gray-400"}`}
              />
              <span>{plugin.status}</span>
              {plugin.pid && <span className="text-xs text-gray-400">(PID {plugin.pid})</span>}
            </div>
          </div>
        </div>
      </div>

      {/* Actions — only for telegram with token */}
      {isTelegram && (
        <div className="bg-white rounded shadow p-4 mb-4">
          <h2 className="font-bold mb-3">Actions</h2>

          <div className="flex flex-wrap gap-3">
            <button
              className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              disabled={actionBusy === "poll"}
              onClick={() => runAction("poll")}
            >
              {actionBusy === "poll" ? (
                <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                "📩"
              )}
              {actionBusy === "poll" ? "Polling..." : "Poll now"}
            </button>

            <button
              className="bg-white text-gray-700 border border-gray-300 px-4 py-2 rounded text-sm hover:bg-gray-50 disabled:opacity-50 flex items-center gap-2"
              onClick={() => navigate("/messages")}
            >
              📋 View Messages
            </button>

            <button
              className={
                (plugin.status === "running"
                  ? "bg-red-600 hover:bg-red-700 text-white"
                  : "bg-green-600 hover:bg-green-700 text-white") +
                " px-4 py-2 rounded text-sm disabled:opacity-50 flex items-center gap-2"
              }
              disabled={actionBusy === "start" || actionBusy === "stop"}
              onClick={toggleDaemon}
            >
              {actionBusy === "start" || actionBusy === "stop" ? (
                <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : plugin.status === "running" ? (
                "⏹"
              ) : (
                "▶"
              )}
              {plugin.status === "running" ? "Stop daemon" : "Start daemon"}
            </button>
          </div>

          {actionResult && (
            <div className="mt-3 bg-gray-50 border border-gray-200 text-sm rounded p-2">
              {actionResult}
            </div>
          )}
        </div>
      )}

      {/* Logs */}
      <div className="bg-white rounded shadow p-4">
        <h2 className="font-bold mb-2">Logs</h2>
        <pre className="bg-gray-900 text-green-300 text-xs p-3 rounded max-h-64 overflow-auto">
          {((logs?.lines as string[]) ?? []).join("\n") || "(no logs)"}
        </pre>
      </div>
    </div>
  );
}
