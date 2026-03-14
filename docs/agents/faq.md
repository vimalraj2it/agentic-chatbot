# FAQ & RAG Agent

Provides answers based on internal documentation and website content indexed in Pinecone.

## Knowledge Ingestion (Advanced RAG)

1. **Sitemap Discovery**: The system automatically crawls `sitemap.xml` to discover all relevant website URLs.
2. **High-Fidelity Cleaning**: Scraped content is cleaned to remove boilerplate (headers, footers, sidebars), scripts, and advertisements while preserving structural elements like tables and headings.
3. **Chunking & Indexing**: Cleaned text is split into semantic chunks and stored in Pinecone for retrieval.

## Use Case: Retrieval-Augmented Generation (RAG)

1. **Classification**: User query identified as `faq`.
2. **Retrieval**: `search_knowledge_base` tool queries Pinecone for relevant document chunks.
3. **Augmentation**: Context is injected into the `faq_system.jinja2` template with **strict** instructions.
4. **Generation**: LLM provides a response **only** if the answer is present in the context.

## Strict Context & Fallback
If the requested information is not available in the retrieved context, the agent MUST respond with:
> "The requested information is not available in the knowledge base."

## Sample Interaction

**User**: "How do I index a new website?"
**Agent**: (Calls `index_website` tool internally or via Admin)
**Response**: "The website has been queued for indexing. 42 URLs were discovered through the sitemap."
