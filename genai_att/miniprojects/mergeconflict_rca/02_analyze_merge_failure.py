"""
Merge Failure Analyzer (RAG-Based + File Impact Analysis)
===========================================================
Given a merge failure (error log + feature branch info), this module:

1. FILE IMPACT ANALYSIS — deterministic file-overlap scoring to identify commits
   that touch the same files/directories as the feature branch or error log.
   File paths are structural identifiers, not semantic concepts — embeddings
   cannot reliably match them, so we use explicit set-intersection instead.
2. RETRIEVES the most relevant commits from ChromaDB using semantic search
   on the error log and feature branch context (captures behavioral/API changes)
3. HYBRID MERGE — combines file-overlap scores with semantic similarity to
   produce a ranked candidate list that is stronger than either signal alone
4. RANKS each candidate by suspicion level using LLM chain-of-thought
5. GENERATES a final root cause analysis report

Architecture:
                     ┌──────────────────────────┐
                     │   Merge Failure Input     │
                     │  (error log + feature     │
                     │   branch context)         │
                     └──────────┬───────────────┘
                                │
               ┌────────────────┼────────────────┐
               │                │                │
    ┌──────────▼──────┐  ┌─────▼──────────┐     │
    │  File Impact    │  │  Semantic      │     │
    │  Analysis       │  │  Retrieval     │     │
    │  (deterministic │  │  (ChromaDB     │     │
    │   set overlap)  │  │   embeddings)  │     │
    └──────────┬──────┘  └─────┬──────────┘     │
               │               │                │
               └───────┬───────┘                │
                       │ Hybrid merge           │
            ┌──────────▼──────────┐             │
            │  LLM Analysis       │◄────────────┘
            │  (chain-of-thought) │  (error log context)
            └──────────┬──────────┘
                       │
            ┌──────────▼──────────┐
            │  Ranked Suspects    │
            │  + Root Cause Report│
            └─────────────────────┘
"""

import os
import re
import json
import warnings
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
warnings.filterwarnings("ignore")

CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chroma_db')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'synthetic_data')


# ── File Impact Analysis (Deterministic) ─────────────────────────────────
#
# WHY THIS EXISTS:
# File paths like "src/billing/billing_utils.py" are structural identifiers.
# Embedding models capture semantic meaning of words ("billing", "utils"),
# but cannot reliably match the IDENTITY of a path. Two commits touching
# the exact same file could end up far apart in embedding space if their
# diff content discusses different things.
#
# File-overlap scoring is deterministic and precise: if commit X modifies
# src/billing/billing_utils.py and the error log references that same file,
# that's a hard signal that no embedding can replicate.

def extract_files_from_error_log(error_log):
    """
    Parse the error log to extract file paths mentioned in tracebacks,
    error messages, and stack frames.
    """
    # Match patterns like: src/billing/loyalty_engine.py:27
    # or paths in "Note:" lines, import statements, etc.
    file_pattern = r'((?:src|tests|lib|app)/[\w/]+\.(?:py|yaml|json|yml|js|ts|cfg))'
    matches = re.findall(file_pattern, error_log)
    # Normalize separators
    return set(m.replace('\\', '/') for m in matches)


def extract_files_from_feature_branch(feature_branch):
    """
    Collect all files touched by the feature branch (changed + imported/referenced).
    """
    files = set()
    for commit in feature_branch['commits']:
        for f in commit['files_changed']:
            files.add(f.replace('\\', '/'))
        # Also extract file references from the diff itself (imports, references)
        diff_files = re.findall(
            r'((?:src|tests|lib|app)/[\w/]+\.(?:py|yaml|json|yml|js|ts|cfg))',
            commit['diff']
        )
        files.update(f.replace('\\', '/') for f in diff_files)
    return files


def compute_file_impact_scores(main_commits, impacted_files):
    """
    For each main branch commit, compute a file-impact score based on how
    many of its changed files overlap with the impacted file set.

    Scoring:
      - Exact file match:      3 points (same file modified)
      - Same directory match:  1 point  (sibling file in same package)

    Returns a list of (commit_index, commit, score, matched_files) sorted
    by score descending.
    """
    impacted_dirs = set(os.path.dirname(f) for f in impacted_files)

    scored = []
    for i, commit in enumerate(main_commits):
        score = 0
        matched_files = []
        commit_files = [f.replace('\\', '/') for f in commit['files_changed']]

        for cf in commit_files:
            # Exact file match
            if cf in impacted_files:
                score += 3
                matched_files.append(f"{cf} (EXACT MATCH)")
            # Same directory match
            elif os.path.dirname(cf) in impacted_dirs:
                score += 1
                matched_files.append(f"{cf} (same directory as impacted files)")

        # Also check if the diff references any impacted files (imports, function calls)
        diff_text = commit.get('diff', '')
        for impacted_file in impacted_files:
            # Check for the filename (without path) in the diff
            basename = os.path.basename(impacted_file).replace('.py', '')
            if basename in diff_text and cf not in impacted_files:
                # Referenced but not in files_changed — weaker signal
                score += 0.5
                matched_files.append(f"references '{basename}' in diff")

        scored.append({
            'commit_index': i,
            'commit': commit,
            'file_impact_score': score,
            'matched_files': matched_files,
        })

    # Sort by score descending
    scored.sort(key=lambda x: x['file_impact_score'], reverse=True)
    return scored


