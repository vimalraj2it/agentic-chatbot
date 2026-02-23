import React from "react";
import { Send, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSubmit: (e: React.FormEvent) => void;
    isLoading: boolean;
    placeholder?: string;
}

export const ChatInput = ({ value, onChange, onSubmit, isLoading, placeholder }: ChatInputProps) => {
    return (
        <form onSubmit={onSubmit} className="relative flex items-center w-full">
            <input
                type="text"
                value={value}
                onChange={onChange}
                placeholder={placeholder || "Type a message..."}
                disabled={isLoading}
                className={cn(
                    "w-full bg-background border border-input rounded-xl px-4 py-3 pr-12 text-sm",
                    "focus:outline-none focus:ring-1 focus:ring-ring focus:border-input",
                    "disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                )}
            />
            <button
                type="submit"
                disabled={isLoading || !value.trim()}
                className={cn(
                    "absolute right-2 p-2 rounded-lg transition-colors",
                    "bg-primary text-primary-foreground hover:bg-primary/90",
                    "disabled:opacity-50 disabled:bg-muted disabled:text-muted-foreground"
                )}
            >
                {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                    <Send className="h-4 w-4" />
                )}
            </button>
        </form>
    );
};
