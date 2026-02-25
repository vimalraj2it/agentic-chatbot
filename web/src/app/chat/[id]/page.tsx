"use client";

import { useRef, useEffect, useState, use } from "react";
import { Bot, Trash2, Terminal, ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { useChatbot } from "@/hooks/use-chatbot";
import { ChatMessage } from "@/components/chat/chat-message";
import { ChatInput } from "@/components/chat/chat-input";

export default function ChatPage({ params }: { params: Promise<{ id: string }> }) {
    const resolvedParams = use(params);
    const sessionId = resolvedParams.id;
    const [isHistoryLoaded, setIsHistoryLoaded] = useState(false);
    const [skip, setSkip] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const router = useRouter();

    const [user, setUser] = useState<{ id: string } | null>(null);

    useEffect(() => {
        const storedUser = localStorage.getItem("chat_user");
        if (storedUser) {
            setUser(JSON.parse(storedUser));
        } else {
            router.push("/login");
        }
    }, [router]);

    const {
        messages,
        input,
        handleInputChange,
        handleSubmit,
        isLoading,
        setMessages,
        pendingImages,
        setPendingImages
    } = useChatbot({
        api: "/api/chat",
        body: {
            session_id: sessionId,
            user_id: user?.id
        }
    });

    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!sessionId) return;
        // Fetch initial history for this session
        fetchHistory(0);
    }, [sessionId]);

    const fetchHistory = async (skipCount: number) => {
        try {
            const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            const res = await fetch(`${API_BASE}/api/chat/history/${sessionId}?skip=${skipCount}&limit=10`);
            if (res.ok) {
                const history = await res.json();
                if (history && history.length > 0) {
                    if (skipCount === 0) {
                        setMessages(history);
                    } else {
                        // Prepend older messages
                        setMessages((prev) => [...history, ...prev]);
                    }

                    if (history.length < 10) {
                        setHasMore(false);
                    }
                } else {
                    if (skipCount === 0) {
                        setMessages([
                            { id: "welcome", role: "assistant", content: "Hello! History for this session is empty. How can I help?" }
                        ]);
                    }
                    setHasMore(false);
                }
            }
        } catch (error) {
            console.error("Failed to fetch history:", error);
        } finally {
            setIsHistoryLoaded(true);
        }
    };

    const loadMore = () => {
        const nextSkip = skip + 10;
        setSkip(nextSkip);
        fetchHistory(nextSkip);
    };

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    if (!isHistoryLoaded) return <div className="flex h-screen items-center justify-center bg-background">Loading chat...</div>;

    return (
        <div className="flex flex-col h-screen bg-background text-foreground">
            <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-xl sticky top-0 z-10">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => router.push("/sessions")}
                        className="p-2 hover:bg-muted rounded-lg transition-all"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div className="w-10 h-10 rounded-xl bg-primary text-primary-foreground flex items-center justify-center shadow-lg">
                        <Bot size={22} />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold tracking-tight">shadcn Chatbot</h1>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-medium">Session: {sessionId?.substr(0, 8) || "New"}</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => setMessages([])}
                        className="p-2.5 hover:bg-muted rounded-xl transition-all text-muted-foreground hover:text-foreground border border-transparent hover:border-border"
                    >
                        <Trash2 size={18} />
                    </button>
                </div>
            </header>

            <main
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth"
            >
                <div className="max-w-3xl mx-auto w-full">
                    {hasMore && messages.length >= 10 && (
                        <div className="flex justify-center mb-6">
                            <button
                                onClick={loadMore}
                                className="text-xs font-medium uppercase tracking-widest text-muted-foreground hover:text-primary transition-colors py-2 px-4 border border-border rounded-full bg-card/20 backdrop-blur-sm"
                            >
                                Load Previous Messages
                            </button>
                        </div>
                    )}
                    {messages.map((msg, i) => (
                        <ChatMessage key={msg.id || i} role={msg.role} content={msg.content} />
                    ))}
                    {isLoading && (
                        <div className="flex justify-start mb-4">
                            <div className="bg-muted px-4 py-2 rounded-lg rounded-tl-none animate-pulse text-sm text-muted-foreground">
                                Thinking...
                            </div>
                        </div>
                    )}
                </div>
            </main>

            <footer className="p-4 md:p-8 border-t border-border bg-card/30 backdrop-blur-md">
                <div className="max-w-3xl mx-auto">
                    <ChatInput
                        value={input}
                        onChange={handleInputChange}
                        onSubmit={handleSubmit}
                        isLoading={isLoading}
                        placeholder="Message AI..."
                        pendingImages={pendingImages}
                        onImageAdd={(img) => setPendingImages((prev) => [...prev, img])}
                        onImageRemove={(index) => setPendingImages((prev) => prev.filter((_, i) => i !== index))}
                    />
                    <div className="flex justify-between items-center mt-6 px-1">
                        <div className="flex gap-3">
                            <div className="flex items-center gap-1.5">
                                <Terminal size={12} className="text-muted-foreground" />
                                <span className="text-[10px] text-muted-foreground font-mono uppercase tracking-widest">v2.1.0-shadcn</span>
                            </div>
                        </div>
                        <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-tighter italic">
                            Powered by LangGraph & shadcn/ui
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    );
}
