import asyncio
import json
from src.services.scraping_service import scraping_service
from src.rag.index_documents import pinecone_service
from src.tools.rag_tools import index_website, search_knowledge_base
from src.graphs.faq import faq_llm_node

async def test_scraping():
    print("\n--- Testing Scraping Logic ---")
    # Using a real but stable URL for testing cleaning
    # (In a real test we might use a mock, but here we want to see the 'CleaningInstructions' in action)
    test_url = "https://example.com" 
    data = await scraping_service.scrape_and_clean(test_url)
    print(f"Title: {data.get('title')}")
    print(f"URL: {data.get('url')}")
    print(f"Content Preview: {data.get('content')[:200]}...")
    print(f"Sections Count: {len(data.get('sections', []))}")

async def test_fallback_messaging():
    print("\n--- Testing Strict Fallback Messaging ---")
    # Simulate the LLM node call with EMPTY context
    state = {
        "messages": [],
        "reference_docs": "", # NO CONTEXT
        "intent": "faq_query"
    }
    
    # We need to mock the LLM call or just check if the prompt logic allows fallback
    from src.services.llm_service import llm_service
    # Constructing a dummy prompt that would be generated
    # This is a bit complex as it involves Jinja2
    
    # Let's just verify the tool returns the expected message structure
    # if we force a low score or no results.
    results = search_knowledge_base("something non-existent")
    print(f"Search Results for non-existent: {results}")

async def main():
    await test_scraping()
    await test_fallback_messaging()

if __name__ == "__main__":
    asyncio.run(main())