# ── RAG Retrieval (Semantic) ─────────────────────────────────────────────

def get_vector_store():
    """Load the ChromaDB vector store with commit embeddings."""
    embeddings = AzureOpenAIEmbeddings(
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
        api_key=os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
    )
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )


def build_retrieval_query(merge_failure, feature_branch):
    """
    Build a semantic search query from the merge failure context.
    Combines error log keywords, affected files, and feature branch context
    to produce a query that will match the most relevant commits.
    """
    query = f"""
Merge failure in telco billing system.
Feature branch: {feature_branch['branch_name']} by {feature_branch['developer']}
Feature description: {feature_branch['description']}

Error log summary:
{merge_failure['error_log'][:1500]}

Affected files: {', '.join(merge_failure['affected_files_in_feature'])}
"""
    return query


def retrieve_candidate_commits(vector_store, query, k=8):
    """
    Retrieve top-K most semantically similar commits to the failure context.
    Returns more than we need so the LLM can reason over a broader set.
    """
    retriever = vector_store.as_retriever(
        search_type='similarity',
        search_kwargs={'k': k}
    )
    results = retriever.invoke(query)
    return results


# ── Hybrid Merge ─────────────────────────────────────────────────────────

def hybrid_merge(file_impact_results, semantic_results, main_commits, top_n=8):
    """
    Merge file-impact scores with semantic retrieval results into a single
    ranked candidate list.

    Strategy:
      - Normalize both scores to 0-1 range
      - Weighted combination: 0.4 * file_impact + 0.6 * semantic_similarity
      - File impact acts as a BOOST — commits with file overlap that were
        also semantically retrieved get a significant ranking boost
      - Commits with high file impact but NOT in semantic results are still
        included (these are the cases pure RAG would miss)

    Returns list of dicts with combined scores.
    """
    # Build lookup: commit_hash -> file impact data
    file_scores = {}
    max_file_score = max((r['file_impact_score'] for r in file_impact_results), default=1) or 1
    for r in file_impact_results:
        h = r['commit']['hash']
        file_scores[h] = {
            'raw_score': r['file_impact_score'],
            'normalized': r['file_impact_score'] / max_file_score,
            'matched_files': r['matched_files'],
            'commit': r['commit'],
        }

    # Build lookup: commit_hash -> semantic rank (lower = better)
    semantic_ranks = {}
    for rank, doc in enumerate(semantic_results):
        h = doc.metadata['commit_hash']
        # Convert rank to a 0-1 score (rank 0 = 1.0, last rank = ~0)
        semantic_ranks[h] = {
            'rank': rank,
            'normalized': 1.0 - (rank / max(len(semantic_results), 1)),
            'doc': doc,
        }

    # Combine all unique commit hashes from both sources
    all_hashes = set(file_scores.keys()) | set(semantic_ranks.keys())

    combined = []
    for h in all_hashes:
        fs = file_scores.get(h, {'raw_score': 0, 'normalized': 0, 'matched_files': [], 'commit': None})
        ss = semantic_ranks.get(h, {'rank': -1, 'normalized': 0, 'doc': None})

        hybrid_score = 0.4 * fs['normalized'] + 0.6 * ss['normalized']

        # Find the commit data
        commit = fs['commit']
        if commit is None:
            commit = next((c for c in main_commits if c['hash'] == h), None)

        combined.append({
            'commit_hash': h,
            'commit': commit,
            'file_impact_score': fs['raw_score'],
            'file_impact_normalized': fs['normalized'],
            'matched_files': fs['matched_files'],
            'semantic_rank': ss['rank'],
            'semantic_normalized': ss['normalized'],
            'hybrid_score': round(hybrid_score, 3),
            'in_semantic_results': ss['rank'] >= 0,
            'in_file_impact': fs['raw_score'] > 0,
            'doc': ss.get('doc'),
        })

    # Sort by hybrid score descending
    combined.sort(key=lambda x: x['hybrid_score'], reverse=True)
    return combined[:top_n]


