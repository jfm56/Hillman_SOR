"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Save, Sparkles, CheckCircle } from "lucide-react";

interface ReportSection {
  id: string;
  section_type: string;
  title: string;
  ai_draft: string | null;
  human_content: string | null;
  final_content: string | null;
  is_approved: boolean;
}

interface Report {
  id: string;
  project_id: string;
  report_number: number;
  report_date: string;
  inspection_date: string;
  status: string;
  version: number;
  weather_conditions: string | null;
  personnel_on_site: string | null;
  executive_summary: string | null;
  sections: ReportSection[];
}

export default function ReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");

  useEffect(() => {
    if (params.id) {
      loadReport();
    }
  }, [params.id]);

  const loadReport = async () => {
    try {
      const response = await fetch(`/api/v1/reports/${params.id}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (response.ok) {
        const data = await response.json();
        setReport(data);
      }
    } catch (err) {
      console.error("Failed to load report:", err);
    } finally {
      setLoading(false);
    }
  };

  const generateDrafts = async () => {
    setGenerating(true);
    try {
      const response = await fetch(`/api/v1/reports/${params.id}/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          sections: ["executive_summary", "site_conditions", "work_observed", "recommendations"],
        }),
      });
      if (response.ok) {
        loadReport();
      }
    } catch (err) {
      console.error("Failed to generate drafts:", err);
    } finally {
      setGenerating(false);
    }
  };

  const saveSection = async (sectionId: string) => {
    try {
      await fetch(`/api/v1/reports/${params.id}/sections/${sectionId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ human_content: editContent }),
      });
      setActiveSection(null);
      loadReport();
    } catch (err) {
      console.error("Failed to save section:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">Report not found</h2>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <div className="flex gap-3">
          <button
            onClick={generateDrafts}
            disabled={generating}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            {generating ? "Generating..." : "Generate AI Drafts"}
          </button>
        </div>
      </div>

      {/* Report Header */}
      <div className="bg-white rounded-xl border p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Site Observation Report #{report.report_number}
            </h1>
            <p className="text-gray-500 mt-1">
              Inspection Date: {new Date(report.inspection_date).toLocaleDateString()}
            </p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            report.status === "approved" ? "bg-green-100 text-green-700" :
            report.status === "draft" ? "bg-gray-100 text-gray-600" :
            "bg-yellow-100 text-yellow-700"
          }`}>
            {report.status}
          </span>
        </div>

        <div className="grid gap-4 md:grid-cols-3 mt-6 text-sm">
          <div>
            <span className="text-gray-500">Report Date</span>
            <p className="font-medium">{new Date(report.report_date).toLocaleDateString()}</p>
          </div>
          <div>
            <span className="text-gray-500">Weather</span>
            <p className="font-medium">{report.weather_conditions || "Not recorded"}</p>
          </div>
          <div>
            <span className="text-gray-500">Personnel</span>
            <p className="font-medium">{report.personnel_on_site || "Not recorded"}</p>
          </div>
        </div>
      </div>

      {/* Sections */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Report Sections</h2>
        
        {report.sections.length === 0 ? (
          <div className="bg-white rounded-xl border p-8 text-center text-gray-500">
            <Sparkles className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No sections yet. Click "Generate AI Drafts" to create initial content.</p>
          </div>
        ) : (
          report.sections.map((section) => (
            <div key={section.id} className="bg-white rounded-xl border p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">{section.title}</h3>
                <div className="flex items-center gap-2">
                  {section.is_approved && (
                    <span className="flex items-center gap-1 text-green-600 text-sm">
                      <CheckCircle className="w-4 h-4" /> Approved
                    </span>
                  )}
                </div>
              </div>

              {activeSection === section.id ? (
                <div className="space-y-3">
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={8}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => saveSection(section.id)}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg"
                    >
                      <Save className="w-4 h-4" /> Save
                    </button>
                    <button
                      onClick={() => setActiveSection(null)}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  {section.ai_draft && !section.human_content && (
                    <div className="mb-3 p-3 bg-purple-50 rounded-lg">
                      <p className="text-xs text-purple-600 font-medium mb-1">AI Generated Draft</p>
                      <p className="text-gray-700 whitespace-pre-wrap">{section.ai_draft}</p>
                    </div>
                  )}
                  {section.human_content && (
                    <p className="text-gray-700 whitespace-pre-wrap">{section.human_content}</p>
                  )}
                  {!section.ai_draft && !section.human_content && (
                    <p className="text-gray-400 italic">No content yet</p>
                  )}
                  <button
                    onClick={() => {
                      setActiveSection(section.id);
                      setEditContent(section.human_content || section.ai_draft || "");
                    }}
                    className="mt-3 text-blue-600 hover:underline text-sm"
                  >
                    Edit Section
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
