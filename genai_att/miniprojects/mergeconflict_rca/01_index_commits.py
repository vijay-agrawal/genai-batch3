"""
Commit Diff Indexer for Merge Conflict Analyzer
=================================================
Reads synthetic commit data and indexes each commit's diff + metadata
into a ChromaDB vector store for RAG-based retrieval.

Each commit is chunked into meaningful segments:
  - Commit metadata (author, message, date, files changed)
  - Each file diff within the commit (separately, for granular retrieval)

This enables semantic search: when a merge failure mentions a specific
function, file, or behavior, the retriever finds the most relevant commits.
"""

import os
import json
import shutil
import warnings
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv

# Load env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
warnings.filterwarnings("ignore")

CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chroma_db')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'synthetic_data')


def load_commits():
    """Load main branch commits from synthetic data."""
    with open(os.path.join(DATA_DIR, "main_branch_commits.json")) as f:
        return json.load(f)


def create_commit_documents(commits):
    """
    Convert each commit into LangChain Documents for embedding.

    Strategy: Create one document per commit that combines:
    - Commit metadata (hash, author, date, message)
    - Files changed
    - Full diff content

    This ensures that each commit's complete context is captured in one
    embedding, making retrieval straightforward (one hit = one suspect commit).
    """
    documents = []

    for i, commit in enumerate(commits):
        # Build a rich text representation of the commit
        text = f"""COMMIT #{i+1}
Commit Hash: {commit['hash']}
Author: {commit['author']}
Date: {commit['date']}
Message: {commit['message']}
Files Changed: {', '.join(commit['files_changed'])}

CODE DIFF:
{commit['diff']}
"""
        metadata = {
            "commit_hash": commit['hash'],
            "author": commit['author'],
            "date": commit['date'],
            "message": commit['message'],
            "files_changed": ", ".join(commit['files_changed']),
            "commit_index": i + 1,
        }

        documents.append(Document(page_content=text, metadata=metadata))

    return documents


def create_vector_store(documents):
    """Create ChromaDB vector store from commit documents."""

    # Clear existing vector database
    if os.path.exists(CHROMA_PATH):
        print(f"Clearing existing vector database at {CHROMA_PATH}")
        shutil.rmtree(CHROMA_PATH)

    embeddings = AzureOpenAIEmbeddings(
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
        api_key=os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
    )

    print(f"Creating embeddings for {len(documents)} commit documents...")

    vector_store = Chroma.from_documents(
        documents,
        embeddings,
        persist_directory=CHROMA_PATH
    )

    print(f"Successfully created {vector_store._collection.count()} embeddings in ChromaDB")
    return vector_store


# ── MAIN ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("MERGE CONFLICT ANALYZER - Commit Indexer")
    print("=" * 70)

    # Load commits
    commits = load_commits()
    print(f"\nLoaded {len(commits)} commits from main branch")

    # Show commit summary
    print("\nCommits to index:")
    for i, c in enumerate(commits):
        print(f"  #{i+1:2d} [{c['hash']}] {c['author']:20s} - {c['message'][:60]}")

    # Create documents
    documents = create_commit_documents(commits)
    print(f"\nCreated {len(documents)} documents for embedding")

    # Index into ChromaDB
    create_vector_store(documents)

    print(f"\nVector store saved to: {CHROMA_PATH}")
    print("Done! Ready for merge failure analysis.")
