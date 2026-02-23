"use client";

import { useState, useCallback } from "react";

export type Message = {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
};

interface UseChatbotOptions {
    api?: string;
    body?: Record<string, any>;
    initialMessages?: Message[];
}

export function useChatbot({
    api = "/api/chat",
    body = {},
    initialMessages = [],
}: UseChatbotOptions = {}) {
    const [messages, setMessages] = useState<Message[]>(initialMessages);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    // If session_id changes, we could fetch history here if we wanted to 
    // keep logic in the hook, but for now we'll handle it in the Page component 
    // to match the "ChatPage" fetch requirement.

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setInput(e.target.value);
    };

    const handleSubmit = useCallback(
        async (e?: React.FormEvent) => {
            e?.preventDefault();
            if (!input.trim() || isLoading) return;

            const userMessage: Message = {
                id: Date.now().toString(),
                role: "user",
                content: input,
            };

            setMessages((prev) => [...prev, userMessage]);
            setInput("");
            setIsLoading(true);

            const assistantMessageId = (Date.now() + 1).toString();
            const assistantMessage: Message = {
                id: assistantMessageId,
                role: "assistant",
                content: "",
            };

            setMessages((prev) => [...prev, assistantMessage]);

            try {
                const response = await fetch(api, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        ...body,
                        messages: [...messages, userMessage],
                    }),
                });

                if (!response.ok) throw new Error("Failed to fetch");

                const contentType = response.headers.get("Content-Type");

                if (contentType?.includes("application/json")) {
                    const data = await response.json();
                    setMessages((prev) =>
                        prev.map((msg) => {
                            if (msg.id === userMessage.id) return { ...msg, id: data.user_id };
                            if (msg.id === assistantMessageId) return { ...msg, id: data.assistant_id, content: data.response };
                            return msg;
                        })
                    );
                } else {
                    const reader = response.body?.getReader();
                    if (!reader) throw new Error("No reader");

                    const decoder = new TextDecoder();
                    let fullContent = "";

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        const chunk = decoder.decode(value, { stream: true });
                        const lines = chunk.split("\n");

                        for (const line of lines) {
                            if (line.startsWith("data: ")) {
                                const dataStr = line.slice(6);
                                if (dataStr === "[DONE]") continue;
                                try {
                                    const data = JSON.parse(dataStr);
                                    if (data.chunk) {
                                        fullContent += data.chunk;
                                        setMessages((prev) =>
                                            prev.map((msg) =>
                                                msg.id === assistantMessageId
                                                    ? { ...msg, content: fullContent }
                                                    : msg
                                            )
                                        );
                                    } else if (data.user_id && data.assistant_id) {
                                        // Update IDs from metadata
                                        setMessages((prev) =>
                                            prev.map((msg) => {
                                                if (msg.id === userMessage.id) return { ...msg, id: data.user_id };
                                                if (msg.id === assistantMessageId) return { ...msg, id: data.assistant_id };
                                                return msg;
                                            })
                                        );
                                    }
                                } catch (e) {
                                    // Handle non-JSON chunks if any
                                }
                            }
                        }
                    }
                }
            } catch (error) {
                console.error("Chat Error:", error);
            } finally {
                setIsLoading(false);
            }
        },
        [input, isLoading, messages, api, body]
    );

    return {
        messages,
        input,
        setInput,
        handleInputChange,
        handleSubmit,
        isLoading,
        setMessages,
    };
}
