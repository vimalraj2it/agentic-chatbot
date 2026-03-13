# FAQ & RAG Agent

Provides answers based on internal documentation indexed in Pinecone.

## Use Case: Retrieval-Augmented Generation (RAG)

1. **Classification**: User query identified as `faq`.
2. **Retrieval**: `search_knowledge_base` tool queries Pinecone for relevant document chunks.
3. **Augmentation**: Context is injected into the `faq_messages.jinja2` template.
4. **Generation**: LLM provides a grounded response.

## Sample Request/Response

**Query**: "What is the return policy?"

**Tool Output (Pinecone Context)**:
```text
"All orders can be returned within 30 days of purchase if unused."
```

**LLM Response**:
```json
{
  "answer": "You can return your order within 30 days of purchase, provided the item is unused.",
  "source_documents": ["policy_v1.pdf"],
  "confidence_score": 0.98
}
```
