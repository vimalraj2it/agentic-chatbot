# Phase 3 — UI / App Context Injection: The "Copilot" Era

This is the bridge between a generic chatbot and a specialized AI agent that knows your business data and current app state.

## 🚀 The Context Builder Layer
Instead of just sending chat history, the backend now "gathers" information before calling the LLM.

### 1. Document Injection (RAG)
Retrieval-Augmented Generation basics.
- **Input**: PDF, CSV, or Text files uploaded by the user.
- **Process**: Parse text → Chunking → Embeddings → Semantic Search.

### 2. Application State
Injecting what the user is currently looking at.
- **User Profile**: "I am a developer with 5 years experience."
- **Current View**: "I am currently on the 'Settings' page."
- **Database Rows**: Injecting specific records related to the user's query.

## 🛠️ Technical Workflow
1. **Trigger**: User asks "How do I fix this error?"
2. **Context Retrieval**: System pulls logs from the DB and recent code changes.
3. **Augmentation**: The prompt becomes: *"Here are the logs [logs] and code [code]. Based on this, what is the error?"*
4. **Execution**: LLM provides a highly relevant, context-aware answer.

## 🎨 UI Enhancements
- **File Uploaders**: Drag-and-drop support for documents.
- **Source Citations**: UI shows *where* the AI got the information from.
- **Context Toggles**: Let users choose what "data" the AI is allowed to see.

> [!TIP]
> This phase is where the AI starts providing high value by solving specific problems rather than just chatting.
