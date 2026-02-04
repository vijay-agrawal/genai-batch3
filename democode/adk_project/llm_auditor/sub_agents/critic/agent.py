# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Critic agent for identifying and verifying statements using search tools."""

import os
from pathlib import Path
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.adk.tools import google_search
from google.genai import types

import sys
sys.path.append("../..")
from callback_logging import log_query_to_model, log_model_response

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

# Load environment variables
PROJECT_ROOT = _find_project_root()
load_dotenv(PROJECT_ROOT / ".env")

# Resolve relative credential paths to absolute
_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if _creds_path and not Path(_creds_path).is_absolute():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str((PROJECT_ROOT / _creds_path).resolve())

from . import prompt


def _render_reference(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse:
    """Appends grounding references to the response."""
    del callback_context
    if (
        not llm_response.content or
        not llm_response.content.parts or
        not llm_response.grounding_metadata
    ):
        return llm_response
    references = []
    for chunk in llm_response.grounding_metadata.grounding_chunks or []:
        title, uri, text = '', '', ''
        if chunk.retrieved_context:
            title = chunk.retrieved_context.title
            uri = chunk.retrieved_context.uri
            text = chunk.retrieved_context.text
        elif chunk.web:
            title = chunk.web.title
            uri = chunk.web.uri
        parts = [s for s in (title, text) if s]
        if uri and parts:
            parts[0] = f'[{parts[0]}]({uri})'
        if parts:
            references.append('* ' + ': '.join(parts) + '\n')
    if references:
        reference_text = ''.join(['\n\nReference:\n\n'] + references)
        llm_response.content.parts.append(types.Part(text=reference_text))
    if all(part.text is not None for part in llm_response.content.parts):
        all_text = '\n'.join(part.text for part in llm_response.content.parts)
        llm_response.content.parts[0].text = all_text
        del llm_response.content.parts[1:]
    return llm_response


critic_agent = Agent(
    model=os.getenv("MODEL", "gemini-2.5-flash"),
    name='critic_agent',
    instruction=prompt.CRITIC_PROMPT,
    tools=[google_search],
    before_model_callback=log_query_to_model,
    after_model_callback=_render_reference,
)
