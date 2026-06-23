import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

type Tab = "pypi" | "upload";
type Status = "idle" | "installing" | "success" | "error";

export default function InstallModal({ onClose }: { onClose: () => void }) {
  const [tab, setTab] = useState<Tab>("pypi");
  const [pkg, setPkg] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [output, setOutput] = useState("");
  const [error, setError] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const qc = useQueryClient();

  const installPypi = async () => {
    setStatus("installing");
    setError("");
    setOutput("");
    try {
      const r = await api.install(pkg);
      setOutput(r.output);
      setStatus(r.success ? "success" : "error");
      if (r.success) {
        qc.invalidateQueries({ queryKey: ["plugins"] });
        setTimeout(() => onClose(), 3000);
      }
    } catch (e: any) {
      setError(e.message);
      setStatus("error");
    }
  };

  const installUpload = async () => {
    if (!file) return;
    setStatus("installing");
    setError("");
    setOutput("");
    try {
      const r = await api.upload(file);
      setOutput(r.output);
      setStatus(r.success ? "success" : "error");
      if (r.success) {
        qc.invalidateQueries({ queryKey: ["plugins"] });
        setTimeout(() => onClose(), 3000);
      }
    } catch (e: any) {
      setError(e.message);
      setStatus("error");
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded shadow-xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold">Install Plugin</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>

        <div className="flex gap-2 mb-4 border-b pb-2">
          <button
            className={`px-3 py-1 rounded-t text-sm font-medium ${tab === "pypi" ? "bg-blue-600 text-white" : "text-gray-500 hover:text-gray-700"}`}
            onClick={() => setTab("pypi")}
          >
            From PyPI
          </button>
          <button
            className={`px-3 py-1 rounded-t text-sm font-medium ${tab === "upload" ? "bg-blue-600 text-white" : "text-gray-500 hover:text-gray-700"}`}
            onClick={() => setTab("upload")}
          >
            Upload .whl
          </button>
        </div>

        {tab === "pypi" && (
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">Package name</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm"
              placeholder="ai-mini-box-telegram"
              value={pkg}
              onChange={(e) => setPkg(e.target.value)}
              disabled={status === "installing"}
            />
            <button
              className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
              disabled={!pkg.trim() || status === "installing"}
              onClick={installPypi}
            >
              {status === "installing" ? "Installing..." : "Install"}
            </button>
          </div>
        )}

        {tab === "upload" && (
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">Wheel file (.whl)</label>
            <input
              type="file"
              accept=".whl"
              className="w-full text-sm"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              disabled={status === "installing"}
            />
            <button
              className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
              disabled={!file || status === "installing"}
              onClick={installUpload}
            >
              {status === "installing" ? "Uploading..." : "Upload & Install"}
            </button>
          </div>
        )}

        {status === "installing" && (
          <div className="mt-4 flex items-center gap-2 text-sm text-gray-600">
            <span className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            Installing...
          </div>
        )}

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded p-3 max-h-40 overflow-auto">
            {error}
          </div>
        )}

        {output && (
          <div className="mt-4">
            <pre className="bg-gray-900 text-green-300 text-xs p-3 rounded max-h-40 overflow-auto">{output}</pre>
          </div>
        )}

        {status === "success" && (
          <div className="mt-3 text-sm text-green-600 font-medium">
            Installed successfully! Reloading server...
          </div>
        )}
      </div>
    </div>
  );
}
