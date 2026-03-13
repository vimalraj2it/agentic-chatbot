# Phase 5: Redis SSE Streaming & Celery Integration

## Overview
Phase 5 implements real-time response delivery for the multi-agent assistant. By leveraging Redis Pub/Sub, we disconnect the long-running Celery worker from the synchronous HTTP request-response cycle, allowing for smooth token-by-token streaming on the frontend.

## Components

### 1. RedisStreamService (`src/services/redis_stream.py`)
- **Role**: The message broker interface.
- **Functionality**: 
  - `publish_token`: Sends individual LLM tokens to a session-specific Redis channel.
  - `publish_status`: Sends lifecycle events (`processing`, `completed`, `error`).
  - `subscribe`: An async generator that the SSE endpoint uses to listen for updates.

### 2. SSE Endpoint (`src/api/chat.py`)
- **Route**: `GET /api/stream/{session_id}`
- **Implementation**: Uses `sse-starlette` to maintain an open HTTP connection. It pipes messages from the `RedisStreamService.subscribe` generator directly to the client.

### 3. Celery Task Updates (`src/services/tasks.py`)
- **Logic**: The `process_chat_task` now uses `graph.astream` instead of `ainvoke`.
- **Streaming**: As the graph processes, partial responses are detected and published to Redis, ensuring the user sees progress immediately.

## Architecture Flow
1. **Frontend** POSTs to `/api/chat`.
2. **FastAPI** returns a `task_id` and starts listening on `/api/stream/{session_id}`.
3. **Celery Worker** picks up the job.
4. **LangGraph** begins execution.
5. **Worker** publishes tokens to Redis as they arrive.
6. **FastAPI SSE** picks up tokens from Redis and sends them to the browser.
7. **Worker** finished and publishes a `completed` status.
