import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const client = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to requests
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Auth
  login: async (email: string, password: string) => {
    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);
    const { data } = await client.post("/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    localStorage.setItem("token", data.access_token);
    return data;
  },

  logout: () => {
    localStorage.removeItem("token");
  },

  getMe: async () => {
    const { data } = await client.get("/auth/me");
    return data;
  },

  // Projects
  getProjects: async () => {
    const { data } = await client.get("/projects");
    return data;
  },

  getProject: async (id: string) => {
    const { data } = await client.get(`/projects/${id}`);
    return data;
  },

  createProject: async (project: any) => {
    const { data } = await client.post("/projects", project);
    return data;
  },

  updateProject: async (id: string, project: any) => {
    const { data } = await client.put(`/projects/${id}`, project);
    return data;
  },

  // Sites
  getSites: async (projectId?: string) => {
    const params = projectId ? { project_id: projectId } : {};
    const { data } = await client.get("/sites", { params });
    return data;
  },

  createSite: async (site: any) => {
    const { data } = await client.post("/sites", site);
    return data;
  },

  // Buildings
  getBuildings: async (siteId?: string) => {
    const params = siteId ? { site_id: siteId } : {};
    const { data } = await client.get("/buildings", { params });
    return data;
  },

  createBuilding: async (building: any) => {
    const { data } = await client.post("/buildings", building);
    return data;
  },

  // File Upload
  uploadImages: async (files: File[], projectId: string, buildingId?: string) => {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    formData.append("project_id", projectId);
    if (buildingId) formData.append("building_id", buildingId);
    
    const { data } = await client.post("/upload/images", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  uploadDocuments: async (files: File[], projectId: string, documentType: string) => {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    formData.append("project_id", projectId);
    formData.append("document_type", documentType);
    
    const { data } = await client.post("/upload/documents", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  // Reports
  getReports: async (projectId?: string) => {
    const params = projectId ? { project_id: projectId } : {};
    const { data } = await client.get("/reports", { params });
    return data;
  },

  getReport: async (id: string) => {
    const { data } = await client.get(`/reports/${id}`);
    return data;
  },

  createReport: async (report: any) => {
    const { data } = await client.post("/reports", report);
    return data;
  },

  generateReportDrafts: async (reportId: string, sections: string[], options?: any) => {
    const { data } = await client.post(`/reports/${reportId}/generate`, {
      sections,
      options,
    });
    return data;
  },

  updateSection: async (reportId: string, sectionId: string, content: any) => {
    const { data } = await client.put(`/reports/${reportId}/sections/${sectionId}`, content);
    return data;
  },

  approveReport: async (reportId: string) => {
    const { data } = await client.post(`/reports/${reportId}/approve`);
    return data;
  },

  // AI
  analyzeImage: async (imageId: string) => {
    const { data } = await client.post("/ai/analyze-image", { image_id: imageId });
    return data;
  },

  parseDocument: async (documentId: string) => {
    const { data } = await client.post("/ai/parse-document", { document_id: documentId });
    return data;
  },

  rewriteText: async (text: string, style?: string, context?: any) => {
    const { data } = await client.post("/ai/rewrite", { text, style, context });
    return data;
  },

  // Chat
  getChatSessions: async () => {
    const { data } = await client.get("/chat/sessions");
    return data;
  },

  createChatSession: async (projectId?: string, reportId?: string) => {
    const { data } = await client.post("/chat/sessions", {
      project_id: projectId,
      report_id: reportId,
    });
    return data;
  },

  getChatSession: async (sessionId: string) => {
    const { data } = await client.get(`/chat/sessions/${sessionId}`);
    return data;
  },

  sendChatMessage: async (sessionId: string, content: string, context?: any) => {
    const { data } = await client.post(`/chat/sessions/${sessionId}/messages`, {
      content,
      context,
    });
    return data;
  },
};
