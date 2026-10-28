/**
 * Typed API client for the AI banking assistant.
 * Mirrors the backend /api/v1/ai/* endpoints defined in app/api/ai.py.
 *
 * Uses the same auth token and base URL as the customer API.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";
const TOKEN_KEY = "customer_token";

function getToken(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = "Bearer " + token;
  const res = await fetch(BASE + path, { ...init, headers });
  if (!res.ok) {
    if (res.status === 204) return undefined as T;
    const body = await res.text().catch(() => "");
    let detail = body;
    try {
      const p = JSON.parse(body);
      detail = p?.detail ?? body;
    } catch {
      /* raw text */
    }
    throw new Error(detail || "API error " + res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ─── Types ─────────────────────────────────────────────────────────────────

/** Request body for POST /ai/chat */
export interface AIChatRequest {
  message: string;
  conversation_id?: string;
}

/** Response from POST /ai/chat */
export interface AIChatResponse {
  conversation_id: string;
  message_id?: string;
  response?: string;
  message?: string;
  tool_used?: string | null;
  user_message?: string;
}

/** A conversation summary from GET /ai/conversations */
export interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

/** A single message from GET /ai/conversations/{id} */
export interface Message {
  id: string;
  role: "user" | "assistant" | "tool" | "system";
  content: string;
  tool_name: string | null;
  created_at: string;
}

// ─── API Functions ─────────────────────────────────────────────────────────

/**
 * Send a chat message to the AI assistant.
 * POST /api/v1/ai/chat
 */
export async function sendChatMessage(
  data: AIChatRequest,
): Promise<AIChatResponse> {
  return apiFetch("/ai/chat", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * List the authenticated user's AI conversations.
 * GET /api/v1/ai/conversations
 */
export async function fetchConversations(): Promise<Conversation[]> {
  const result = await apiFetch<Conversation[] | { message: string }>(
    "/ai/conversations",
  );
  // Handle placeholder response from backend stub
  if (!Array.isArray(result)) return [];
  return result;
}

/**
 * Fetch messages for a specific conversation.
 * GET /api/v1/ai/conversations/{conversation_id}
 */
export async function fetchConversationMessages(
  conversationId: string,
): Promise<Message[]> {
  const result = await apiFetch<Message[] | { message: string }>(
    "/ai/conversations/" + conversationId,
  );
  // Handle placeholder response from backend stub
  if (!Array.isArray(result)) return [];
  return result;
}
