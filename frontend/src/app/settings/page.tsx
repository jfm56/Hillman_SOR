"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { User, Lock, Bell, Database, Shield } from "lucide-react";

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export default function SettingsPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [passwords, setPasswords] = useState({
    current: "",
    new: "",
    confirm: "",
  });
  const [message, setMessage] = useState({ type: "", text: "" });

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const data = await api.getMe();
      setUser(data);
    } catch (err) {
      console.error("Failed to load user:", err);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage({ type: "", text: "" });

    if (passwords.new !== passwords.confirm) {
      setMessage({ type: "error", text: "New passwords do not match" });
      return;
    }

    try {
      await fetch("/api/v1/auth/change-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          current_password: passwords.current,
          new_password: passwords.new,
        }),
      });
      setMessage({ type: "success", text: "Password changed successfully" });
      setPasswords({ current: "", new: "", confirm: "" });
    } catch (err) {
      setMessage({ type: "error", text: "Failed to change password" });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      {/* Profile Section */}
      <div className="bg-white rounded-xl border p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-blue-100 rounded-lg">
            <User className="w-5 h-5 text-blue-600" />
          </div>
          <h2 className="text-lg font-semibold">Profile</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-500">Full Name</label>
            <p className="mt-1 text-gray-900">{user?.full_name}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500">Email</label>
            <p className="mt-1 text-gray-900">{user?.email}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500">Role</label>
            <p className="mt-1">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 capitalize">
                {user?.role}
              </span>
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500">Status</label>
            <p className="mt-1">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                user?.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
              }`}>
                {user?.is_active ? "Active" : "Inactive"}
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* Security Section */}
      <div className="bg-white rounded-xl border p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-amber-100 rounded-lg">
            <Lock className="w-5 h-5 text-amber-600" />
          </div>
          <h2 className="text-lg font-semibold">Change Password</h2>
        </div>

        {message.text && (
          <div className={`mb-4 p-3 rounded-lg text-sm ${
            message.type === "error" ? "bg-red-50 text-red-600" : "bg-green-50 text-green-600"
          }`}>
            {message.text}
          </div>
        )}

        <form onSubmit={handlePasswordChange} className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium text-gray-700">Current Password</label>
            <input
              type="password"
              value={passwords.current}
              onChange={(e) => setPasswords({ ...passwords, current: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">New Password</label>
            <input
              type="password"
              value={passwords.new}
              onChange={(e) => setPasswords({ ...passwords, new: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
            <input
              type="password"
              value={passwords.confirm}
              onChange={(e) => setPasswords({ ...passwords, confirm: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Update Password
          </button>
        </form>
      </div>

      {/* System Info */}
      <div className="bg-white rounded-xl border p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-gray-100 rounded-lg">
            <Database className="w-5 h-5 text-gray-600" />
          </div>
          <h2 className="text-lg font-semibold">System Information</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2 text-sm">
          <div>
            <label className="block font-medium text-gray-500">Version</label>
            <p className="mt-1 text-gray-900">1.0.0</p>
          </div>
          <div>
            <label className="block font-medium text-gray-500">API Endpoint</label>
            <p className="mt-1 text-gray-900">{process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
