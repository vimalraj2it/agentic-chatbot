"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Bot, Plus, MessageSquare, Clock, LogOut, FileText } from "lucide-react";
import { apiClient } from "@/lib/api-client";

export default function SessionsPage() {
    const [user, setUser] = useState<any>(null);
    const [sessions, setSessions] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        const storedUser = localStorage.getItem("chat_user");
        if (!storedUser) {
            router.push("/login");
            return;
        }
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
        fetchSessions(parsedUser.id);
    }, []);

    const fetchSessions = async (userId: string) => {
        try {
            const data = await apiClient.listSessions(userId);
            setSessions(data.sessions);
        } catch (error) {
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreateSession = async () => {
        if (!user) return;
        try {
            const newSession = await apiClient.createSession(user.id);
            router.push(`/chat/${newSession.id}`);
        } catch (error) {
            console.error(error);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("chat_user");
        router.push("/login");
    };

    if (isLoading) return <div className="flex h-screen items-center justify-center bg-background">Loading sessions...</div>;

    return (
        <div className="flex flex-col min-h-screen bg-background text-foreground">
            <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-xl">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary text-primary-foreground flex items-center justify-center shadow-lg">
                        <Bot size={22} />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold">My Chats</h1>
                        <p className="text-[10px] text-muted-foreground">User ID: {user?.id?.substr(0, 8) || "N/A"}</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => router.push("/documents")}
                        className="p-2 hover:bg-muted rounded-lg text-muted-foreground transition-all flex items-center gap-2"
                        title="Document Management"
                    >
                        <FileText size={20} />
                        <span className="hidden md:inline text-xs font-medium">Docs</span>
                    </button>
                    <button onClick={handleLogout} className="p-2 hover:bg-muted rounded-lg text-muted-foreground transition-all">
                        <LogOut size={20} />
                    </button>
                </div>
            </header>

            <main className="flex-1 p-4 md:p-8 max-w-4xl mx-auto w-full">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <button
                        onClick={handleCreateSession}
                        className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-border rounded-2xl hover:border-primary hover:bg-primary/5 transition-all space-y-4 group min-h-[160px]"
                    >
                        <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center group-hover:scale-110 transition-transform">
                            <Plus size={24} />
                        </div>
                        <div className="text-center">
                            <span className="font-bold block">New Chat Session</span>
                            <span className="text-sm text-muted-foreground">Start a fresh conversation</span>
                        </div>
                    </button>

                    <button
                        onClick={() => router.push("/documents")}
                        className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-border rounded-2xl hover:border-secondary hover:bg-secondary/5 transition-all space-y-4 group min-h-[160px]"
                    >
                        <div className="w-12 h-12 rounded-full bg-secondary/10 text-secondary flex items-center justify-center group-hover:scale-110 transition-transform">
                            <FileText size={24} />
                        </div>
                        <div className="text-center">
                            <span className="font-bold block">Document Library</span>
                            <span className="text-sm text-muted-foreground">Manage PDF references & RAG</span>
                        </div>
                    </button>

                    {sessions.map((session) => (
                        <button
                            key={session.id}
                            onClick={() => router.push(`/chat/${session.id}`)}
                            className="flex flex-col items-start p-6 bg-card border border-border rounded-2xl hover:border-primary/50 hover:shadow-md transition-all text-left relative overflow-hidden group"
                        >
                            <div className="flex items-center gap-3 mb-2">
                                <MessageSquare size={18} className="text-primary" />
                                <span className="font-bold">{session.title}</span>
                            </div>
                            <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                                <Clock size={12} />
                                <span>{new Date(session.updated_at).toLocaleString()}</span>
                            </div>
                            <div className="text-xs text-muted-foreground mt-4 line-clamp-1">
                                ID: {session.id}
                            </div>
                            <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                <ArrowRight size={16} />
                            </div>
                        </button>
                    ))}
                </div>
            </main>
        </div>
    );
}

function ArrowRight({ size }: { size: number }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M5 12h14"></path>
            <path d="m12 5 7 7-7 7"></path>
        </svg>
    );
}
