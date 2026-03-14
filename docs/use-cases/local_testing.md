# Testing Use-Cases (Local / Minimal Mode)

This guide provides step-by-step instructions on how to test the core AI agents and their corresponding use-cases when running the application **without Docker** (and optionally without Celery/Redis).

> **Note**: Ensure you have started the application according to the [Start without Docker](../setup/startwithoutdocker.md) guide before proceeding.

---

## 1. Smalltalk & General Conversation
**Agent:** `smalltalk_agent`
**Goal:** Verifies the AI's ability to engage in casual conversation while maintaining its persona.

**How to test:**
1. Open the UI (Next.js at `http://localhost:3000` or Streamlit at `http://localhost:8501`).
2. Send a casual greeting:
   * "Hi, how are you today?"
   * "What can you help me with?"
3. **Expected Result:** The AI should respond politely, staying in character as a helpful jewelry or customer service assistant, without triggering any backend database tools.

---

## 2. FAQ & Knowledge Retrieval (RAG)
**Agent:** `faq_agent`
**Goal:** Verifies that the AI can answer policy or product questions strictly using the indexed knowledge base (Pinecone search).

**How to test:**
1. Send a policy-related question:
   * "What is your return policy?"
   * "How long does shipping take?"
2. **Expected Result:** The AI should retrieve relevant excerpts from Pinecone and format an answer based *only* on that context. It should not make up policies.
3. *Fallback Test:* Ask a completely unrelated question like "What is the capital of France?". The AI should respond with a polite fallback message indicating the information isn't in its knowledge base.

---

## 3. Order Status Tracking
**Agent:** `order_status_agent`
**Goal:** Verifies the system's ability to validate an order ID, check ownership (guardrails), and return mock tracking data.

**How to test:**
1. **Direct ID Test:** 
   * "What's the status of order ORD-1001?"
   * **Expected Result:** The AI should immediately fetch the status for `ORD-1001` (shipped/delivered) without asking follow-up questions.
2. **Interactive Selection Test:**
   * Ask vaguely: "Where is my order?"
   * **Expected Result:** The AI should fetch your past orders and present a numbered list.
   * Reply with the number (e.g., "1").
   * **Expected Result:** The AI fetches the status for the selected order.

---

## 4. Creating a Draft Order
**Agent:** `create_order_agent`
**Goal:** Verifies complex information extraction (Product, Quantity, Address) and confirmation workflows.

**How to test:**
1. Start the workflow:
   * "I want to buy 2 Gold Necklaces and ship them to 123 Main St, New York."
2. **Expected Result:** The AI should extract all three pieces of information, generate a draft order summary, and ask for your confirmation (Yes/No).
3. **Missing Info Test:**
   * "I want to buy a Diamond Ring."
   * **Expected Result:** The AI should detect missing info and ask: "How many would you like, and what is the shipping address?"
4. Confirm the order:
   * Reply "Yes" to the final summary.
   * **Expected Result:** The AI confirms the order is placed and returns a mock confirmation ID.

---

## 5. Workflow Interruption & Journey Resumption
**Goal:** Verifies the `ConversationStateManager` handles tracking state when the user drastically changes topics mid-flow.

**How to test:**
1. Ask vaguely: "Where is my order?" (AI asks you to pick from a list).
2. **Interrupt:** Instead of picking a number, ask: "Wait, what is your return policy?" (Triggers FAQ).
3. **Expected Result:** 
   * The AI answers the return policy question.
   * Immediately below the answer, it appends a message like: *🔄 Continuing your previous request... Please select an order:* (Restores the interactive list).
4. Reply "1" to see if it correctly finishes the original order status request.
