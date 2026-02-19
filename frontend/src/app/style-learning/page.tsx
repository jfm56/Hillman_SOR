"use client";

import { useEffect, useState } from "react";
import { Upload, FileText, Trash2, BookOpen, CheckCircle, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";

interface StyleSample {
  id: string;
  source_name: string;
  created_at: string;
  sections: { type: string; preview: string }[];
}

interface ProcessResult {
  sample_id: string;
  source_name: string;
  sections_extracted: number;
  style_characteristics: {
    voice?: string;
    tone?: string;
    sentence_length?: string;
  };
  common_phrases: string[];
  terminology: string[];
}

export default function StyleLearningPage() {
  const [samples, setSamples] = useState<StyleSample[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"upload" | "samples">("upload");
  const [textContent, setTextContent] = useState("");
  const [sourceName, setSourceName] = useState("");

  useEffect(() => {
    loadSamples();
  }, []);

  const loadSamples = async () => {
    try {
      const data = await api.getStyleSamples();
      setSamples(data);
    } catch (err) {
      console.error("Failed to load samples:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError("");
    setResult(null);

    try {
      const data = await api.uploadStyleFile(file, sourceName || file.name);
      setResult(data);
      loadSamples();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to upload file");
    } finally {
      setUploading(false);
    }
  };

  const handleTextUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textContent.trim()) return;

    setUploading(true);
    setError("");
    setResult(null);

    try {
      const data = await api.uploadStyleText(textContent, sourceName || "Pasted Report", "sor");
      setResult(data);
      setTextContent("");
      setSourceName("");
      loadSamples();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to process text");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (sampleId: string) => {
    if (!confirm("Delete this style sample?")) return;

    try {
      await api.deleteStyleSample(sampleId);
      loadSamples();
    } catch (err) {
      console.error("Failed to delete sample:", err);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Style Learning</h1>
        <p className="text-gray-500 mt-1">
          Upload existing reports to teach the AI your preferred writing style and terminology
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab("upload")}
          className={`px-4 py-2 font-medium border-b-2 -mb-px transition-colors ${
            activeTab === "upload"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          <Upload className="w-4 h-4 inline mr-2" />
          Upload Report
        </button>
        <button
          onClick={() => setActiveTab("samples")}
          className={`px-4 py-2 font-medium border-b-2 -mb-px transition-colors ${
            activeTab === "samples"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          <BookOpen className="w-4 h-4 inline mr-2" />
          Learned Samples ({samples.length})
        </button>
      </div>

      {activeTab === "upload" && (
        <div className="space-y-6">
          {/* Error/Success Messages */}
          {error && (
            <div className="flex items-center gap-2 p-4 bg-red-50 text-red-700 rounded-lg">
              <AlertCircle className="w-5 h-5" />
              {error}
            </div>
          )}

          {result && (
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="flex items-center gap-2 text-green-700 font-medium mb-2">
                <CheckCircle className="w-5 h-5" />
                Successfully processed: {result.source_name}
              </div>
              <div className="text-sm text-green-600 space-y-1">
                <p>Sections extracted: {result.sections_extracted}</p>
                {result.style_characteristics.tone && (
                  <p>Tone: {result.style_characteristics.tone}</p>
                )}
                {result.common_phrases.length > 0 && (
                  <p>Common phrases: {result.common_phrases.slice(0, 5).join(", ")}</p>
                )}
              </div>
            </div>
          )}

          {/* File Upload */}
          <div className="bg-white rounded-xl border p-6">
            <h2 className="text-lg font-semibold mb-4">Upload PDF Report</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Source Name (optional)
                </label>
                <input
                  type="text"
                  value={sourceName}
                  onChange={(e) => setSourceName(e.target.value)}
                  placeholder="e.g., Sample SOR from Project XYZ"
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div className="border-2 border-dashed rounded-lg p-8 text-center">
                <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <label className="cursor-pointer">
                  <span className="text-blue-600 hover:underline font-medium">
                    Choose a PDF file
                  </span>
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileUpload}
                    className="hidden"
                    disabled={uploading}
                  />
                </label>
                <p className="text-sm text-gray-500 mt-2">
                  Upload previous Site Observation Reports to learn from
                </p>
              </div>
            </div>
          </div>

          {/* Text Paste */}
          <div className="bg-white rounded-xl border p-6">
            <h2 className="text-lg font-semibold mb-4">Or Paste Report Text</h2>
            <form onSubmit={handleTextUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Report Content
                </label>
                <textarea
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  rows={10}
                  placeholder="Paste your report text here..."
                  className="w-full px-3 py-2 border rounded-lg font-mono text-sm"
                />
              </div>
              <button
                type="submit"
                disabled={uploading || !textContent.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {uploading ? "Processing..." : "Process Report"}
              </button>
            </form>
          </div>
        </div>
      )}

      {activeTab === "samples" && (
        <div className="space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : samples.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-xl border">
              <BookOpen className="w-12 h-12 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">No samples yet</h3>
              <p className="text-gray-500 mt-1">
                Upload reports to teach the AI your writing style
              </p>
            </div>
          ) : (
            samples.map((sample) => (
              <div key={sample.id} className="bg-white rounded-xl border p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{sample.source_name}</h3>
                    <p className="text-sm text-gray-500">
                      Added {new Date(sample.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDelete(sample.id)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {sample.sections.map((section, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600"
                    >
                      {section.type.replace("_", " ")}
                    </span>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
