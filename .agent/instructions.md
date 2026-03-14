# 🤖 Instructions for AI Agents (Antigravity)
> [!IMPORTANT]
> This file contains the MANDATORY coding standards for this project. 
> **Antigravity** and other AI assistants MUST read this file at the start of any planning phase to ensure architectural consistency.

# Project Coding Standards & Architecture

This document serves as the "Source of Truth" for coding standards, architectural patterns, and development workflows in this project. It is intended for both AI coding assistants and human developers.

## 🚀 Tech Stack Overview

- **Backend**: Python 3.10+, FastAPI, LangGraph, LiteLLM, Celery, Redis, Motor (MongoDB).
- **Frontend**: Next.js 15, React 19, Tailwind CSS, Lucide Icons.
- **Infrastructure**: Docker, Docker Compose.

---

## 🛠️ Backend Standards (Python/FastAPI)

### 1. Asynchronous Architecture
- **FastAPI**: Use asynchronous endpoints (`async def`) for all I/O bound operations.
- **Celery**: Long-running or heavy processing tasks (like LLM calls) MUST be handled asynchronously via Celery workers.
- **Database**: Use `Motor` for asynchronous MongoDB interactions.

### 2. Agentic Workflows (LangGraph)
- **State Management**: Define a `TypedDict` for the `AgentState`.
- **Node-Based Design**: Break down logic into discrete nodes (e.g., `load_memory`, `inject_context`, `call_llm`).
- **Graph Visualization**: High-level graph flow should be automatically generated and saved in the `graph/` directory.

### 3. Prompt Engineering (PromptService)
- **Modular Prompts**: Use Jinja2 templates for prompts located in `src/templates/prompts/`.
- **System Prompts**: We follow a "Split System Prompt" pattern where the system prompt is divided into:
    - `role_rules.jinja2`: Role definition and core rules.
    - `user_profile.jinja2`: User context and profile info.
    - `guardrails_format.jinja2`: Safety instructions and output formatting.
    - `reference_document.jinja2`: RAG or document-specific context.
- **Prompt Caching**: Enable caching for expensive prompts using the `ENABLE_PROMPT_CACHING` setting.

### 4. Code Style & Logging
- **Type Hinting**: Use Python type hints for all function signatures and complex variables.
- **Logging**: Use the centralized `src.core.logging_config` for all loggers. Always include `session_id` or `user_id` in logs for traceability.
- **Execution Tracing**: Use the `@log_execution` decorator from `src.core.logging_config` for all key methods (nodes, tools, services). This ensures consistent logging of method entry/exit with input arguments and return values.

---

## 🎨 Frontend Standards (Next.js/React)

### 1. Modern React
- **React 19**: Leverage the latest React features and hooks.
- **Next.js 15 (App Router)**: Use the App Router for routing. Use Client Components (`"use client"`) only when necessary for interactivity.

### 2. UI/UX & Styling
- **Tailwind CSS**: Use utility classes for styling. Avoid inline styles.
- **Framer Motion**: Use Framer Motion for smooth transitions and complex animations.
- **Lucide-React**: Standard icon library for the project.

---

## 🏗️ Project Structure

```bash
├── src/
│   ├── api/          # FastAPI Routers
│   ├── core/         # Core config, logging, telemetry
│   ├── models/        # Pydantic/Database schemas
│   ├── services/      # Business logic, Graph, LLM services
│   ├── templates/     # Modular Jinja2 prompts
├── web/               # Next.js Frontend
├── docs/              # Project documentation
├── graph/             # Generated workflow visualizations
```

---

## ✅ Best Practices
- **Package Management**: ALWAYS use `uv` instead of `pip` for package management and virtual environments (e.g., `uv pip install`, `uv run`). Do not use `pip`.
- **Small Commits**: Make atomic commits that focus on a single feature or fix.
- **Validation**: Always verify changes by running existing tests (e.g., `uv run python src/tests/test_split_prompts.py`).
- **Environment Variables**: Never hardcode secrets. Use `.env` or `.docker.env` managed via `pydantic-settings`.
