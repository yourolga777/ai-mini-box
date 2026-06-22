const BASE = import.meta.env.VITE_API_BASE ?? "";

async function request<T>(url: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...opts?.headers },
  });
  if (res.status === 204) return undefined as T;
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json();
}

export const api = {
  list: <T>(path: string) => request<T[]>(`/api/${path}`),
  get: <T>(path: string, id: number) => request<T>(`/api/${path}/${id}`),
  create: <T>(path: string, data: unknown) =>
    request<T>(`/api/${path}/`, { method: "POST", body: JSON.stringify(data) }),
  update: <T>(path: string, id: number, data: unknown) =>
    request<T>(`/api/${path}/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (path: string, id: number) =>
    request<void>(`/api/${path}/${id}`, { method: "DELETE" }),
};
