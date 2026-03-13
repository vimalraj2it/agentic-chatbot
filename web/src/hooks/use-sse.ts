"use client";

import { useState, useEffect, useCallback, useRef } from "react";

export type SSEEvent = {
    type: "token" | "status" | "error" | "complete";
    content?: string;
    token?: string;
    taskId?: string;
    step?: string;
    error?: string;
    metadata?: any;
};

interface UseSSEOptions {
    sessionId?: string;
    onToken?: (token: string) => void;
    onStatus?: (status: string, metadata?: any) => void;
    onError?: (error: string) => void;
    onComplete?: (data: any) => void;
}

export function useSSE({
    sessionId,
    onToken,
    onStatus,
    onError,
    onComplete
}: UseSSEOptions = {}) {
    const [status, setStatus] = useState<string>("idle");
    const [error, setError] = useState<string | null>(null);
    const eventSourceRef = useRef<EventSource | null>(null);

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    const connect = useCallback(() => {
        if (!sessionId) return;

        // Close existing connection if any
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        const url = `${baseUrl}/api/chat/stream/${sessionId}`;
        console.log(`Connecting to SSE: ${url}`);
        
        const eventSource = new EventSource(url);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
            console.log("SSE Connection opened");
            setStatus("connected");
        };

        eventSource.onerror = (e) => {
            console.error("SSE Error:", e);
            setError("Connection error");
            setStatus("error");
            eventSource.close();
        };

        eventSource.addEventListener("token", (event) => {
            const data = JSON.parse(event.data);
            if (onToken) onToken(data.token);
        });

        eventSource.addEventListener("status", (event) => {
            const data = JSON.parse(event.data);
            setStatus(data.content);
            if (onStatus) onStatus(data.content, data.metadata);
        });

        eventSource.addEventListener("error", (event) => {
            const data = JSON.parse(event.data);
            setError(data.content);
            if (onError) onError(data.content);
        });

        eventSource.addEventListener("complete", (event) => {
            const data = JSON.parse(event.data);
            setStatus("complete");
            if (onComplete) onComplete(data);
            eventSource.close();
        });

    }, [sessionId, baseUrl, onToken, onStatus, onError, onComplete]);

    const disconnect = useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
            setStatus("disconnected");
        }
    }, []);

    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, []);

    return {
        status,
        error,
        connect,
        disconnect
    };
}
