# Phase 13: Advanced RAG with Sitemap Scraping

## Goal
Enhance the FAQ assistant with automated knowledge ingestion from websites and enforce strict context-based answering.

## Changes
- **Scraping Service**: Implemented `ScrapingService` for automated `sitemap.xml` discovery and URL crawling.
- **Preprocessing**: Added high-fidelity HTML cleaning (boiler-plate removal, structural preservation, normalization).
- **Indexing Pipeline**: Updated `PineconeIndexer` to support bulk URL indexing.
- **Strict Generation**: Updated `faq_system.jinja2` to enforce "context-only" answering and specific fallback messaging.
- **Admin Tool**: Created `index_website` tool for manual triggering of site-wide indexing.

## Files Created/Modified
- `src/services/scraping_service.py`
- `src/rag/index_documents.py`
- `src/templates/prompts/faq_system.jinja2`
- `src/tools/rag_tools.py`