# ── LLM Analysis ─────────────────────────────────────────────────────────

ANALYSIS_PROMPT = """You are a senior software engineer specializing in merge conflict root cause analysis
for a large-scale telecom billing system. Your job is to identify which commit(s) on the main
branch caused the feature branch's tests to fail after merge.

## FEATURE BRANCH CONTEXT
Branch: {branch_name}
Developer: {developer}
Description: {feature_description}

Key feature branch code (the code that is now failing):
{feature_diff_summary}

## MERGE FAILURE - ERROR LOG
{error_log}

## CANDIDATE COMMITS (Ranked by hybrid score: file-impact + semantic similarity)
These commits were selected using two complementary signals:
1. **File Impact Analysis** (deterministic) — exact file-path overlap between each
   commit's changed files and the files referenced in the error log / feature branch.
2. **Semantic Similarity** (embedding-based) — cosine similarity between the error
   context and the commit's diff content in ChromaDB.

Commits with HIGH file-impact scores touch the same files as the failure — pay
special attention to these even if their semantic score is lower.

{candidate_commits}

## YOUR TASK
For each candidate commit above, analyze whether it could have caused the merge failure.
Use chain-of-thought reasoning:

1. What does this commit change?
2. Does it touch the same files, functions, APIs, or configurations as the feature branch?
   (Check the FILE IMPACT SCORE — a non-zero score means direct file overlap)
3. Could it cause the specific errors shown in the error log?
4. Rate the suspicion level: HIGH, MEDIUM, LOW, or NONE

Then provide:
- A RANKED LIST of suspects (most likely first)
- For each suspect rated MEDIUM or above, explain the specific causal chain
- A FINAL RECOMMENDATION on which commit is the primary root cause and what fix is needed

Format your response clearly with markdown headers and bullet points.
"""


def get_llm():
    """Initialize Azure OpenAI LLM."""
    return AzureChatOpenAI(
        temperature=0,
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        model=os.getenv("AZURE_OPENAI_MODEL_NAME")
    )


def format_candidate_commits_hybrid(hybrid_results):
    """Format hybrid-ranked commit candidates for the LLM prompt, including file-impact data."""
    formatted = []
    for i, entry in enumerate(hybrid_results, 1):
        commit = entry['commit']
        file_impact_str = f"{entry['file_impact_score']:.1f}"
        semantic_str = f"Rank #{entry['semantic_rank']+1}" if entry['in_semantic_results'] else "Not in top semantic results"
        matched_str = ", ".join(entry['matched_files']) if entry['matched_files'] else "None"

        # Use the doc's page_content (full diff) if available from semantic results,
        # otherwise reconstruct from commit data
        if entry['doc']:
            diff_content = entry['doc'].page_content
        else:
            diff_content = f"""COMMIT
Commit Hash: {commit['hash']}
Author: {commit['author']}
Date: {commit['date']}
Message: {commit['message']}
Files Changed: {', '.join(commit['files_changed'])}

CODE DIFF:
{commit['diff']}
"""

        formatted.append(f"""### Candidate #{i} (Hybrid Score: {entry['hybrid_score']})
- **Commit:** {commit['hash']}
- **Author:** {commit['author']}
- **Date:** {commit['date']}
- **Message:** {commit['message']}
- **Files Changed:** {', '.join(commit['files_changed'])}
- **FILE IMPACT SCORE:** {file_impact_str} — Matched: [{matched_str}]
- **Semantic Retrieval:** {semantic_str}

**Diff:**
```
{diff_content}
```
""")
    return "\n---\n".join(formatted)


def format_feature_diff_summary(feature_branch):
    """Extract a summary of the feature branch's key code for context."""
    summaries = []
    for commit in feature_branch['commits']:
        summaries.append(f"**{commit['message']}**\n```\n{commit['diff'][:800]}\n```")
    return "\n\n".join(summaries)


def analyze_merge_failure(merge_failure, feature_branch, hybrid_results):
    """
    Run the LLM analysis chain on hybrid-ranked candidates to identify root cause.
    """
    llm = get_llm()

    prompt = ChatPromptTemplate.from_template(ANALYSIS_PROMPT)

    chain = prompt | llm | StrOutputParser()

    result = chain.invoke({
        "branch_name": feature_branch['branch_name'],
        "developer": feature_branch['developer'],
        "feature_description": feature_branch['description'],
        "feature_diff_summary": format_feature_diff_summary(feature_branch),
        "error_log": merge_failure['error_log'],
        "candidate_commits": format_candidate_commits_hybrid(hybrid_results),
    })

    return result


