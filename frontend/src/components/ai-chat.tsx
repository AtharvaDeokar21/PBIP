"use client";
/**
 * AI Banking Assistant – a fully integrated chat component for the customer portal.
 *
 * Calls POST /api/v1/ai/chat with the customer's JWT.
 * Falls back gracefully when the backend is a stub (returns user_message echo).
 *
 * Features:
 * - Real API integration with the backend AI endpoint
 * - Conversation persistence via conversation_id
 * - Typing indicator & loading states
 * - Quick-action suggestion chips
 * - Auto-scroll on new messages
 * - Graceful error handling (no raw API errors shown)
 * - Keyboard shortcut (Enter to send)
 * - Tool usage badges when the AI uses a banking tool
 * - New conversation support
 */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Sparkles,
  Send,
  MessageCircle,
  Loader2,
  ArrowRight,
  AlertCircle,
  X,
  Wallet,
  TrendingUp,
  Landmark,
  ReceiptText,
  ShieldCheck,
  RefreshCcw,
  Bot,
} from "lucide-react";
import {
  sendChatMessage,
  type AIChatResponse,
} from "@/lib/customer/ai-api";

// ─── Types ─────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system" | "error";
  content: string;
  toolUsed?: string | null;
  timestamp: Date;
}

// ─── Quick Action Suggestions ──────────────────────────────────────────────

const QUICK_ACTIONS = [
  {
    label: "How much did I spend this month?",
    icon: ReceiptText,
    category: "spending",
  },
  {
    label: "Show my account balances",
    icon: Wallet,
    category: "accounts",
  },
  {
    label: "What loans am I eligible for?",
    icon: Landmark,
    category: "loans",
  },
  {
    label: "Show my investment portfolio",
    icon: TrendingUp,
    category: "investments",
  },
];

const FOLLOW_UP_SUGGESTIONS = [
  "Show my recent transactions",
  "What are my recommendations?",
  "Help me understand my spending",
  "Tell me about my accounts",
];

// ─── Helper: unique id ────────────────────────────────────────────────────

let _msgId = 0;
function nextId() {
  return "msg-" + Date.now() + "-" + ++_msgId;
}

// ─── Tool badge labels ────────────────────────────────────────────────────

const TOOL_LABELS: Record<string, string> = {
  get_customer_profile: "Profile",
  get_accounts: "Accounts",
  get_account_balance: "Balance",
  get_recent_transactions: "Transactions",
  search_transactions: "Search",
  get_spending_summary: "Spending",
  get_loan_products: "Loans",
  check_loan_eligibility: "Eligibility",
  get_loan_applications: "Applications",
  get_investment_products: "Investments",
  get_customer_investments: "Holdings",
  get_recommendations: "Recommendations",
  get_notifications: "Notifications",
};

// ─── Component ────────────────────────────────────────────────────────────

