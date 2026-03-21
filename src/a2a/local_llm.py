from python_a2a import A2AClient, run_server
from python_a2a.langchain import to_a2a_server
from langchain_ollama.llms import OllamaLLM
import os
# Create a LangChain LLM
#llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
llm = OllamaLLM(model="llama3.2:latest")
# Convert LLM to A2A server
llm_server = to_a2a_server(llm)
# Run LLM agent server in background threads
import threading
import signal
import sys
def main():
    llm_thread = threading.Thread(
        target=lambda: run_server(llm_server, port=5001),
        daemon=True
    )
    llm_thread.start()
    # Wait here until Ctrl+C
    try:
        print("Servers are running. Press Ctrl+C to stop.")
        threading.Event().wait()  # Block main thread (cross-platform)
    except KeyboardInterrupt:
        print("\nStopping servers...")
        sys.exit(0)
if __name__ == "__main__":
    main()
