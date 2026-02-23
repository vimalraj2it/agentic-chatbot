import React from "react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import { MessageContent } from "@/hooks/use-chatbot";

interface ChatMessageProps {
    role: "user" | "assistant" | "system";
    content: MessageContent;
}

export const ChatMessage = ({ role, content }: ChatMessageProps) => {
    const isUser = role === "user";

    // Extract text and images from diverse content formats 
    const textContent = typeof content === "string"
        ? content
        : content.find(c => c.type === "text")?.text || "";

    const images = typeof content === "object" && Array.isArray(content)
        ? content.filter(c => c.type === "image_url").map(c => c.image_url?.url)
        : [];

    return (
        <div
            className={cn(
                "flex w-full mb-4",
                isUser ? "justify-end" : "justify-start"
            )}
        >
            <div
                className={cn(
                    "max-w-[85%] px-4 py-2 rounded-2xl text-sm shadow-sm",
                    isUser
                        ? "bg-primary text-primary-foreground rounded-tr-none"
                        : "bg-card text-card-foreground rounded-tl-none border border-border"
                )}
            >
                {images.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-2 mt-1">
                        {images.map((url, i) => url && (
                            <img
                                key={i}
                                src={url}
                                alt="Shared"
                                className="max-h-60 rounded-lg border border-border/50 object-contain bg-muted/50"
                            />
                        ))}
                    </div>
                )}
                {textContent && (
                    <div className="prose prose-sm dark:prose-invert break-words text-inherit max-w-none">
                        <ReactMarkdown>
                            {textContent}
                        </ReactMarkdown>
                    </div>
                )}
            </div>
        </div>
    );
};
