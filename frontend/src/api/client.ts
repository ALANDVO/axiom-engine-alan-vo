const API_BASE = "/v1";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  chat: {
    completions: (data: any) => request<any>("/chat/completions", { method: "POST", body: JSON.stringify(data) }),
  },
  models: {
    list: (params?: { platform?: string; capability?: string; enabled_only?: boolean; page?: number; page_size?: number }) => {
      const search = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([k, v]) => {
          if (v !== undefined) search.set(k, String(v));
        });
      }
      return request<any>(`/models?${search.toString()}`);
    },
    get: (platform: string, modelId: string) => request<any>(`/models/${modelId}?platform=${platform}`),
  },
  keys: {
    list: (platform?: string) => request<any>(`/keys${platform ? `?platform=${platform}` : ""}`),
    create: (data: any) => request<any>("/keys", { method: "POST", body: JSON.stringify(data) }),
    delete: (id: number) => request<any>(`/keys/${id}`, { method: "DELETE" }),
  },
  health: {
    check: () => request<any>("/health/"),
    db: () => request<any>("/health/db"),
  },
};