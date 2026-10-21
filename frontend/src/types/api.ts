export interface ChatMessage {
  role: "system" | "user" | "assistant" | "tool";
  content?: string;
  tool_calls?: Array<{
    id: string;
    type: "function";
    function: { name: string; arguments: string };
  }>;
  tool_call_id?: string;
}

export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
  tools?: Array<{
    type: "function";
    function: { name: string; description?: string; parameters: object };
  }>;
  tool_choice?: "auto" | "none" | "required";
}

export interface ChatCompletionChoice {
  index: number;
  message: ChatMessage;
  finish_reason: string;
}

export interface ChatCompletionUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: ChatCompletionChoice[];
  usage: ChatCompletionUsage;
}

export interface Model {
  id: number;
  platform: string;
  model_id: string;
  display_name?: string;
  context_window?: number;
  max_output_tokens?: number;
  supports_tools: boolean;
  supports_vision: boolean;
  input_cost_per_million?: number;
  output_cost_per_million?: number;
  is_enabled: boolean;
  source: string;
  capability_label: string;
  capability_updated_at?: string;
}

export interface ModelListResponse {
  models: Model[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiKey {
  id: number;
  platform: string;
  key_name?: string;
  is_enabled: boolean;
  quota_limit?: number;
  quota_used: number;
  quota_pool: string;
  concurrency_limit?: number;
  created_at: string;
}

export interface ApiKeyCreate {
  platform: string;
  key_hash: string;
  key_name?: string;
  quota_limit?: number;
  quota_pool?: string;
  concurrency_limit?: number;
}