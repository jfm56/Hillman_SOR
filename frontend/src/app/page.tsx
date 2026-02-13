"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { FileText, Plus, FolderOpen, BarChart3 } from "lucide-react";
import { api } from "@/lib/api";

export default function Dashboard() {
  const { data: projects, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.getProjects(),
  });

  const { data: reports } = useQuery({
    queryKey: ["reports"],
    queryFn: () => api.getReports(),
  });

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">
            Site Observation Report AI System
          </p>
        </div>
        <Link
          href="/projects/new"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="mr-2 h-5 w-5" />
          New Project
        </Link>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-500">Total Projects</h3>
            <FolderOpen className="h-5 w-5 text-gray-400" />
          </div>
          <p className="text-2xl font-bold mt-2">{projects?.length || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-500">Total Reports</h3>
            <FileText className="h-5 w-5 text-gray-400" />
          </div>
          <p className="text-2xl font-bold mt-2">{reports?.length || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-500">Draft Reports</h3>
            <FileText className="h-5 w-5 text-yellow-400" />
          </div>
          <p className="text-2xl font-bold mt-2">
            {reports?.filter((r: any) => r.status === "draft").length || 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-500">Approved</h3>
            <BarChart3 className="h-5 w-5 text-green-400" />
          </div>
          <p className="text-2xl font-bold mt-2">
            {reports?.filter((r: any) => r.status === "approved").length || 0}
          </p>
        </div>
      </div>

      {/* Recent Projects */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold">Recent Projects</h2>
        </div>
        <div className="p-6">
          {isLoading ? (
            <p className="text-gray-500">Loading...</p>
          ) : projects?.length === 0 ? (
            <div className="text-center py-8">
              <FolderOpen className="h-12 w-12 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">No projects yet</p>
              <Link
                href="/projects/new"
                className="text-blue-600 hover:underline mt-2 inline-block"
              >
                Create your first project
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {projects?.slice(0, 5).map((project: any) => (
                <Link
                  key={project.id}
                  href={`/projects/${project.id}`}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center space-x-4">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <FolderOpen className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-medium">{project.name}</h3>
                      <p className="text-sm text-gray-500">{project.client_name}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    project.status === "active" 
                      ? "bg-green-100 text-green-800" 
                      : "bg-gray-100 text-gray-800"
                  }`}>
                    {project.status}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
