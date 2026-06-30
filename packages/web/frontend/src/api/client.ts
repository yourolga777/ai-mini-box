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
    request<T>(`/api/${path}`, { method: "POST", body: JSON.stringify(data) }),
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
    request<{ success: boolean; count?: number; output: string; detected_chat_ids?: number[] }>(
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

  // telegram
  verifyToken: (name: string) =>
    request<{ success: boolean; bot_name: string; bot_username: string }>(
      `/api/plugins/${name}/verify-token`, { method: "POST" },
    ),

  // config
  getConfig: () => request<Record<string, unknown>>("/api/plugins/config"),
  setConfig: (key: string, value: unknown) =>
    request<{ success: boolean }>("/api/plugins/config/set", {
      method: "POST",
      body: JSON.stringify({ key, value }),
    }),

  // folders (LLM plugin)
  listFolders: () => request<Folder[]>("/api/llm/folders"),
  createFolder: (data: { name: string; description?: string; color?: string }) =>
    request<Folder>("/api/llm/folders", { method: "POST", body: JSON.stringify(data) }),
  updateFolder: (id: number, data: { name?: string; description?: string; color?: string }) =>
    request<Folder>(`/api/llm/folders/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteFolder: (id: number, mode: "move" | "delete_messages" = "move") =>
    request<{ ok: boolean; mode: string; messages_affected: number }>(
      `/api/llm/folders/${id}?mode=${mode}`, { method: "DELETE" },
    ),
  getFolderMessages: (id: number) => request<number[]>(`/api/llm/folders/${id}/messages`),
  assignFolder: (folderId: number, messageId: number) =>
    request<{ ok: boolean; already_assigned: boolean }>(
      `/api/llm/folders/${folderId}/assign`, { method: "POST", body: JSON.stringify({ message_id: messageId }) },
    ),
  unassignFolder: (folderId: number, messageId: number) =>
    request<{ ok: boolean; was_assigned: boolean }>(
      `/api/llm/folders/${folderId}/unassign`, { method: "POST", body: JSON.stringify({ message_id: messageId }) },
    ),
  runAutoProcessor: () => request<{ ok: boolean; processed: number }>(
    "/api/llm/process", { method: "POST" },
  ),

  // new message-category endpoints
  assignMessageCategory: (messageId: number, categoryId: number) =>
    request<{ ok: boolean }>(
      `/api/messages/${messageId}/categories`, { method: "POST", body: JSON.stringify({ category_id: categoryId }) },
    ),
  unassignMessageCategory: (messageId: number, categoryId: number) =>
    request<{ ok: boolean }>(
      `/api/messages/${messageId}/categories/${categoryId}`, { method: "DELETE" },
    ),
  batchAssignCategories: (data: { message_ids: number[]; category_id: number }) =>
    request<{ assigned: number; errors: Array<{ message_id: number; error: string }> }>(
      "/api/llm/batch-assign", { method: "POST", body: JSON.stringify(data) },
    ),
  assignAllCategories: (limit: number = 50) =>
    request<{ checked: number; assigned: number }>(
      `/api/llm/assign-all?limit=${limit}`, { method: "POST" },
    ),

  // catalog + update
  catalogPlugins: () => request<CatalogPlugin[]>("/api/plugins/catalog"),
  updatePlugin: (name: string) =>
    request<{ success: boolean; output: string }>(`/api/plugins/${name}/update`, { method: "POST" }),

  // plugin config
  getPluginConfigSchema: (name: string) =>
    request<Record<string, any>>(`/api/plugins/${name}/config-schema`),
  getPluginConfig: (name: string) =>
    request<Record<string, any>>(`/api/plugins/${name}/config`),
  setPluginConfig: (name: string, data: Record<string, any>) =>
    request<{ success: boolean }>(`/api/plugins/${name}/config`, { method: "POST", body: JSON.stringify(data) }),

  // folders — reorder
  reorderFolders: (order: number[]) =>
    request<{ ok: boolean }>("/api/llm/folders/reorder", {
      method: "POST", body: JSON.stringify({ order }),
    }),
  getMessageCategories: (id: number) =>
    request<FolderAssign[]>("/api/messages/" + id + "/categories"),

  // orders
  getMessageOrder: (id: number) =>
    request<Order | null>(`/api/messages/${id}/order`),
  createOrder: (id: number, data: { total_kopecks?: number; notes?: string }) =>
    request<Order>(`/api/messages/${id}/create-order`, { method: "POST", body: JSON.stringify(data) }),
  getContactOrders: (contactId: number) =>
    request<Order[]>(`/api/orders?contact_id=${contactId}`),
  getOrderItems: (orderId: number) =>
    request<OrderItem[]>(`/api/orders/${orderId}/items`),
  createOrderItem: (orderId: number, data: { product_name: string; quantity: number; price_kopecks: number; product_id?: number }) =>
    request<OrderItem>(`/api/orders/${orderId}/items`, { method: "POST", body: JSON.stringify(data) }),
  updateOrderItem: (orderId: number, itemId: number, data: Partial<{ product_name: string; quantity: number; price_kopecks: number }>) =>
    request<OrderItem>(`/api/orders/${orderId}/items/${itemId}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteOrderItem: (orderId: number, itemId: number) =>
    request<void>(`/api/orders/${orderId}/items/${itemId}`, { method: "DELETE" }),
  updateOrder: (id: number, data: Partial<{ status: string; notes: string; contact_id: number | null }>) =>
    request<Order>(`/api/orders/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteOrder: (id: number) =>
    request<void>(`/api/orders/${id}`, { method: "DELETE" }),
  searchProducts: (query: string) =>
    request<Product[]>(`/api/products?search=${encodeURIComponent(query)}`),

  // email
  emailStatus: () => request<EmailStatus>("/api/email/status"),
  emailTest: (data: EmailTestRequest) =>
    request<EmailTestResponse>("/api/email/test", { method: "POST", body: JSON.stringify(data) }),
  emailSaveConfig: (data: EmailConfig) =>
    request<{ success: boolean }>("/api/plugins/email/config", { method: "POST", body: JSON.stringify(data) }),

  // analytics
  getAnalytics: <T>(path: string, params?: Record<string, string | number>) => {
    const qs = params ? "?" + new URLSearchParams(Object.fromEntries(Object.entries(params).map(([k, v]) => [k, String(v)]))).toString() : "";
    return request<T>(`/api/analytics/${path}${qs}`);
  },

  // business config
  getBusinessConfig: () => request<BusinessConfig>("/api/business/config"),
  updateBusinessConfig: (cfg: Partial<BusinessConfig>) =>
    request<BusinessConfig>("/api/business/config", { method: "PUT", body: JSON.stringify(cfg) }),
  reprocessMessage: (id: number) =>
    request<ReprocessResult>(`/api/messages/${id}/reprocess-chatbot`, { method: "POST" }),

  // templates
  listTemplates: (params?: Record<string, string | number | boolean>) => {
    const qs = params ? "?" + new URLSearchParams(Object.fromEntries(Object.entries(params).map(([k, v]) => [k, String(v)]))).toString() : "";
    return request<TemplateItem[]>(`/api/v1/templates/${qs}`);
  },
  getTemplate: (id: string) => request<TemplateItem>(`/api/v1/templates/${id}`),
  createTemplate: (data: TemplateCreateBody) =>
    request<TemplateItem>("/api/v1/templates/", { method: "POST", body: JSON.stringify(data) }),
  updateTemplate: (id: string, data: Partial<TemplateCreateBody & { is_active: boolean }>) =>
    request<TemplateItem>(`/api/v1/templates/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteTemplate: (id: string, hard?: boolean) => {
    const qs = hard ? "?hard=true" : "";
    return request<void>(`/api/v1/templates/${id}${qs}`, { method: "DELETE" });
  },
  suggestTemplates: (message: string, category?: string, limit?: number) => {
    const params = new URLSearchParams({ message });
    if (category) params.set("category", category);
    if (limit) params.set("limit", String(limit));
    return request<TemplateSuggestResult>(`/api/v1/templates/suggest?${params.toString()}`);
  },
  useTemplate: (id: string, data: { message_id?: string; operator_approved?: boolean; operator_edited?: boolean; final_text?: string; response_time_ms?: number }) =>
    request<{ ok: boolean }>(`/api/v1/templates/${id}/use`, { method: "POST", body: JSON.stringify(data) }),
  approveTemplate: (id: string) =>
    request<TemplateItem>(`/api/v1/templates/${id}/approve`, { method: "POST" }),
};

export interface FolderAssign {
  id: number;
  name: string;
  description: string;
  color: string;
  is_system: boolean;
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_id: number | null;
  product_name: string;
  quantity: number;
  price_kopecks: number;
  created_at: string;
}

export interface Product {
  id: number;
  name: string;
  description: string | null;
  price_kopecks: number;
  stock: number;
  unit: string;
  category: string | null;
  created_at: string;
}

export interface Order {
  id: number;
  contact_id: number | null;
  source_message_id: number | null;
  total_kopecks: number;
  notes: string;
  status: string;
  created_at: string;
}

export interface CatalogPlugin {
  name: string;
  description: string;
  version: string | null;
  installed: boolean;
  installed_version: string | null;
  has_update: boolean;
}

export interface Folder {
  id: number;
  name: string;
  description: string;
  color: string;
  is_system: boolean;
  message_count: number;
}

export interface EmailStatus {
  configured: boolean;
  connected: boolean;
  last_poll_at: string | null;
  last_error: string | null;
  messages_fetched_today: number;
}

export interface EmailTestRequest {
  imap_host: string;
  imap_port: number;
  imap_ssl: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_ssl: boolean;
  email_address: string;
  email_password: string;
}

export interface EmailTestResponse {
  success: boolean;
  imap: boolean;
  smtp: boolean;
  message: string | null;
}

export interface EmailConfig {
  imap_host: string;
  imap_port: number;
  imap_ssl: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_ssl: boolean;
  email_address: string;
  email_password: string;
  folder: string;
  max_per_cycle: number;
  mark_as_seen: boolean;
  poll_interval_seconds: number;
}

export interface BusinessConfig {
  company_name: string;
  work_hours: string;
  delivery_info: string;
  return_policy: string;
  payment_methods: string;
  contacts: string;
  faq: Array<{ question: string; answer: string }>;
}

export interface ReprocessResult {
  success: boolean;
  category: string | null;
  subcategory: string | null;
  reply_to_user: string | null;
  need_human: boolean;
  auto_replied: boolean;
}

export interface TemplateItem {
  id: string;
  scope: string;
  category: string;
  name: string;
  slug: string;
  text: string;
  variables: string[];
  defaults: Record<string, string>;
  triggers: string[];
  confidence_min: number;
  usage_count: number;
  success_count: number;
  success_rate: number;
  version: number;
  is_active: boolean;
  is_archived: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface TemplateCreateBody {
  category: string;
  name: string;
  text: string;
  variables?: string[];
  defaults?: Record<string, string>;
  triggers?: string[];
  confidence_min?: number;
}

export interface TemplateSuggestResult {
  templates: TemplateItem[];
  entities: Record<string, string>;
  category: string | null;
  confidence: number;
}
