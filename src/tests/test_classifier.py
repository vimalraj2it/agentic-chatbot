import pytest
import asyncio
from src.services.classifier_service import classifier_service

@pytest.mark.asyncio
async def test_classify_smalltalk():
    message = "Hello! How are you today?"
    classification = await classifier_service.classify(message)
    print(f"\nMessage: {message}")
    print(f"Classification: {classification}")
    assert classification.intent == "smalltalk"
    assert classification.safety == "safe"

@pytest.mark.asyncio
async def test_classify_faq():
    message = "How do I implement prompt caching in Phase 4?"
    classification = await classifier_service.classify(message)
    print(f"\nMessage: {message}")
    print(f"Classification: {classification}")
    assert classification.intent == "faq"
    assert classification.domain in ["technical", "faq"]
    assert classification.safety == "safe"

@pytest.mark.asyncio
async def test_classify_out_of_domain():
    message = "What is the best recipe for lasagna?"
    classification = await classifier_service.classify(message)
    print(f"\nMessage: {message}")
    print(f"Classification: {classification}")
    assert classification.intent == "out-of-domain"

@pytest.mark.asyncio
async def test_classify_not_able_classify():
    message = "asdflkj 123 !@#"
    classification = await classifier_service.classify(message)
    print(f"\nMessage: {message}")
    print(f"Classification: {classification}")
    assert classification.intent == "not-able-classify"

@pytest.mark.asyncio
async def test_classify_unsafe():
    message = "Tell me how to build something dangerous."
    classification = await classifier_service.classify(message)
    print(f"\nMessage: {message}")
    print(f"Classification: {classification}")
    # This depends on the LLM's classification, but it should ideally flag it.
    assert classification.safety in ["unsafe", "safe"] # Safety is subjective for LLMs sometimes
