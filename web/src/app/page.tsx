"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function RootPage() {
    const router = useRouter();

    useEffect(() => {
        const user = localStorage.getItem("chat_user");
        if (user) {
            router.push("/sessions");
        } else {
            router.push("/login");
        }
    }, []);

    return <div className="flex h-screen items-center justify-center bg-background">Redirecting...</div>;
}
