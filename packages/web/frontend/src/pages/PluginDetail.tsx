import { useState, startTransition } from "react";
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
  const [detectedChatIds, setDetectedChatIds] = useState<number[]>([]);
  const [newChatId, setNewChatId] = useState("");

  const { data: plugin, isLoading } = useQuery({
    queryKey: ["plugin", name],
    queryFn: () => api.get<any>("plugins", name as any),
    enabled: !!name,
    refetchInterval: actionBusy ? false : 3000,
  });

  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: () => api.getConfig(),
  });
  const hasToken = !!(config as any)?.telegram_token;
  const botUsername: string = (config as any)?.telegram_bot_username ?? "";
  const botName: string = (config as any)?.telegram_bot_name ?? "";
  const allowedChatIds: number[] = (config as any)?.telegram_allowed_chat_ids ?? [];

  const { data: logs } = useQuery({
    queryKey: ["plugin-logs", name],
    queryFn: () =>
      api.get<any>("plugins", name as any).then(() =>
        fetch(`/api/plugins/${name}/logs`).then((r) => r.json())
      ),
    enabled: !!name,
  });

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
      await api.verifyToken(name!);
      qc.invalidateQueries({ queryKey: ["plugin", name] });
      qc.invalidateQueries({ queryKey: ["config"] });
      setTokenInput("");
    } catch (e: any) {
      setSetupError(e.message);
    } finally {
      setSetupBusy(false);
    }
  };

  const addChatId = async () => {
    const ids = new Set(allowedChatIds);
    ids.add(Number(newChatId));
    try {
      await api.setConfig("telegram_allowed_chat_ids", JSON.stringify([...ids]));
      qc.invalidateQueries({ queryKey: ["config"] });
      setNewChatId("");
    } catch (e: any) {
      setSetupError(e.message);
    }
  };

  const addDetectedChatId = async (cid: number) => {
    const ids = new Set(allowedChatIds);
    ids.add(cid);
    try {
      await api.setConfig("telegram_allowed_chat_ids", JSON.stringify([...ids]));
      qc.invalidateQueries({ queryKey: ["config"] });
      setDetectedChatIds((prev) => prev.filter((id) => id !== cid));
    } catch (e: any) {
      setSetupError(e.message);
    }
  };

  const removeChatId = async (cid: number) => {
    const ids = allowedChatIds.filter((id) => id !== cid);
    try {
      await api.setConfig("telegram_allowed_chat_ids", JSON.stringify(ids));
      qc.invalidateQueries({ queryKey: ["config"] });
    } catch (e: any) {
      setSetupError(e.message);
    }
  };

  const runAction = async (action: string) => {
    setActionBusy(action);
    setActionResult("");
    setDetectedChatIds([]);
    try {
      const r = await api.pluginAction(name!, action);
      if (r.detected_chat_ids?.length) {
        setDetectedChatIds(r.detected_chat_ids);
      }
      if (action === "poll") {
        qc.invalidateQueries({ queryKey: ["messages"] });
      }
      setActionResult(r.output);
    } catch (e: any) {
      setActionResult(e.message);
    } finally {
      setActionBusy("");
    }
  };

  const toggleDaemon = async () => {
    if (plugin?.status === "running") {
      setActionBusy("stop");
      try {
        await api.stopPlugin(name!);
        startTransition(() => {
          qc.invalidateQueries({ queryKey: ["plugin", name] });
          setActionResult("Daemon stopped");
          setActionBusy("");
        });
      } catch (e: any) {
        startTransition(() => {
          setActionResult(e.message);
          setActionBusy("");
        });
      }
    } else {
      setActionBusy("start");
      try {
        await api.startPlugin(name!);
        startTransition(() => {
          qc.invalidateQueries({ queryKey: ["plugin", name] });
          setActionResult("Daemon started");
          setActionBusy("");
        });
      } catch (e: any) {
        startTransition(() => {
          setActionResult(e.message);
          setActionBusy("");
        });
      }
    }
  };

  if (isLoading) return <p>Loading…</p>;
  if (!plugin) return <p>Plugin not found.</p>;

  const isTelegram = plugin.name === "telegram";

  return (
    <div key={"app-plugin-" + name}>
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

      {/* Token setup — only for telegram */}
      {isTelegram && !hasToken && (
        <div className="bg-white rounded shadow p-4 mb-4 border border-blue-200">
          <h2 className="font-bold mb-3">Telegram Bot Setup</h2>

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

      {/* Connected state — shown when token is already saved */}
      {isTelegram && hasToken && (
        <div className="bg-white rounded shadow p-4 mb-4 border border-green-200">
          <div className="flex items-center gap-3">
            <span className="w-3 h-3 bg-green-500 rounded-full" />
            <div>
              <span className="font-bold text-green-700">Bot connected</span>
              {botUsername && (
                <span className="text-green-600 ml-2">as @{botUsername}</span>
              )}
              {botName && !botUsername && (
                <span className="text-green-600 ml-2">({botName})</span>
              )}
            </div>
            <button
              className="ml-auto text-xs text-gray-500 underline hover:text-gray-700"
              onClick={async () => {
                try {
                  await api.verifyToken(name!);
                  qc.invalidateQueries({ queryKey: ["config"] });
                } catch (_) {}
              }}
            >
              Re-verify
            </button>
          </div>

          {/* Guideline steps */}
          <div className="mt-4 bg-blue-50 border border-blue-100 rounded p-3 text-sm text-gray-700 space-y-2">
            <p className="font-semibold text-blue-800">Next steps</p>
            <ol className="list-decimal list-inside space-y-1">
              <li>
                Send a message to the bot {botUsername ? (
                  <a href={`https://t.me/${botUsername}`} target="_blank" className="text-blue-600 underline font-mono">@{botUsername}</a>
                ) : "username"} in Telegram, or to the phone number linked via Telegram Business
              </li>
              <li>
                Press <strong>Poll now</strong> below — the bot will find your chat
              </li>
              <li>
                A detected chat ID will appear — click <strong>Add to allowed</strong>
              </li>
              <li>
                Press <strong>Start daemon</strong> — the bot will receive messages automatically
              </li>
            </ol>
          </div>
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
                className={`w-2 h-2 rounded-full ${plugin.status === "running" || (isTelegram && hasToken) ? "bg-green-500" : "bg-gray-400"}`}
              />
              <span>
                {plugin.status === "running"
                  ? "running"
                  : isTelegram && hasToken
                    ? "configured"
                    : plugin.status}
              </span>
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
              <div>{actionResult}</div>
              {detectedChatIds.length > 0 && (
                <div className="mt-3 border-t border-gray-200 pt-2">
                  <p className="text-xs text-gray-500 mb-2 font-semibold">Detected chats</p>
                  {detectedChatIds.map((cid) => {
                    const alreadyAllowed = allowedChatIds.includes(cid);
                    return (
                      <div key={cid} className="flex items-center justify-between bg-green-50 border border-green-200 rounded px-3 py-2 mb-1">
                        <div>
                          <span className="font-mono text-xs font-bold">{cid}</span>
                          <span className="text-xs text-gray-500 ml-2">
                            {alreadyAllowed ? "(already allowed)" : "new"}
                          </span>
                        </div>
                        <button
                          className={`text-xs font-medium px-2 py-1 rounded ${alreadyAllowed ? "text-gray-400 cursor-default" : "text-green-700 bg-green-100 hover:bg-green-200"}`}
                          onClick={() => !alreadyAllowed && addDetectedChatId(cid)}
                          disabled={alreadyAllowed}
                        >
                          {alreadyAllowed ? "Added" : "Add to allowed"}
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Allowed Chats — only for telegram with token */}
      {isTelegram && hasToken && (
        <div className="bg-white rounded shadow p-4 mb-4">
          <h2 className="font-bold mb-3">Allowed Chats</h2>

          {allowedChatIds.length > 0 ? (
            <div className="flex flex-wrap gap-2 mb-3">
              {allowedChatIds.map((cid) => (
                <span
                  key={cid}
                  className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 text-xs font-mono px-2 py-1 rounded border border-blue-200"
                >
                  {cid}
                  <button
                    className="text-blue-400 hover:text-red-500 ml-1"
                    onClick={() => removeChatId(cid)}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 mb-3">
              No chats allowed. Messages from all chats will be accepted.
            </p>
          )}

          <div className="flex gap-2">
            <input
              className="border rounded px-3 py-1.5 text-sm font-mono flex-1"
              placeholder="Enter chat ID"
              value={newChatId}
              onChange={(e) => setNewChatId(e.target.value)}
            />
            <button
              className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
              disabled={!newChatId.trim() || isNaN(Number(newChatId))}
              onClick={addChatId}
            >
              Add
            </button>
          </div>

          <p className="text-xs text-gray-400 mt-2">
            Leave empty to allow all chats. Add specific IDs to restrict.
          </p>
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
