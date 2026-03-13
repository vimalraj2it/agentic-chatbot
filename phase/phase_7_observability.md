# Phase 7: LangSmith & Observability

## Objective
Enable full tracing of agent runs, tool calls, latency, and errors via LangSmith.

---

## 7.1 Environment Configuration

**File**: `.env` — additions

```env
# LangSmith Tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=wechat-assistant
LANGCHAIN_API_KEY=YOUR_LANGCHAIN_API_KEY_HERE
```

**File**: `src/core/config.py` — additions

```python
# In class Settings:
LANGCHAIN_TRACING_V2: str = "false"
LANGCHAIN_PROJECT: str = "wechat-assistant"
LANGCHAIN_API_KEY: str = ""
```

---

## 7.2 Tracing Initialization

**File**: `src/main.py` — additions inside `lifespan`

```python
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── LangSmith setup ────────────────────────────────────────
    if settings.LANGCHAIN_TRACING_V2 == "true":
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
        print(f"LangSmith tracing enabled for project: {settings.LANGCHAIN_PROJECT}")

    # ... existing startup code ...
    await db.connect_to_storage()
    # ...
    yield
    await db.close_storage()
```

---

## 7.3 What Gets Traced

Once `LANGCHAIN_TRACING_V2=true`, LangChain and LangGraph automatically trace:

| Component | Traced |
|---|---|
| LangGraph `.ainvoke()` | ✅ Full run with node-by-node timing |
| `get_chat_completion()` (via litellm) | ✅ LLM call input/output/latency |
| Tool calls (list_orders, etc.) | ✅ If called through LangChain tool wrappers |
| Node exceptions | ✅ Error stack traces |
| Token usage | ✅ Prompt/completion token counts |

---

## 7.4 Dashboard Access

Once deployed with a valid API key:
- **URL**: https://smith.langchain.com
- **Project name**: `wechat-assistant`
- Traces appear within seconds of each chat request
