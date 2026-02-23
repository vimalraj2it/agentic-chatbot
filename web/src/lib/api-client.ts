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
    }
};
