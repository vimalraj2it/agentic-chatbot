const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = {
    async login(mobileNumber: string) {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mobile_number: mobileNumber }),
        });
        if (!res.ok) throw new Error("Login failed");
        return res.json();
    },

    async listSessions(userId: string) {
        const res = await fetch(`${API_BASE}/api/sessions/${userId}`);
        if (!res.ok) throw new Error("Failed to fetch sessions");
        return res.json();
    },

    async createSession(userId: string, title?: string) {
        const res = await fetch(`${API_BASE}/api/sessions/${userId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title }),
        });
        if (!res.ok) throw new Error("Failed to create session");
        return res.json();
    },

    async listDocuments() {
        const res = await fetch(`${API_BASE}/api/documents/`);
        if (!res.ok) throw new Error("Failed to fetch documents");
        return res.json();
    },

    async uploadDocument(file: File) {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${API_BASE}/api/documents/upload`, {
            method: "POST",
            body: formData,
        });
        if (!res.ok) throw new Error("Failed to upload document");
        return res.json();
    },

    async loadDocument(docId: string) {
        const res = await fetch(`${API_BASE}/api/documents/${docId}/load`, { method: "POST" });
        if (!res.ok) throw new Error("Failed to load document");
        return res.json();
    },

    async unloadDocument(docId: string) {
        const res = await fetch(`${API_BASE}/api/documents/${docId}/unload`, { method: "POST" });
        if (!res.ok) throw new Error("Failed to unload document");
        return res.json();
    },

    async reloadDocument(docId: string) {
        const res = await fetch(`${API_BASE}/api/documents/${docId}/reload`, { method: "POST" });
        if (!res.ok) throw new Error("Failed to reload document");
        return res.json();
    },

    async deleteDocument(docId: string) {
        const res = await fetch(`${API_BASE}/api/documents/${docId}`, { method: "DELETE" });
        if (!res.ok) throw new Error("Failed to delete document");
        return res.json();
    }
};
