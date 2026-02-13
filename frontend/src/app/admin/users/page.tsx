"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Users, Shield, UserCheck, UserX, Edit2, Save, X } from "lucide-react";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

const roleColors: Record<string, string> = {
  admin: "bg-purple-100 text-purple-700",
  manager: "bg-blue-100 text-blue-700",
  inspector: "bg-green-100 text-green-700",
};

const roleDescriptions: Record<string, string> = {
  admin: "IT / system control - full access",
  manager: "Review & approve reports",
  inspector: "Upload photos & write narratives",
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<User>>({});
  const [showCreate, setShowCreate] = useState(false);
  const [newUser, setNewUser] = useState({
    email: "",
    password: "",
    full_name: "",
    role: "inspector",
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await fetch("/api/v1/auth/users", {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (err) {
      console.error("Failed to load users:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (user: User) => {
    setEditingId(user.id);
    setEditForm({ full_name: user.full_name, role: user.role, is_active: user.is_active });
  };

  const handleSave = async (userId: string) => {
    try {
      const response = await fetch(`/api/v1/auth/users/${userId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify(editForm),
      });
      if (response.ok) {
        setEditingId(null);
        loadUsers();
      }
    } catch (err) {
      console.error("Failed to update user:", err);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch("/api/v1/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify(newUser),
      });
      if (response.ok) {
        setShowCreate(false);
        setNewUser({ email: "", password: "", full_name: "", role: "inspector" });
        loadUsers();
      }
    } catch (err) {
      console.error("Failed to create user:", err);
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
          <p className="text-sm text-gray-500 mt-1">Admin only - manage users and roles</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Add User
        </button>
      </div>

      {/* Role Legend */}
      <div className="bg-white rounded-xl border p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Role Permissions</h3>
        <div className="grid gap-3 md:grid-cols-3">
          {Object.entries(roleDescriptions).map(([role, desc]) => (
            <div key={role} className="flex items-center gap-2">
              <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${roleColors[role]}`}>
                {role}
              </span>
              <span className="text-sm text-gray-600">{desc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Create User Form */}
      {showCreate && (
        <div className="bg-white rounded-xl border p-6">
          <h2 className="text-lg font-semibold mb-4">Create New User</h2>
          <form onSubmit={handleCreate} className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Full Name</label>
              <input
                type="text"
                required
                value={newUser.full_name}
                onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                required
                value={newUser.email}
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <input
                type="password"
                required
                value={newUser.password}
                onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Role</label>
              <select
                value={newUser.role}
                onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border rounded-lg"
              >
                <option value="inspector">Inspector</option>
                <option value="manager">Manager</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div className="md:col-span-2 flex gap-3">
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">
                Create User
              </button>
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Users Table */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {users.map((user) => (
              <tr key={user.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  {editingId === user.id ? (
                    <input
                      type="text"
                      value={editForm.full_name || ""}
                      onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                      className="px-2 py-1 border rounded"
                    />
                  ) : (
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4 text-gray-400" />
                      <span className="font-medium">{user.full_name}</span>
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.email}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {editingId === user.id ? (
                    <select
                      value={editForm.role || ""}
                      onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                      className="px-2 py-1 border rounded"
                    >
                      <option value="inspector">Inspector</option>
                      <option value="manager">Manager</option>
                      <option value="admin">Admin</option>
                    </select>
                  ) : (
                    <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${roleColors[user.role]}`}>
                      {user.role}
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {editingId === user.id ? (
                    <select
                      value={editForm.is_active ? "active" : "inactive"}
                      onChange={(e) => setEditForm({ ...editForm, is_active: e.target.value === "active" })}
                      className="px-2 py-1 border rounded"
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  ) : user.is_active ? (
                    <span className="inline-flex items-center gap-1 text-green-600 text-sm">
                      <UserCheck className="w-4 h-4" /> Active
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-red-600 text-sm">
                      <UserX className="w-4 h-4" /> Inactive
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {editingId === user.id ? (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleSave(user.id)}
                        className="p-1 text-green-600 hover:bg-green-50 rounded"
                      >
                        <Save className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        className="p-1 text-gray-600 hover:bg-gray-50 rounded"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleEdit(user)}
                      className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
