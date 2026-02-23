import React from "react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";

interface ChatMessageProps {
    role: "user" | "assistant" | "system";
    content: string;
}

export const ChatMessage = ({ role, content }: ChatMessageProps) => {
    const isUser = role === "user";

    return (
        <div
            className={cn(
                "flex w-full mb-4",
                isUser ? "justify-end" : "justify-start"
            )}
        >
            <div
                className={cn(
                    "max-w-[80%] px-4 py-2 rounded-lg text-sm",
                    isUser
                        ? "bg-primary text-primary-foreground rounded-tr-none"
                        : "bg-muted text-muted-foreground rounded-tl-none border border-border"
                )}
            >
                <div className="prose prose-sm dark:prose-invert break-words text-inherit">
                    <ReactMarkdown>
                        {content}
                    </ReactMarkdown>
                </div>
            </div>
        </div>
    );
};
