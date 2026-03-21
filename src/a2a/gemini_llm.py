from python_a2a import run_server
from python_a2a.langchain import to_a2a_server
from langchain_google_genai import ChatGoogleGenerativeAI
import threading
import sys
import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# Create a Gemini LLM via LangChain
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

# Convert LLM to A2A server
llm_server = to_a2a_server(llm)

def main():
    llm_thread = threading.Thread(
        target=lambda: run_server(llm_server, port=5001),
        daemon=True
    )
    llm_thread.start()
    try:
        print("Gemini LLM A2A server running on port 5001. Press Ctrl+C to stop.")
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\nStopping server...")
        sys.exit(0)

if __name__ == "__main__":
    main()
