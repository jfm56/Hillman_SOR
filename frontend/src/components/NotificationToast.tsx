"use client";

import { X, FolderPlus, FileText, CheckCircle } from "lucide-react";

interface NotificationToastProps {
  notifications: Array<{
    id: string;
    type: string;
    data: {
      project_name?: string;
      report_title?: string;
      created_by?: string;
      changed_by?: string;
      new_status?: string;
      timestamp: string;
    };
  }>;
  onDismiss: (id: string) => void;
}

export function NotificationToast({ notifications, onDismiss }: NotificationToastProps) {
  if (notifications.length === 0) return null;

  const getIcon = (type: string) => {
    switch (type) {
      case "project_created":
        return <FolderPlus className="w-5 h-5 text-blue-500" />;
      case "report_created":
        return <FileText className="w-5 h-5 text-green-500" />;
      case "report_status_changed":
        return <CheckCircle className="w-5 h-5 text-purple-500" />;
      default:
        return null;
    }
  };

  const getMessage = (notification: NotificationToastProps["notifications"][0]) => {
    const { type, data } = notification;
    switch (type) {
      case "project_created":
        return `${data.created_by} created project "${data.project_name}"`;
      case "report_created":
        return `${data.created_by} created report "${data.report_title}"`;
      case "report_status_changed":
        return `${data.changed_by} changed report status to ${data.new_status}`;
      default:
        return "New activity";
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 max-w-sm">
      {notifications.slice(0, 3).map((notification) => (
        <div
          key={notification.id}
          className="bg-white rounded-lg shadow-lg border p-4 flex items-start gap-3 animate-slide-in"
        >
          {getIcon(notification.type)}
          <div className="flex-1 min-w-0">
            <p className="text-sm text-gray-900">{getMessage(notification)}</p>
            <p className="text-xs text-gray-400 mt-1">
              {new Date(notification.data.timestamp).toLocaleTimeString()}
            </p>
          </div>
          <button
            onClick={() => onDismiss(notification.id)}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
