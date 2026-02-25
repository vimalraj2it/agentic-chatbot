"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, Upload, RefreshCw, XCircle, Trash2, CheckCircle, AlertCircle, Loader2, ArrowLeft } from "lucide-react";
import { apiClient } from "@/lib/api-client";

export default function DocumentsPage() {
    const [documents, setDocuments] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isUploading, setIsUploading] = useState(false);
    const router = useRouter();

    useEffect(() => {
        fetchDocuments();
    }, []);

    const fetchDocuments = async () => {
        try {
            const data = await apiClient.listDocuments();
            setDocuments(data.documents);
        } catch (error) {
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        try {
            await apiClient.uploadDocument(file);
            fetchDocuments();
        } catch (error) {
            console.error(error);
            alert("Upload failed");
        } finally {
            setIsUploading(false);
        }
    };

    const handleAction = async (docId: string, action: 'load' | 'unload' | 'reload' | 'delete') => {
        try {
            if (action === 'load') await apiClient.loadDocument(docId);
            else if (action === 'unload') await apiClient.unloadDocument(docId);
            else if (action === 'reload') await apiClient.reloadDocument(docId);
            else if (action === 'delete') {
                if (!confirm("Are you sure you want to delete this document?")) return;
                await apiClient.deleteDocument(docId);
            }
            fetchDocuments();
        } catch (error) {
            console.error(error);
            alert(`${action} failed`);
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "loaded": return <CheckCircle size={16} className="text-green-500" />;
            case "loading": return <Loader2 size={16} className="text-blue-500 animate-spin" />;
            case "error": return <AlertCircle size={16} className="text-red-500" />;
            default: return <RefreshCw size={16} className="text-muted-foreground" />;
        }
    };

    if (isLoading) return <div className="flex h-screen items-center justify-center bg-background">Loading documents...</div>;

    return (
        <div className="flex flex-col min-h-screen bg-background text-foreground">
            <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-xl">
                <div className="flex items-center gap-4">
                    <button onClick={() => router.push("/sessions")} className="p-2 hover:bg-muted rounded-lg text-muted-foreground transition-all">
                        <ArrowLeft size={20} />
                    </button>
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-secondary text-secondary-foreground flex items-center justify-center shadow-lg">
                            <FileText size={22} />
                        </div>
                        <h1 className="text-lg font-bold">Reference Documents</h1>
                    </div>
                </div>
                <div className="relative">
                    <input
                        type="file"
                        id="file-upload"
                        className="hidden"
                        accept=".pdf"
                        onChange={handleFileUpload}
                        disabled={isUploading}
                    />
                    <label
                        htmlFor="file-upload"
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg cursor-pointer transition-all ${isUploading ? 'bg-muted text-muted-foreground' : 'bg-primary text-primary-foreground hover:opacity-90'
                            }`}
                    >
                        {isUploading ? <Loader2 size={18} className="animate-spin" /> : <Upload size={18} />}
                        <span className="text-sm font-medium">{isUploading ? "Uploading..." : "Upload PDF"}</span>
                    </label>
                </div>
            </header>

            <main className="flex-1 p-4 md:p-8 max-w-5xl mx-auto w-full">
                <div className="bg-card rounded-2xl border border-border overflow-hidden">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-muted/50 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                <th className="px-6 py-4">Filename</th>
                                <th className="px-6 py-4">Status</th>
                                <th className="px-6 py-4">Last Updated</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {documents.length === 0 ? (
                                <tr>
                                    <td colSpan={4} className="px-6 py-12 text-center text-muted-foreground">
                                        No documents found. Upload a PDF to get started.
                                    </td>
                                </tr>
                            ) : documents.map((doc) => (
                                <tr key={doc.id} className="hover:bg-muted/30 transition-colors group">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded bg-primary/5 text-primary flex items-center justify-center">
                                                <FileText size={16} />
                                            </div>
                                            <span className="font-medium text-sm">{doc.filename}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2 text-xs">
                                            {getStatusIcon(doc.status)}
                                            <span className="capitalize">{doc.status}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-xs text-muted-foreground">
                                        {new Date(doc.updated_at).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex items-center justify-end gap-1 opacity-100 md:opacity-0 group-hover:opacity-100 transition-opacity">
                                            {doc.status === "loaded" ? (
                                                <>
                                                    <button onClick={() => handleAction(doc.id, 'unload')} title="Unload from Index" className="p-2 hover:bg-yellow-500/10 text-yellow-500 rounded-lg">
                                                        <XCircle size={18} />
                                                    </button>
                                                    <button onClick={() => handleAction(doc.id, 'reload')} title="Reload Index" className="p-2 hover:bg-blue-500/10 text-blue-500 rounded-lg">
                                                        <RefreshCw size={18} />
                                                    </button>
                                                </>
                                            ) : (
                                                <button onClick={() => handleAction(doc.id, 'load')} title="Load into Index" className="p-2 hover:bg-green-500/10 text-green-500 rounded-lg" disabled={doc.status === "loading"}>
                                                    <Upload size={18} />
                                                </button>
                                            )}
                                            <button onClick={() => handleAction(doc.id, 'delete')} title="Delete Document" className="p-2 hover:bg-red-500/10 text-red-500 rounded-lg">
                                                <Trash2 size={18} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </main>
        </div>
    );
}
