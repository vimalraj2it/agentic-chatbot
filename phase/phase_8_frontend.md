# Phase 8: Frontend Updates — SSE Streaming & Order Workflow UI

## Objective
Add real-time SSE streaming and order workflow UI components to the Next.js frontend.

---

## 8.1 SSE Client Hook

**File**: `web/src/hooks/useSSE.ts`

```typescript
import { useState, useCallback, useRef } from "react";

interface SSEMessage {
  event: string;
  data: string;
}

export function useSSE(baseUrl: string) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState("");
  const eventSourceRef = useRef<EventSource | null>(null);

  const startStreaming = useCallback(
    (sessionId: string, onComplete?: (fullText: string) => void) => {
      // Close existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      setIsStreaming(true);
      setStreamedText("");
      let accumulated = "";

      const es = new EventSource(`${baseUrl}/api/stream/${sessionId}`);
      eventSourceRef.current = es;

      es.onmessage = (event) => {
        accumulated += event.data;
        setStreamedText(accumulated);
      };

      es.addEventListener("done", (event) => {
        setIsStreaming(false);
        es.close();
        onComplete?.(accumulated || (event as MessageEvent).data);
      });

      es.addEventListener("error", (event) => {
        setIsStreaming(false);
        es.close();
      });

      es.onerror = () => {
        setIsStreaming(false);
        es.close();
      };
    },
    [baseUrl]
  );

  const stopStreaming = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      setIsStreaming(false);
    }
  }, []);

  return { isStreaming, streamedText, startStreaming, stopStreaming };
}
```

---

## 8.2 Chat Message Component with Streaming

**File**: `web/src/components/ChatMessage.tsx`

```tsx
"use client";

import { cn } from "@/lib/utils";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export function ChatMessage({ role, content, isStreaming }: ChatMessageProps) {
  return (
    <div
      className={cn(
        "flex w-full gap-3 p-4",
        role === "user" ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          role === "user"
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-muted-foreground"
        )}
      >
        <div className="whitespace-pre-wrap">{content}</div>
        {isStreaming && (
          <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
        )}
      </div>
    </div>
  );
}
```

---

## 8.3 Order Selection Component

**File**: `web/src/components/OrderSelect.tsx`

```tsx
"use client";

interface Order {
  order_id: string;
  product: string;
}

interface OrderSelectProps {
  orders: Order[];
  onSelect: (orderId: string) => void;
}

export function OrderSelect({ orders, onSelect }: OrderSelectProps) {
  return (
    <div className="space-y-2 mt-2">
      {orders.map((order, idx) => (
        <button
          key={order.order_id}
          onClick={() => onSelect(order.order_id)}
          className="w-full text-left px-4 py-3 rounded-lg border
                     hover:bg-accent hover:border-primary transition-colors
                     flex items-center gap-3"
        >
          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary
                          text-primary-foreground flex items-center
                          justify-center text-xs font-bold">
            {idx + 1}
          </span>
          <span className="font-medium">{order.product}</span>
          <span className="text-muted-foreground text-xs ml-auto">
            {order.order_id}
          </span>
        </button>
      ))}
    </div>
  );
}
```

---

## 8.4 Integration in Chat Page

```tsx
// In the main chat page component:

const { isStreaming, streamedText, startStreaming } = useSSE(
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
);

// After sending a message:
async function handleSend(message: string) {
  // 1. POST to /api/chat
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      user_id: userId,
      message,
    }),
  });

  // 2. Start SSE streaming to get real-time response
  startStreaming(sessionId, (fullText) => {
    // Add complete message to history
    addMessage({ role: "assistant", content: fullText });
  });
}
```

---

## Architecture Notes

- **SSE is primary**, polling `/api/chat/status/{task_id}` is the fallback
- The `useSSE` hook manages connection lifecycle and auto-closes on completion
- `ChatMessage` component renders token-by-token via the streaming cursor animation
- `OrderSelect` renders a clickable list of orders returned by OrderStatusAgent
