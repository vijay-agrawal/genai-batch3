from google.adk import Agent
from google.adk.tools import google_search  # The Google Search tool

import sys
import os
from pathlib import Path
sys.path.append("..")

from dotenv import load_dotenv
import google.auth
import vertexai

# ============================================================================
# Helper Function: Find Project Root
# ============================================================================
def _find_project_root() -> Path:
    """Find project root by looking for .env or service account key."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".env").exists() or (current / "google-vertexai-serviceaccount-key.json").exists():
            return current
        current = current.parent
    print("ERROR: Could not find .env or google-vertexai-serviceaccount-key.json in any parent directory.")
    print(f"Started searching from: {Path(__file__).resolve().parent}")
    exit(1)

# --- Setup Google Vertex AI Authentication ---
print("\n[AGENT] Setting up Google authentication...")
PROJECT_ROOT = _find_project_root()
load_dotenv(PROJECT_ROOT / ".env")

# Resolve relative credential paths to absolute
_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if _creds_path and not Path(_creds_path).is_absolute():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str((PROJECT_ROOT / _creds_path).resolve())

_resolved_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
print(f"✓ Credentials: {_resolved_creds}")

# Verify credentials file exists
if _resolved_creds and not Path(_resolved_creds).exists():
    print(f"✗ ERROR: Credentials file not found at {_resolved_creds}")
    exit(1)
elif _resolved_creds:
    print(f"✓ Credentials file exists")
    try:
        import json
        with open(_resolved_creds, 'r') as f:
            creds_json = json.load(f)
            if "type" in creds_json and creds_json["type"] == "service_account":
                print(f"✓ Valid service account key")
                print(f"  Email: {creds_json.get('client_email', 'Unknown')}")
    except Exception as e:
        print(f"✗ ERROR: Invalid credentials file: {e}")
        exit(1)

# Set Project Details
PROJECT_ID = os.getenv("GOOGLE_VERTEXAI_PROJECT_ID", "your-gcp-project-id")
LOCATION = os.getenv("GOOGLE_VERTEXAI_LOCATION", "us-central1")

# Initialize Vertex AI
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print(f"✓ Vertex AI initialized: {PROJECT_ID}")
except Exception as e:
    print(f"✗ Error initializing Vertex AI: {e}")
    exit(1)

from callback_logging import log_query_to_model, log_model_response


root_agent = Agent(
    # name: A unique name for the agent.
    name="google_search_agent",
    # description: A short description of the agent's purpose, so
    # other agents in a multi-agent system know when to call it.
    description="Answer questions using Google Search.",
    # model: The LLM model that the agent will use:
    model="gemini-2.5-flash",
    # instruction: Instructions (or the prompt) for the agent.
    instruction="You are an expert researcher. You stick to the facts.",
    # callbacks: Allow for you to run functions at certain points in
    # the agent's execution cycle. In this example, you will log the
    # request to the agent and its response.
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    # tools: functions to enhance the model's capabilities.
    tools=[google_search],
)

# ============================================================================
# Agent Entry Point - Process user queries
# ============================================================================
def process_query(query: str) -> str:
    """
    Process a user query using the agent.
    
    Args:
        query: The user's question or search query
        
    Returns:
        The agent's response
    """
    try:
        print(f"\n[AGENT] Processing query: {query}")
        
        # Run the agent with the user's query
        response = root_agent.run(query)
        
        print(f"[AGENT] Response generated successfully")
        return response
        
    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        print(f"[AGENT] {error_msg}")
        return error_msg


# For testing locally
if __name__ == "__main__":
    test_queries = [
        "What is TCS?",
        "Tell me about Tata Consultancy Services",
    ]
    
    print("\n" + "="*70)
    print("GOOGLE SEARCH AGENT - Test Mode")
    print("="*70)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 70)
        result = process_query(query)
        print(f"Response:\n{result}")
        print("-" * 70)
