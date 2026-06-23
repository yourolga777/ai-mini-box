const BASE = import.meta.env.VITE_API_BASE ?? "";

async function request<T>(url: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...opts?.headers },
  });
  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  list: <T>(path: string) => request<T[]>(`/api/${path}`),
  get: <T>(path: string, id: number | string) => request<T>(`/api/${path}/${id}`),
  create: <T>(path: string, data: unknown) =>
    request<T>(`/api/${path}/`, { method: "POST", body: JSON.stringify(data) }),
  update: <T>(path: string, id: number, data: unknown) =>
    request<T>(`/api/${path}/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (path: string, id: number | string) =>
    request<void>(`/api/${path}/${id}`, { method: "DELETE" }),

  // plugin lifecycle
  startPlugin: (name: string) =>
    request<{ success: boolean; output: string; pid?: number }>(
      `/api/plugins/${name}/start`, { method: "POST" },
    ),
  stopPlugin: (name: string) =>
    request<{ success: boolean; output: string }>(
      `/api/plugins/${name}/stop`, { method: "POST" },
    ),
  pluginAction: (name: string, action: string) =>
    request<{ success: boolean; count?: number; output: string }>(
      `/api/plugins/${name}/action`, { method: "POST", body: JSON.stringify({ action }) },
    ),

  // install
  install: (pkg: string) =>
    request<{ success: boolean; output: string; reload?: boolean }>(
      `/api/plugins/install`,
      { method: "POST", body: JSON.stringify({ package: pkg }) },
    ),
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/api/plugins/install/upload`, {
      method: "POST",
      body: form,
    }).then(async (res) => {
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
      return body as { success: boolean; output: string; reload?: boolean };
    });
  },
  checkPackage: (pkg: string) =>
    request<{ installed: boolean }>(`/api/plugins/check/package?package=${encodeURIComponent(pkg)}`),
  uninstallPlugin: (name: string) =>
    request<{ success: boolean; output: string }>(`/api/plugins/${name}`, { method: "DELETE" }),

  // config
  getConfig: () => request<Record<string, unknown>>("/api/plugins/config"),
  setConfig: (key: string, value: unknown) =>
    request<{ success: boolean }>("/api/plugins/config/set", {
      method: "POST",
      body: JSON.stringify({ key, value }),
    }),
};
