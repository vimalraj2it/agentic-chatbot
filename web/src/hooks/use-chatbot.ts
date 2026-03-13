"use client";

import { useState, useCallback } from "react";

export type MessageContent = string | Array<{
    type: "text" | "image_url";
    text?: string;
    image_url?: { url: string };
}>;

export type Message = {
    id: string;
    role: "user" | "assistant" | "system";
    content: MessageContent;
};

interface UseChatbotOptions {
    api?: string;
    body?: Record<string, any>;
    initialMessages?: Message[];
}

export function useChatbot({
    api,
    body = {},
    initialMessages = [],
}: UseChatbotOptions = {}) {
    const [messages, setMessages] = useState<Message[]>(initialMessages);
    const [input, setInput] = useState("");
    const [pendingImages, setPendingImages] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const chatApiUrl = api || `${baseUrl}/api/chat`;

    // If session_id changes, we could fetch history here if we wanted to 
    // keep logic in the hook, but for now we'll handle it in the Page component 
    // to match the "ChatPage" fetch requirement.

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setInput(e.target.value);
    };

    const handleSubmit = useCallback(
        async (e?: React.FormEvent) => {
            e?.preventDefault();
            if ((!input.trim() && pendingImages.length === 0) || isLoading) return;

            // Construct multi-modal content if images are present
            let content: MessageContent = input;
            if (pendingImages.length > 0) {
                content = [
                    { type: "text", text: input },
                    ...pendingImages.map(img => ({
                        type: "image_url" as const,
                        image_url: { url: img }
                    }))
                ];
            }

            const userMessage: Message = {
                id: Date.now().toString(),
                role: "user",
                content,
            };

            const currentImages = [...pendingImages];
            setMessages((prev) => [...prev, userMessage]);
            setInput("");
            setPendingImages([]);
            setIsLoading(true);

            const assistantMessageId = (Date.now() + 1).toString();
            const assistantMessage: Message = {
                id: assistantMessageId,
                role: "assistant",
                content: "",
            };

            setMessages((prev) => [...prev, assistantMessage]);

            try {
                const response = await fetch(chatApiUrl, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        ...body,
                        message: input,
                    }),
                });

                if (!response.ok) throw new Error("Failed to submit chat request");

                const data = await response.json();
                const taskId = data.task_id;

                if (!taskId) throw new Error("No task_id received");

                // Instead of polling, we wait for SSE events.
                // The ChatPage will handle the connection via useSSE
                // or we can handle it here if we pass the right callbacks.
                
                // For simplicity in this refactor, we'll keep the isLoading state
                // and expect the caller to use the SSE updates to fill in the message tokens.

            } catch (error) {
                console.error("Chat Error:", error);
                setMessages((prev) =>
                    prev.map((msg) =>
                        msg.id === assistantMessageId
                            ? { ...msg, content: "Error: Failed to process your request." }
                            : msg
                    )
                );
                setIsLoading(false);
            }
        },
        [input, isLoading, messages, chatApiUrl, baseUrl, body]
    );

    return {
        messages,
        input,
        setInput,
        pendingImages,
        setPendingImages,
        handleInputChange,
        handleSubmit,
        isLoading,
        setMessages,
    };
}
