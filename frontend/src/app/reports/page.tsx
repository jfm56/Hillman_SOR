"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { FileText, Calendar, Clock, CheckCircle, AlertCircle } from "lucide-react";

interface Report {
  id: string;
  project_id: string;
  report_number: number;
  report_date: string;
  inspection_date: string;
  status: string;
  version: number;
  created_at: string;
}

const statusColors: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  in_review: "bg-yellow-100 text-yellow-700",
  approved: "bg-green-100 text-green-700",
  published: "bg-blue-100 text-blue-700",
};

const statusIcons: Record<string, React.ReactNode> = {
  draft: <Clock className="w-4 h-4" />,
  in_review: <AlertCircle className="w-4 h-4" />,
  approved: <CheckCircle className="w-4 h-4" />,
  published: <CheckCircle className="w-4 h-4" />,
};

export default function ReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const data = await api.getReports();
      setReports(data);
    } catch (err) {
      console.error("Failed to load reports:", err);
    } finally {
      setLoading(false);
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
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
      </div>

      {reports.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No reports yet</h3>
          <p className="text-gray-500 mt-1">Reports will appear here once created from projects</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Report #</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Report Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Inspection Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Version</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reports.map((report) => (
                <tr
                  key={report.id}
                  onClick={() => router.push(`/reports/${report.id}`)}
                  className="hover:bg-gray-50 cursor-pointer"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <FileText className="w-5 h-5 text-gray-400 mr-3" />
                      <span className="font-medium text-gray-900">SOR #{report.report_number}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      {new Date(report.report_date).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(report.inspection_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[report.status] || "bg-gray-100 text-gray-700"}`}>
                      {statusIcons[report.status]}
                      {report.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    v{report.version}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
