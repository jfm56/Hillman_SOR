"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { 
  ArrowLeft, Upload, FileText, Trash2, Star, StarOff, 
  CheckCircle, Clock, AlertCircle 
} from "lucide-react";
import { api } from "@/lib/api";

interface Template {
  id: string;
  name: string;
  description: string | null;
  template_type: string;
  is_active: boolean;
  is_default: boolean;
  original_filename: string | null;
  file_size: number | null;
  structure: Record<string, any>;
  style_guide: Record<string, any>;
  created_at: string;
  processed_at: string | null;
}

export default function TemplatesPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  
  const [showUpload, setShowUpload] = useState(false);
  const [uploadData, setUploadData] = useState({
    name: "",
    description: "",
    template_type: "sor",
    set_as_default: false,
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const data = await api.getTemplates(false);
      setTemplates(data);
    } catch (err) {
      console.error("Failed to load templates:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      if (!uploadData.name) {
        setUploadData({ ...uploadData, name: file.name.replace(/\.[^/.]+$/, "") });
      }
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please select a file");
      return;
    }

    setUploading(true);
    setError("");
    setSuccess("");

    try {
      await api.uploadTemplate(
        selectedFile,
        uploadData.name,
        uploadData.description,
        uploadData.template_type,
        uploadData.set_as_default
      );
      setSuccess("Template uploaded successfully!");
      setShowUpload(false);
      setSelectedFile(null);
      setUploadData({ name: "", description: "", template_type: "sor", set_as_default: false });
      loadTemplates();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to upload template");
    } finally {
      setUploading(false);
    }
  };

  const setAsDefault = async (templateId: string) => {
    try {
      await api.setTemplateDefault(templateId);
      loadTemplates();
    } catch (err) {
      console.error("Failed to set default:", err);
    }
  };

  const deleteTemplate = async (templateId: string) => {
    if (!confirm("Are you sure you want to delete this template?")) return;

    try {
      await api.deleteTemplate(templateId);
      loadTemplates();
    } catch (err) {
      console.error("Failed to delete template:", err);
    }
  };

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return "Unknown";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
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
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push("/settings")}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <h1 className="text-2xl font-bold text-gray-900">Report Templates</h1>
      </div>

      <p className="text-gray-600">
        Upload sample reports to define how your final reports should look. 
        The AI will use these templates as a reference for formatting, structure, and style.
      </p>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {success && (
        <div className="p-4 bg-green-50 text-green-600 rounded-lg flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          {success}
        </div>
      )}

      {/* Upload Section */}
      <div className="bg-white rounded-xl border p-6">
        {!showUpload ? (
          <button
            onClick={() => setShowUpload(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Upload className="w-4 h-4" />
            Upload Template
          </button>
        ) : (
          <form onSubmit={handleUpload} className="space-y-4">
            <h2 className="text-lg font-semibold">Upload New Template</h2>
            
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition-colors"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={handleFileSelect}
                className="hidden"
              />
              {selectedFile ? (
                <div className="flex items-center justify-center gap-2 text-blue-600">
                  <FileText className="w-6 h-6" />
                  <span>{selectedFile.name}</span>
                </div>
              ) : (
                <div className="text-gray-500">
                  <Upload className="w-8 h-8 mx-auto mb-2" />
                  <p>Click to select a PDF or Word document</p>
                  <p className="text-sm">Upload a sample report that shows the desired format</p>
                </div>
              )}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">Template Name</label>
                <input
                  type="text"
                  required
                  value={uploadData.name}
                  onChange={(e) => setUploadData({ ...uploadData, name: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Standard SOR Format"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Template Type</label>
                <select
                  value={uploadData.template_type}
                  onChange={(e) => setUploadData({ ...uploadData, template_type: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="sor">Site Observation Report</option>
                  <option value="photo_log">Photo Log</option>
                  <option value="inspection">Inspection Report</option>
                  <option value="progress">Progress Report</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                rows={2}
                value={uploadData.description}
                onChange={(e) => setUploadData({ ...uploadData, description: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe when to use this template..."
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="setDefault"
                checked={uploadData.set_as_default}
                onChange={(e) => setUploadData({ ...uploadData, set_as_default: e.target.checked })}
                className="rounded border-gray-300"
              />
              <label htmlFor="setDefault" className="text-sm text-gray-700">
                Set as default template for this type
              </label>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={uploading || !selectedFile}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {uploading ? "Uploading..." : "Upload Template"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowUpload(false);
                  setSelectedFile(null);
                }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Templates List */}
      <div className="bg-white rounded-xl border">
        <div className="p-4 border-b">
          <h2 className="font-semibold text-gray-900">Uploaded Templates</h2>
        </div>
        
        {templates.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No templates uploaded yet.</p>
            <p className="text-sm">Upload a sample report to get started.</p>
          </div>
        ) : (
          <div className="divide-y">
            {templates.map((template) => (
              <div key={template.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <FileText className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-gray-900">{template.name}</h3>
                        {template.is_default && (
                          <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full flex items-center gap-1">
                            <Star className="w-3 h-3" />
                            Default
                          </span>
                        )}
                        {!template.is_active && (
                          <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                            Inactive
                          </span>
                        )}
                      </div>
                      {template.description && (
                        <p className="text-sm text-gray-500 mt-1">{template.description}</p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                        <span>{template.template_type.toUpperCase()}</span>
                        {template.original_filename && (
                          <span>{template.original_filename}</span>
                        )}
                        <span>{formatFileSize(template.file_size)}</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(template.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      
                      {/* Show extracted structure */}
                      {template.structure?.sections?.length > 0 && (
                        <div className="mt-2">
                          <span className="text-xs text-gray-500">Sections detected: </span>
                          <span className="text-xs text-blue-600">
                            {template.structure.sections.join(", ")}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {!template.is_default && (
                      <button
                        onClick={() => setAsDefault(template.id)}
                        className="p-2 text-gray-400 hover:text-yellow-500"
                        title="Set as default"
                      >
                        <StarOff className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => deleteTemplate(template.id)}
                      className="p-2 text-gray-400 hover:text-red-500"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
