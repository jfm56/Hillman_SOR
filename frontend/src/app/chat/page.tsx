"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/lib/api";
import { Send, MessageSquare, Plus, Trash2 } from "lucide-react";

interface Message {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

interface Session {
  id: string;
  title: string;
  created_at: string;
}

export default function ChatPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    if (activeSession) {
      loadMessages(activeSession);
    }
  }, [activeSession]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadSessions = async () => {
    try {
      const data = await api.getChatSessions();
      setSessions(data);
      if (data.length > 0 && !activeSession) {
        setActiveSession(data[0].id);
      }
    } catch (err) {
      console.error("Failed to load sessions:", err);
    }
  };

  const loadMessages = async (sessionId: string) => {
    try {
      const data = await api.getChatSession(sessionId);
      setMessages(data.messages || []);
    } catch (err) {
      console.error("Failed to load messages:", err);
    }
  };

  const createSession = async () => {
    try {
      const session = await api.createChatSession();
      setSessions([session, ...sessions]);
      setActiveSession(session.id);
      setMessages([]);
    } catch (err) {
      console.error("Failed to create session:", err);
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !activeSession || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      created_at: new Date().toISOString(),
    };

    setMessages([...messages, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await api.sendChatMessage(activeSession, input);
      setMessages((prev) => [...prev, response]);
    } catch (err) {
      console.error("Failed to send message:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Sessions sidebar */}
      <div className="w-64 bg-white rounded-xl border p-4 flex flex-col">
        <button
          onClick={createSession}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 mb-4"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>

        <div className="flex-1 overflow-y-auto space-y-2">
          {sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => setActiveSession(session.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                activeSession === session.id
                  ? "bg-blue-50 text-blue-700"
                  : "hover:bg-gray-50 text-gray-700"
              }`}
            >
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4" />
                <span className="truncate">{session.title || "New Chat"}</span>
              </div>
              <span className="text-xs text-gray-400">
                {new Date(session.created_at).toLocaleDateString()}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 bg-white rounded-xl border flex flex-col">
        {activeSession ? (
          <>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full text-gray-400">
                  <div className="text-center">
                    <MessageSquare className="w-12 h-12 mx-auto mb-4" />
                    <p>Start a conversation with the AI assistant</p>
                    <p className="text-sm mt-2">Ask questions about reports, get writing help, or analyze data</p>
                  </div>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[70%] px-4 py-2 rounded-lg ${
                        msg.role === "user"
                          ? "bg-blue-600 text-white"
                          : "bg-gray-100 text-gray-900"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                ))
              )}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 px-4 py-2 rounded-lg">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={sendMessage} className="p-4 border-t">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </form>
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <MessageSquare className="w-12 h-12 mx-auto mb-4" />
              <p>Select a chat or start a new one</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
