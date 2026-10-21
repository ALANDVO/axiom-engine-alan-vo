import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Chat } from "./Chat";
import { api } from "../api/client";

// Mock the API client
vi.mock("../api/client", () => ({
  api: {
    chat: {
      completions: vi.fn(),
    },
  },
}));

describe("Chat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders chat interface", () => {
    render(<Chat />);
    expect(screen.getByText("Axiom Engine Chat")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Type your message...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send" })).toBeInTheDocument();
  });

  it("sends message and displays response", async () => {
    const mockResponse = {
      id: "test-123",
      object: "chat.completion",
      created: Date.now(),
      model: "openai/gpt-4o-mini",
      choices: [
        {
          index: 0,
          message: { role: "assistant", content: "Hello! How can I help?" },
          finish_reason: "stop",
        },
      ],
      usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
    };

    vi.mocked(api.chat.completions).mockResolvedValue(mockResponse);

    render(<Chat />);

    const textarea = screen.getByPlaceholderText("Type your message...");
    fireEvent.change(textarea, { target: { value: "Hello" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(screen.getByText("Hello! How can I help?")).toBeInTheDocument();
    });

    expect(api.chat.completions).toHaveBeenCalledWith(
      expect.objectContaining({
        model: "openai/gpt-4o-mini",
        messages: expect.arrayContaining([
          expect.objectContaining({ role: "user", content: "Hello" }),
        ]),
      })
    );
  });

  it("displays error on API failure", async () => {
    vi.mocked(api.chat.completions).mockRejectedValue(new Error("API Error"));

    render(<Chat />);

    const textarea = screen.getByPlaceholderText("Type your message...");
    fireEvent.change(textarea, { target: { value: "Hello" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(screen.getByText("Error: API Error")).toBeInTheDocument();
    });
  });

  it("disables send button while loading", async () => {
    let resolveFn: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolveFn = resolve;
    });
    vi.mocked(api.chat.completions).mockReturnValue(promise);

    render(<Chat />);

    const textarea = screen.getByPlaceholderText("Type your message...");
    fireEvent.change(textarea, { target: { value: "Hello" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(screen.getByRole("button", { name: "Sending..." })).toBeDisabled();

    resolveFn!({
      id: "test",
      object: "chat.completion",
      created: Date.now(),
      model: "openai/gpt-4o-mini",
      choices: [{ index: 0, message: { role: "assistant", content: "OK" }, finish_reason: "stop" }],
      usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
    });
    await promise;
  });
});