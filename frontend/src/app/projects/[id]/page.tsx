"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Plus, FileText, Calendar, MapPin, Building2, Pencil, Save, X } from "lucide-react";

interface Project {
  id: string;
  name: string;
  client_name: string;
  project_number: string;
  description: string;
  status: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  created_at: string;
}

interface Report {
  id: string;
  report_number: number;
  report_date: string;
  inspection_date: string;
  status: string;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateReport, setShowCreateReport] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    name: "",
    client_name: "",
    project_number: "",
    description: "",
    address: "",
    city: "",
    state: "",
    zip_code: "",
    status: "",
  });
  const [newReport, setNewReport] = useState({
    report_date: new Date().toISOString().split("T")[0],
    inspection_date: new Date().toISOString().split("T")[0],
  });

  useEffect(() => {
    if (params.id) {
      loadProject();
      loadReports();
    }
  }, [params.id]);

  const loadProject = async () => {
    try {
      const response = await fetch(`/api/v1/projects/${params.id}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (response.ok) {
        const data = await response.json();
        setProject(data);
      }
    } catch (err) {
      console.error("Failed to load project:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadReports = async () => {
    try {
      const response = await fetch(`/api/v1/reports?project_id=${params.id}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (response.ok) {
        const data = await response.json();
        setReports(data);
      }
    } catch (err) {
      console.error("Failed to load reports:", err);
    }
  };

  const startEditing = () => {
    if (project) {
      setEditData({
        name: project.name || "",
        client_name: project.client_name || "",
        project_number: project.project_number || "",
        description: project.description || "",
        address: project.address || "",
        city: project.city || "",
        state: project.state || "",
        zip_code: project.zip_code || "",
        status: project.status || "active",
      });
      setIsEditing(true);
    }
  };

  const saveProject = async () => {
    try {
      const response = await fetch(`/api/v1/projects/${params.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify(editData),
      });
      if (response.ok) {
        setIsEditing(false);
        loadProject();
      }
    } catch (err) {
      console.error("Failed to update project:", err);
    }
  };

  const createReport = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch("/api/v1/reports", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          project_id: params.id,
          report_number: reports.length + 1,
          ...newReport,
        }),
      });
      if (response.ok) {
        const report = await response.json();
        router.push(`/reports/${report.id}`);
      }
    } catch (err) {
      console.error("Failed to create report:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">Project not found</h2>
        <button
          onClick={() => router.push("/projects")}
          className="mt-4 text-blue-600 hover:underline"
        >
          Back to Projects
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <button
        onClick={() => router.push("/projects")}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Projects
      </button>

      {/* Project Header */}
      <div className="bg-white rounded-xl border p-6">
        {isEditing ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Edit Project</h2>
              <button
                onClick={() => setIsEditing(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700">Project Name</label>
                <input
                  type="text"
                  value={editData.name}
                  onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Client Name</label>
                <input
                  type="text"
                  value={editData.client_name}
                  onChange={(e) => setEditData({ ...editData, client_name: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Project Number</label>
                <input
                  type="text"
                  value={editData.project_number}
                  onChange={(e) => setEditData({ ...editData, project_number: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  rows={3}
                  value={editData.description}
                  onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700">Address</label>
                <input
                  type="text"
                  value={editData.address}
                  onChange={(e) => setEditData({ ...editData, address: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">City</label>
                <input
                  type="text"
                  value={editData.city}
                  onChange={(e) => setEditData({ ...editData, city: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">State</label>
                  <input
                    type="text"
                    value={editData.state}
                    onChange={(e) => setEditData({ ...editData, state: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">ZIP</label>
                  <input
                    type="text"
                    value={editData.zip_code}
                    onChange={(e) => setEditData({ ...editData, zip_code: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Status</label>
                <select
                  value={editData.status}
                  onChange={(e) => setEditData({ ...editData, status: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                  <option value="on_hold">On Hold</option>
                </select>
              </div>
            </div>
            
            <div className="flex gap-3 pt-4">
              <button
                onClick={saveProject}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Save className="w-4 h-4" />
                Save Changes
              </button>
              <button
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
                <p className="text-gray-500 mt-1">{project.client_name}</p>
                {project.project_number && (
                  <p className="text-sm text-gray-400 mt-1">#{project.project_number}</p>
                )}
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={startEditing}
                  className="flex items-center gap-2 px-3 py-1.5 text-gray-600 border rounded-lg hover:bg-gray-50"
                >
                  <Pencil className="w-4 h-4" />
                  Edit
                </button>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  project.status === "active" ? "bg-green-100 text-green-700" : 
                  project.status === "completed" ? "bg-blue-100 text-blue-700" :
                  "bg-gray-100 text-gray-600"
                }`}>
                  {project.status}
                </span>
              </div>
            </div>

            {project.description && (
              <p className="mt-4 text-gray-600">{project.description}</p>
            )}

            <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-500">
              {project.address && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {project.address}, {project.city}, {project.state} {project.zip_code}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                Created {new Date(project.created_at).toLocaleDateString()}
              </span>
            </div>
          </>
        )}
      </div>

      {/* Reports Section */}
      <div className="bg-white rounded-xl border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Site Observation Reports</h2>
          <button
            onClick={() => setShowCreateReport(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            New Report
          </button>
        </div>

        {showCreateReport && (
          <form onSubmit={createReport} className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium mb-3">Create New Report</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">Report Date</label>
                <input
                  type="date"
                  value={newReport.report_date}
                  onChange={(e) => setNewReport({ ...newReport, report_date: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Inspection Date</label>
                <input
                  type="date"
                  value={newReport.inspection_date}
                  onChange={(e) => setNewReport({ ...newReport, inspection_date: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-lg"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-4">
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">
                Create Report
              </button>
              <button
                type="button"
                onClick={() => setShowCreateReport(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {reports.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No reports yet. Create your first report to get started.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((report) => (
              <div
                key={report.id}
                onClick={() => router.push(`/reports/${report.id}`)}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="font-medium">SOR #{report.report_number}</p>
                    <p className="text-sm text-gray-500">
                      Inspection: {new Date(report.inspection_date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  report.status === "approved" ? "bg-green-100 text-green-700" :
                  report.status === "draft" ? "bg-gray-100 text-gray-600" :
                  "bg-yellow-100 text-yellow-700"
                }`}>
                  {report.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
