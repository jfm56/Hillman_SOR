"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { 
  FolderOpen, 
  FileText, 
  Users, 
  Activity,
  Clock,
  TrendingUp
} from "lucide-react";

interface DashboardStats {
  total_projects: number;
  active_projects: number;
  total_reports: number;
  pending_reports: number;
  total_users: number;
  recent_activity: Array<{
    id: string;
    action: string;
    object_type: string;
    object_name?: string;
    user_name?: string;
    created_at: string;
  }>;
}

interface RecentProject {
  id: string;
  name: string;
  client_name: string;
  status: string;
  created_by_name?: string;
  created_at: string;
  report_count: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentProjects, setRecentProjects] = useState<RecentProject[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const [statsData, projectsData] = await Promise.all([
        api.getDashboardStats(),
        api.getRecentProjects(7),
      ]);
      setStats(statsData);
      setRecentProjects(projectsData);
    } catch (err) {
      console.error("Failed to load dashboard:", err);
    } finally {
      setLoading(false);
    }
  };

  const formatAction = (action: string, objectType: string) => {
    return `${action} ${objectType}`;
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
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
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <FolderOpen className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats?.total_projects || 0}</p>
              <p className="text-sm text-gray-500">Total Projects</p>
            </div>
          </div>
          <p className="text-xs text-green-600 mt-2">
            {stats?.active_projects || 0} active
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <FileText className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats?.total_reports || 0}</p>
              <p className="text-sm text-gray-500">Total Reports</p>
            </div>
          </div>
          <p className="text-xs text-yellow-600 mt-2">
            {stats?.pending_reports || 0} pending review
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Users className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats?.total_users || 0}</p>
              <p className="text-sm text-gray-500">Active Users</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-orange-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{recentProjects.length}</p>
              <p className="text-sm text-gray-500">Projects This Week</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Projects */}
        <div className="bg-white rounded-xl border">
          <div className="p-4 border-b">
            <h2 className="font-semibold text-gray-900">Recent Projects</h2>
          </div>
          <div className="divide-y">
            {recentProjects.length === 0 ? (
              <p className="p-4 text-gray-500 text-sm">No recent projects</p>
            ) : (
              recentProjects.slice(0, 5).map((project) => (
                <div
                  key={project.id}
                  onClick={() => router.push(`/projects/${project.id}`)}
                  className="p-4 hover:bg-gray-50 cursor-pointer"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{project.name}</p>
                      <p className="text-sm text-gray-500">{project.client_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">{project.report_count} reports</p>
                      {project.created_by_name && (
                        <p className="text-xs text-gray-400">by {project.created_by_name}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl border">
          <div className="p-4 border-b">
            <h2 className="font-semibold text-gray-900">Recent Activity</h2>
          </div>
          <div className="divide-y max-h-80 overflow-y-auto">
            {!stats?.recent_activity?.length ? (
              <p className="p-4 text-gray-500 text-sm">No recent activity</p>
            ) : (
              stats.recent_activity.slice(0, 10).map((activity) => (
                <div key={activity.id} className="p-4 flex items-start gap-3">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    <Activity className="w-4 h-4 text-gray-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900">
                      <span className="font-medium">{activity.user_name || "Someone"}</span>
                      {" "}
                      {formatAction(activity.action, activity.object_type)}
                      {activity.object_name && (
                        <span className="font-medium"> "{activity.object_name}"</span>
                      )}
                    </p>
                    <p className="text-xs text-gray-400 flex items-center gap-1 mt-1">
                      <Clock className="w-3 h-3" />
                      {formatTime(activity.created_at)}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