export default function AIChat({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 200);
    }
  }, [isOpen]);

  // ─── Send message ──────────────────────────────────────────────────────

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || loading) return;

      setError(null);
      setInput("");

      // Add user message
      const userMsg: ChatMessage = {
        id: nextId(),
        role: "user",
        content: trimmed,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setLoading(true);

      try {
        const response: AIChatResponse = await sendChatMessage({
          message: trimmed,
          conversation_id: conversationId,
        });

        // Track conversation
        if (response.conversation_id) {
          setConversationId(response.conversation_id);
        }

        // Extract the response text – the backend may use "response" or "message"
        const responseText =
          response.response ||
          response.message ||
          "I received your message. The AI assistant is being set up – please try again shortly.";

        const assistantMsg: ChatMessage = {
          id: nextId(),
          role: "assistant",
          content: responseText,
          toolUsed: response.tool_used,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Something went wrong";

        // Don't show raw API errors – present a friendly message
        const friendlyMessage = errorMessage.includes("401")
          ? "Your session has expired. Please log in again."
          : errorMessage.includes("403")
            ? "You don't have permission to use the AI assistant."
            : errorMessage.includes("404")
              ? "The AI assistant service is not available yet. Please check back later."
              : errorMessage.includes("500") ||
                  errorMessage.includes("503") ||
                  errorMessage.includes("fetch")
                ? "I'm unable to reach the banking assistant right now. Please try again in a moment."
                : errorMessage;

        const errorMsg: ChatMessage = {
          id: nextId(),
          role: "error",
          content: friendlyMessage,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMsg]);
        setError(friendlyMessage);
      } finally {
        setLoading(false);
      }
    },
    [loading, conversationId],
  );

  // ─── New conversation ──────────────────────────────────────────────────

  const startNewConversation = useCallback(() => {
    setMessages([]);
    setConversationId(undefined);
    setError(null);
    setInput("");
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  // ─── Handle form submit ────────────────────────────────────────────────

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  if (!isOpen) return null;

  return (
    <section
      className="ai-chat-panel"
      id="ai-assistant-panel"
      aria-label="AI Banking Assistant"
      role="complementary"
    >
      {/* ── Header ────────────────────────────────────────────────────── */}
      <header className="ai-chat-header">
        <div className="ai-chat-header-left">
          <span className="ai-chat-avatar">
            <Sparkles size={18} />
          </span>
          <div>
            <strong>Credora AI</strong>
            <small>Your personal banking companion</small>
          </div>
        </div>
        <div className="ai-chat-header-actions">
          <button
            className="ai-chat-icon-btn"
            onClick={startNewConversation}
            aria-label="New conversation"
            title="New conversation"
          >
            <MessageCircle size={16} />
          </button>
          <button
            className="ai-chat-icon-btn"
            onClick={onClose}
            aria-label="Close assistant"
            title="Close"
          >
            <X size={16} />
          </button>
        </div>
      </header>

      {/* ── Messages ──────────────────────────────────────────────────── */}
      <div className="ai-chat-messages" aria-live="polite">
        {messages.length === 0 ? (
          <div className="ai-chat-welcome">
            <div className="ai-chat-welcome-icon">
              <Bot size={32} />
            </div>
            <h3>
              How can I help you
              <br />
              today?
            </h3>
            <p>
              Ask me anything about your accounts, spending, loans,
              investments, or recommendations.
            </p>
            <div className="ai-chat-suggestions">
              {QUICK_ACTIONS.map((action) => (
                <button
                  key={action.label}
                  className="ai-suggestion-chip"
                  onClick={() => sendMessage(action.label)}
                  disabled={loading}
                >
                  <action.icon size={14} />
                  <span>{action.label}</span>
                  <ArrowRight size={12} className="ai-chip-arrow" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`ai-chat-bubble ${msg.role}`}
              >
                {msg.role === "assistant" && (
                  <span className="ai-bubble-avatar">
                    <Sparkles size={12} />
                  </span>
                )}
                {msg.role === "error" && (
                  <span className="ai-bubble-avatar error">
                    <AlertCircle size={12} />
                  </span>
                )}
                <div className="ai-bubble-content">
                  <p>{msg.content}</p>
                  {msg.toolUsed && TOOL_LABELS[msg.toolUsed] && (
                    <span className="ai-tool-badge">
                      <ShieldCheck size={10} />
                      {TOOL_LABELS[msg.toolUsed]}
                    </span>
                  )}
                  <time className="ai-bubble-time">
                    {msg.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </time>
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {loading && (
              <div className="ai-chat-bubble assistant typing">
                <span className="ai-bubble-avatar">
                  <Sparkles size={12} />
                </span>
                <div className="ai-typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}

            {/* Follow-up suggestions after a response */}
            {messages.length > 0 &&
              !loading &&
              messages[messages.length - 1].role === "assistant" && (
                <div className="ai-followup-suggestions">
                  {FOLLOW_UP_SUGGESTIONS.slice(0, 2).map((suggestion) => (
                    <button
                      key={suggestion}
                      className="ai-followup-chip"
                      onClick={() => sendMessage(suggestion)}
                      disabled={loading}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* ── Error banner ──────────────────────────────────────────────── */}
      {error && (
        <div className="ai-chat-error-banner">
          <AlertCircle size={14} />
          <span>Connection issue</span>
          <button
            className="ai-chat-icon-btn"
            onClick={() => setError(null)}
            aria-label="Dismiss error"
          >
            <X size={12} />
          </button>
        </div>
      )}

      {/* ── Input ─────────────────────────────────────────────────────── */}
      <form className="ai-chat-input-form" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          aria-label="Message to AI assistant"
          placeholder="Ask about your money…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          maxLength={500}
          disabled={loading}
          autoComplete="off"
        />
        <button
          className="ai-send-btn"
          aria-label="Send message"
          disabled={!input.trim() || loading}
          type="submit"
        >
          {loading ? <Loader2 size={16} className="ai-spin" /> : <Send size={16} />}
        </button>
      </form>

      {/* ── Footer ────────────────────────────────────────────────────── */}
      <footer className="ai-chat-footer">
        <ShieldCheck size={11} />
        <span>Secured · Your data stays private</span>
      </footer>
    </section>
  );
}

// ─── Toggle button (exported separately for the shell) ────────────────────

export function AIChatToggle({
  isOpen,
  onClick,
}: {
  isOpen: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className="ai-assistant-toggle"
      onClick={onClick}
      aria-expanded={isOpen}
      aria-controls="ai-assistant-panel"
    >
      {isOpen ? <X size={18} /> : <Sparkles size={18} />}
      <span>{isOpen ? "Close" : "Ask Credora AI"}</span>
    </button>
  );
}
