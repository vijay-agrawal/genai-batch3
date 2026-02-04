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

"""LLM Auditor for verifying & refining LLM-generated answers using the web."""

import os
from pathlib import Path
from dotenv import load_dotenv

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

from google.adk.agents import SequentialAgent

from .sub_agents.critic import critic_agent
from .sub_agents.reviser import reviser_agent

import logging
import google.cloud.logging

logging.basicConfig()

cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()


llm_auditor = SequentialAgent(
    name='llm_auditor',
    description=(
        'Evaluates LLM-generated answers, verifies actual accuracy using the'
        ' web, and refines the response to ensure alignment with real-world'
        ' knowledge.'
    ),
    sub_agents=[critic_agent, reviser_agent],
)

root_agent = llm_auditor