# ── Full Pipeline ─────────────────────────────────────────────────────────

def run_full_analysis():
    """Execute the complete hybrid (file-impact + RAG) merge failure analysis pipeline."""

    print("=" * 70)
    print("MERGE CONFLICT ANALYZER - Hybrid (File Impact + RAG) Root Cause Analysis")
    print("=" * 70)

    # Step 1: Load data
    print("\n[Step 1] Loading merge failure data...")
    with open(os.path.join(DATA_DIR, "merge_failure.json")) as f:
        merge_failure = json.load(f)
    with open(os.path.join(DATA_DIR, "feature_branch.json")) as f:
        feature_branch = json.load(f)
    with open(os.path.join(DATA_DIR, "main_branch_commits.json")) as f:
        main_commits = json.load(f)

    print(f"  Branch: {feature_branch['branch_name']}")
    print(f"  Developer: {feature_branch['developer']}")
    print(f"  Merge status: {merge_failure['merge_status']}")

    # Step 2: File Impact Analysis (deterministic)
    print("\n[Step 2] Running file impact analysis...")
    error_files = extract_files_from_error_log(merge_failure['error_log'])
    feature_files = extract_files_from_feature_branch(feature_branch)
    impacted_files = error_files | feature_files

    print(f"  Files from error log:     {error_files}")
    print(f"  Files from feature branch: {feature_files}")
    print(f"  Combined impacted files:   {impacted_files}")

    file_impact_results = compute_file_impact_scores(main_commits, impacted_files)

    print(f"\n  File impact scores (non-zero only):")
    for r in file_impact_results:
        if r['file_impact_score'] > 0:
            print(f"    [{r['commit']['hash']}] score={r['file_impact_score']:.1f} "
                  f"— {r['commit']['author']} — {', '.join(r['matched_files'])}")

    # Step 3: Semantic Retrieval (embedding-based)
    print("\n[Step 3] Retrieving semantically similar commits from ChromaDB...")
    vector_store = get_vector_store()
    query = build_retrieval_query(merge_failure, feature_branch)
    semantic_results = retrieve_candidate_commits(vector_store, query, k=8)

    print(f"  Retrieved {len(semantic_results)} commits by semantic similarity:")
    for i, doc in enumerate(semantic_results, 1):
        meta = doc.metadata
        print(f"    #{i} [{meta['commit_hash']}] {meta['author']} - {meta['message'][:50]}")

    # Step 4: Hybrid Merge
    print("\n[Step 4] Merging file-impact + semantic scores...")
    hybrid_results = hybrid_merge(file_impact_results, semantic_results, main_commits, top_n=8)

    print(f"  Hybrid-ranked candidates:")
    for i, entry in enumerate(hybrid_results, 1):
        c = entry['commit']
        flags = []
        if entry['in_file_impact']:
            flags.append(f"file={entry['file_impact_score']:.1f}")
        if entry['in_semantic_results']:
            flags.append(f"sem=#{entry['semantic_rank']+1}")
        flag_str = ", ".join(flags) if flags else "low signal"
        print(f"    #{i} [{c['hash']}] hybrid={entry['hybrid_score']:.3f} ({flag_str}) "
              f"— {c['author']} — {c['message'][:40]}")

    # Step 5: LLM Analysis
    print("\n[Step 5] Running LLM chain-of-thought analysis on hybrid candidates...")
    analysis = analyze_merge_failure(merge_failure, feature_branch, hybrid_results)

    print("\n" + "=" * 70)
    print("ANALYSIS RESULT")
    print("=" * 70)
    print(analysis)

    return {
        "file_impact": [
            {
                "hash": r['commit']['hash'],
                "author": r['commit']['author'],
                "message": r['commit']['message'],
                "file_impact_score": r['file_impact_score'],
                "matched_files": r['matched_files'],
            }
            for r in file_impact_results if r['file_impact_score'] > 0
        ],
        "semantic_results": [
            {
                "hash": doc.metadata['commit_hash'],
                "author": doc.metadata['author'],
                "message": doc.metadata['message'],
            }
            for doc in semantic_results
        ],
        "hybrid_results": [
            {
                "hash": entry['commit']['hash'],
                "hybrid_score": entry['hybrid_score'],
                "file_impact_score": entry['file_impact_score'],
                "semantic_rank": entry['semantic_rank'],
            }
            for entry in hybrid_results
        ],
        "analysis": analysis,
    }


if __name__ == "__main__":
    result = run_full_analysis()
