# Phase 6: RAG Enhancement — Pinecone Integration

## Objective
Full Pinecone vector DB integration: document indexing pipeline + search retrieval in the FAQ agent.

---

## 6.1 Document Indexing Pipeline

**File**: `src/rag/index_documents.py`

```python
"""
Standalone script to chunk documents, create embeddings,
and upsert into Pinecone.

Usage:
    python -m src.rag.index_documents --input-dir ./docs
"""

import os
import argparse
from typing import List, Dict
from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from sentence_transformers import SentenceTransformer
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

INDEX_NAME = "wechat-assistant-kb"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def load_documents(input_dir: str):
    """Load all PDFs and text files from a directory."""
    loader = DirectoryLoader(
        input_dir,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True,
    )
    return loader.load()


def chunk_documents(documents) -> List[Dict]:
    """Split documents into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
    return chunks


def create_embeddings(chunks, model_name: str = None):
    """Generate embeddings for each chunk."""
    model_name = model_name or settings.EMBEDDING_MODEL
    model = SentenceTransformer(model_name, device=settings.EMBEDDING_DEVICE)

    texts = [chunk.page_content for chunk in chunks]
    embeddings = model.encode(
        texts, normalize_embeddings=settings.EMBEDDING_NORMALIZE
    )
    logger.info(f"Generated embeddings: shape={embeddings.shape}")
    return embeddings


def upsert_to_pinecone(chunks, embeddings):
    """Upsert vectors into Pinecone index."""
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)

    # Create index if it doesn't exist
    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            dimension=embeddings.shape[1],
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.PINECONE_CLOUD,
                region=settings.PINECODE_REGION,
            ),
        )

    index = pc.Index(INDEX_NAME)

    # Batch upsert
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_embeddings = embeddings[i : i + batch_size]

        vectors = []
        for j, (chunk, emb) in enumerate(zip(batch_chunks, batch_embeddings)):
            vectors.append({
                "id": f"chunk_{i + j}",
                "values": emb.tolist(),
                "metadata": {
                    "content": chunk.page_content,
                    "filename": chunk.metadata.get("source", "unknown"),
                    "page": chunk.metadata.get("page", 0),
                },
            })
        index.upsert(vectors=vectors)
        logger.info(f"Upserted batch {i // batch_size + 1}")

    logger.info(f"Indexing complete: {len(chunks)} vectors in '{INDEX_NAME}'")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    args = parser.parse_args()

    docs = load_documents(args.input_dir)
    chunks = chunk_documents(docs)
    embeddings = create_embeddings(chunks)
    upsert_to_pinecone(chunks, embeddings)


if __name__ == "__main__":
    main()
```

---

## 6.2 Pinecone Search in RAG Node

**File**: `src/nodes/rag_nodes.py` — update `reference_docs_pinecone_node`

```python
async def reference_docs_pinecone_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves reference documents from Pinecone."""
    logger.info(f"Node: reference_docs_pinecone_node - User: {state['user_id']}")

    query = state["user_message"]
    if state.get("expanded_queries"):
        query = state["expanded_queries"][0]["query"]

    # ── Embed query ────────────────────────────────────────────
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(
        settings.EMBEDDING_MODEL, device=settings.EMBEDDING_DEVICE
    )
    query_embedding = model.encode(
        [query], normalize_embeddings=settings.EMBEDDING_NORMALIZE
    )[0].tolist()

    # ── Query Pinecone ─────────────────────────────────────────
    from pinecone import Pinecone
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    index = pc.Index("wechat-assistant-kb")

    results = index.query(
        vector=query_embedding, top_k=5, include_metadata=True
    )

    pinecone_context = ""
    if results.matches:
        pinecone_context = "\n\n".join([
            f"--- {m.metadata.get('filename', 'doc')} "
            f"(score: {m.score:.4f}) ---\n{m.metadata.get('content', '')}"
            for m in results.matches
        ])
        logger.info(f"Retrieved {len(results.matches)} snippets from Pinecone")

    # ── Build full context ─────────────────────────────────────
    context = await memory_service.get_user_context(state["user_id"])
    context_parts = context_builder.build_context_dict(
        user_info=context["user_info"],
        memory=context["memory"],
        app_state=state.get("app_state"),
        referenced_data=state.get("referenced_data"),
        files=state.get("files"),
    )
    reference_docs = prompt_service.render_template(
        "reference_document.jinja2", **context_parts
    )

    if pinecone_context:
        reference_docs = f"{pinecone_context}\n\n# GENERAL CONTEXT\n{reference_docs}"

    return {"reference_docs": reference_docs}
```

---

## Dependencies

Add to `pyproject.toml`:
```toml
"pinecone-client>=5.1.0",
```
