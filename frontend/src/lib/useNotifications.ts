"use client";

import { useEffect, useState, useCallback, useRef } from "react";

interface Notification {
  id: string;
  type: string;
  data: {
    project_id?: string;
    project_name?: string;
    report_id?: string;
    report_title?: string;
    created_by?: string;
    changed_by?: string;
    new_status?: string;
    timestamp: string;
  };
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = window.location.host;
    const wsUrl = `${wsProtocol}//${wsHost}/api/v1/ws?token=${token}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnected(true);
        console.log("WebSocket connected");
      };

      ws.onmessage = (event) => {
        try {
          const notification = JSON.parse(event.data);
          if (notification.type) {
            const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            setNotifications((prev) => [{ ...notification, id }, ...prev.slice(0, 9)]);
          }
        } catch (e) {
          console.error("Failed to parse notification:", e);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        console.log("WebSocket disconnected");
        // Reconnect after 5 seconds
        setTimeout(connect, 5000);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      wsRef.current = ws;

      // Keep connection alive with ping
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send("ping");
        }
      }, 30000);

      return () => {
        clearInterval(pingInterval);
        ws.close();
      };
    } catch (e) {
      console.error("Failed to connect WebSocket:", e);
    }
  }, []);

  useEffect(() => {
    const cleanup = connect();
    return () => {
      cleanup?.();
      wsRef.current?.close();
    };
  }, [connect]);

  const dismissNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  return {
    notifications,
    connected,
    dismissNotification,
    clearAll,
  };
}
