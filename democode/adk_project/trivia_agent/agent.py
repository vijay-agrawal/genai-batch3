import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session
from google.genai import types

import os
from pathlib import Path
from dotenv import load_dotenv

import sys
sys.path.append(".")
from callback_logging import log_query_to_model, log_model_response
import google.cloud.logging

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
    return Path(__file__).resolve().parent

# 1. Load environment variables from the agent directory's .env file
PROJECT_ROOT = _find_project_root()
load_dotenv(PROJECT_ROOT / ".env")

# Resolve relative credential paths to absolute
_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if _creds_path and not Path(_creds_path).is_absolute():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str((PROJECT_ROOT / _creds_path).resolve())

google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT")
google_cloud_location = os.getenv("GOOGLE_CLOUD_LOCATION")
google_genai_use_vertexai = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "1")
model_name = os.getenv("MODEL", "gemini-2.5-flash")

cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

# ============================================================================
# Define root_agent at module level for ADK web server
# ============================================================================
root_agent = Agent(
    model=model_name,
    name="trivia_agent",
    instruction="Answer questions accurately and helpfully.",
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
)

# Create an async main function
async def main():

    # 2. Set or load other variables
    app_name = 'my_agent_app'
    user_id_1 = 'user1'

    # 3. Create a Runner using the module-level root_agent
    runner = InMemoryRunner(
        agent=root_agent,
        app_name=app_name,
    )

    # 4. Create a session
    my_session = await runner.session_service.create_session(
        app_name=app_name, user_id=user_id_1
    )

    # 5. Prepare a function to package a user's message as
    # genai.types.Content, run it asynchronously, and iterate
    # through the response 
    async def run_prompt(session: Session, new_message: str):
        content = types.Content(
                role='user', parts=[types.Part.from_text(text=new_message)]
            )
        print('** User says:', content.model_dump(exclude_none=True))
        async for event in runner.run_async(
            user_id=user_id_1,
            session_id=session.id,
            new_message=content,
        ):
            if event.content.parts and event.content.parts[0].text:
                print(f'** {event.author}: {event.content.parts[0].text}')

        cloud_logging_client.close()


    # 6. Use this function on a new query
    query = "What is the capital of France?"
    await run_prompt(my_session, query)

if __name__ == "__main__":
    asyncio.run(main())