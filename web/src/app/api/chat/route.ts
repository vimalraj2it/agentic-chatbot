
export async function POST(req: Request) {
    const { messages, session_id } = await req.json();
    const lastMessage = messages[messages.length - 1];

    // Use internal docker networking if available, fallback to localhost for development
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

    // We use the Python backend as the underlying source
    const response = await fetch(`${backendUrl}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            session_id: session_id || `sess_next_${Math.random().toString(36).substr(2, 9)}`,
            message: lastMessage.content
        }),
    });

    if (!response.ok) {
        return new Response("Failed to connect to backend", { status: 500 });
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    // Create a simple text stream to send chunks directly to the frontend hook
    const stream = new ReadableStream({
        async start(controller) {
            if (!reader) {
                controller.close();
                return;
            }

            try {
                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split("\n");

                    for (const line of lines) {
                        if (line.startsWith("data: ")) {
                            const dataStr = line.replace("data: ", "").trim();
                            if (dataStr === "[DONE]") break;

                            try {
                                const data = JSON.parse(dataStr);
                                if (data.chunk) {
                                    controller.enqueue(new TextEncoder().encode(data.chunk));
                                }
                            } catch (e) {
                                console.error("Error parsing chunk", e);
                            }
                        }
                    }
                }
            } catch (e) {
                controller.error(e);
            } finally {
                controller.close();
            }
        }
    });

    return new Response(stream, {
        headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
}
