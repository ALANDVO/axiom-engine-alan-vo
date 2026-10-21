import { useState } from "react";
import { api } from "../api/client";
import { ChatMessage, ChatCompletionRequest } from "../types/api";

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [model, setModel] = useState("openai/gpt-4o-mini");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const request: ChatCompletionRequest = {
        model,
        messages: [...messages, userMessage],
      };
      const response = await api.chat.completions(request);
      const assistantMessage: ChatMessage = response.choices[0].message;
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: "800px", marginTop: "2rem" }}>
      <h1 style={{ marginBottom: "1.5rem" }}>Axiom Engine Chat</h1>

      <div className="card" style={{ marginBottom: "1rem", minHeight: "300px", maxHeight: "500px", overflow: "auto" }}>
        {messages.length === 0 && (
          <p style={{ color: "#6b7280", textAlign: "center", marginTop: "2rem" }}>
            Start a conversation...
          </p>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} style={{ marginBottom: "1rem", padding: "0.75rem", background: msg.role === "user" ? "#eff6ff" : "#f3f4f6", borderRadius: "8px" }}>
            <div style={{ fontWeight: 600, marginBottom: "0.25rem", textTransform: "capitalize" }}>
              {msg.role}
            </div>
            <div>{msg.content || "(tool call)"}</div>
          </div>
        ))}
      </div>

      {error && (
        <div className="card badge badge-danger" style={{ marginBottom: "1rem" }}>
          Error: {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="card">
        <div className="form-group" style={{ marginBottom: "0.5rem" }}>
          <label className="form-label" htmlFor="model">Model</label>
          <select id="model" className="form-input" value={model} onChange={(e) => setModel(e.target.value)}>
            <option value="openai/gpt-4o-mini">GPT-4o Mini</option>
            <option value="openai/gpt-4o">GPT-4o</option>
            <option value="anthropic/claude-3-haiku">Claude 3 Haiku</option>
          </select>
        </div>
        <div className="form-group" style={{ marginBottom: "0.5rem" }}>
          <textarea
            className="form-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            rows={3}
            disabled={loading}
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading || !input.trim()}>
          {loading ? "Sending..." : "Send"}
        </button>
      </form>

      <footer style={{ marginTop: "2rem", textAlign: "center", color: "#6b7280", fontSize: "0.875rem" }}>
        Axiom Engine — Alan Vo | AI & Machine Learning
      </footer>
    </div>
  );
}