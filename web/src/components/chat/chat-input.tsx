import React, { useRef } from "react";
import { Send, Loader2, Image as ImageIcon, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSubmit: (e: React.FormEvent) => void;
    isLoading: boolean;
    placeholder?: string;
    pendingImages?: string[];
    onImageAdd?: (base64: string) => void;
    onImageRemove?: (index: number) => void;
}

export const ChatInput = ({
    value,
    onChange,
    onSubmit,
    isLoading,
    placeholder,
    pendingImages = [],
    onImageAdd,
    onImageRemove
}: ChatInputProps) => {
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file && onImageAdd) {
            const reader = new FileReader();
            reader.onloadend = () => {
                onImageAdd(reader.result as string);
            };
            reader.readAsDataURL(file);
        }
        if (fileInputRef.current) fileInputRef.current.value = "";
    };

    return (
        <div className="w-full space-y-4">
            {pendingImages.length > 0 && (
                <div className="flex flex-wrap gap-2 px-1">
                    {pendingImages.map((img, i) => (
                        <div key={i} className="relative group animate-in fade-in zoom-in duration-200">
                            <img
                                src={img}
                                alt="Preview"
                                className="h-20 w-20 object-cover rounded-lg border border-border shadow-sm"
                            />
                            <button
                                onClick={() => onImageRemove?.(i)}
                                className="absolute -top-1.5 -right-1.5 p-1 bg-destructive text-destructive-foreground rounded-full shadow-md opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                                <X className="h-3 w-3" />
                            </button>
                        </div>
                    ))}
                </div>
            )}
            <form onSubmit={onSubmit} className="relative flex items-center w-full gap-2">
                <div className="relative flex-1 flex items-center">
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
                    <div className="absolute right-2 flex items-center gap-1">
                        <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={isLoading}
                            className="p-2 text-muted-foreground hover:text-primary transition-colors disabled:opacity-50"
                        >
                            <ImageIcon className="h-4 w-4" />
                        </button>
                        <input
                            type="file"
                            ref={fileInputRef}
                            className="hidden"
                            accept="image/*"
                            onChange={handleFileChange}
                        />
                    </div>
                </div>
                <button
                    type="submit"
                    disabled={isLoading || (!value.trim() && pendingImages.length === 0)}
                    className={cn(
                        "p-3 rounded-xl transition-colors shrink-0",
                        "bg-primary text-primary-foreground hover:bg-primary/90",
                        "disabled:opacity-50 disabled:bg-muted disabled:text-muted-foreground shadow-sm"
                    )}
                >
                    {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                        <Send className="h-4 w-4" />
                    )}
                </button>
            </form>
        </div>
    );
};
