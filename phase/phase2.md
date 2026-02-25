# Phase 2 — Chat + History: Short-Term Memory

This phase transitions the app from a simple "question-answer" tool to a "conversation" system that understands context over time.

## 🏗️ Architecture Expansion

### 1. The Conversation Store
A database or in-memory cache to store message pairs.
- **Structure**: `(session_id, role, content, timestamp)`.
- **Database**: Often starts with Redis for speed or PostgreSQL for persistence.

### 2. Session Management
The UI must maintain a `session_id` (usually a UUID) to link messages together.
- **Flow**: UI sends `session_id` + `message` → Backend fetches history → Backend sends `history` + `new message` to LLM.

### 3. Token Window Management
LLMs have a finite memory (context window).
- **Problem**: Long conversations exceed the model's limit.
- **Solutions**:
    - **Sliding Window**: Keep only the last N messages.
    - **Summarization**: Ask the LLM to summarize previous messages to save space.

## ✨ New Features
- **Threaded Conversations**: Users can see their previous messages.
- **Continuity**: "What did I just say?" or "Tell me more about that" now works.
- **Streaming UI**: Responses appear word-by-word for a better UX.

## 🚧 Challenges
- **Cost**: Sending history increases the number of tokens per request, raising costs.
- **Latency**: Large histories can slow down response times.
- **Data Integrity**: Ensuring history stays synced across multiple browser tabs.
