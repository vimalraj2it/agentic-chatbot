"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Bot, ArrowRight, Smartphone } from "lucide-react";
import { apiClient } from "@/lib/api-client";

export default function LoginPage() {
    const [mobile, setMobile] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!mobile.trim() || isLoading) return;

        setIsLoading(true);
        try {
            const user = await apiClient.login(mobile);
            localStorage.setItem("chat_user", JSON.stringify(user));
            router.push("/sessions");
        } catch (error) {
            console.error(error);
            alert("Login failed. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-background p-4 flex-col">
            <div className="w-full max-w-md space-y-8 bg-card p-8 rounded-2xl border border-border shadow-xl">
                <div className="flex flex-col items-center text-center space-y-2">
                    <div className="w-16 h-16 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center shadow-lg mb-4">
                        <Bot size={36} />
                    </div>
                    <h1 className="text-3xl font-bold tracking-tight">Welcome to Chat AI</h1>
                    <p className="text-muted-foreground">Enter your mobile number to get started</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-6">
                    <div className="relative">
                        <Smartphone className="absolute left-3 top-3 text-muted-foreground" size={20} />
                        <input
                            type="tel"
                            placeholder="Mobile Number"
                            className="w-full pl-10 pr-4 py-3 bg-muted rounded-xl border-none focus:ring-2 focus:ring-primary outline-none transition-all"
                            value={mobile}
                            onChange={(e) => setMobile(e.target.value)}
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full py-3 bg-primary text-primary-foreground rounded-xl font-bold flex items-center justify-center gap-2 hover:opacity-90 transition-all disabled:opacity-50"
                    >
                        {isLoading ? "Signing in..." : "Get Started"}
                        <ArrowRight size={20} />
                    </button>
                </form>
            </div>

            <p className="mt-8 text-sm text-muted-foreground">
                Powered by LangGraph & shadcn/ui
            </p>
        </div>
    );
}
