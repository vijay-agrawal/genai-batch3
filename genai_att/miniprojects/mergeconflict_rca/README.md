# Merge Conflict Root Cause Analyzer

AI-powered tool that identifies which commit on the `main` branch caused a feature branch's tests to fail after merge — built for large-scale telecom billing codebases with many contributors.

---

## Problem Description

In large telco development teams, a common and painful workflow issue arises during feature branch merges:

```
Feature Branch:  A───B───C───D  (all tests pass)
                /
Main Branch:   M───E───F───G───H───I───J  (other developers' commits)
                \                         \
                 └─── Merge attempt ───────→  Tests FAIL
```

1. A developer creates a **feature branch** from `main` and builds a new capability (e.g., a loyalty discount engine for the billing system).
2. All tests pass on the feature branch in isolation.
3. Meanwhile, **10–50+ commits** land on `main` from other developers across the organization.
4. When the feature branch is merged back into `main`, **certain tests fail** or runtime errors occur.
5. The change works fine in the branch, but **breaks when merged**.

The developer must now **manually sift through all commits** on `main` between the branch-off point and the merge point to locate which commit (from someone else) introduced the incompatibility. Commit descriptions are often vague ("refactor billing utils", "update config"), and the developer must read through code diffs — a tedious, error-prone process that can take hours.

### Why This Is Hard

- **Volume**: Dozens to hundreds of commits to review
- **Subtlety**: The conflict is often semantic, not textual (no merge conflict markers, but behavior changed)
- **Cross-team**: The developer has no context on what other teams changed or why
- **Time pressure**: Merge failures block CI/CD pipelines and release timelines

---

## Proposed Solutions

### Solution 1: RAG-Based Commit Bisect Advisor (Implemented)

Build a Retrieval-Augmented Generation (RAG) pipeline over commit diffs and metadata. When a merge failure occurs:

1. **Index** all commits on `main` (between branch-off and merge) into a vector store — storing diffs, commit messages, file paths, and function signatures as embeddings
2. **Analyze the failure** — parse the error/test failure log to extract failing tests, error types, affected files, and symbols
3. **Retrieve** the most relevant commits via semantic similarity search against the error context
4. **Rank and explain** — an LLM analyzes retrieved candidates using chain-of-thought reasoning and produces a ranked suspect list with explanations

| Pros | Cons |
|------|------|
| Works well for large histories (100s of commits) | Requires vector store infrastructure (ChromaDB, etc.) |
| Retrieval step keeps LLM context focused and cost-efficient | Retrieval quality depends on chunking strategy for diffs |
| Can be integrated into CI/CD pipelines | May miss subtle semantic conflicts if embeddings don't capture nuance |
| Scales to very large repositories | Initial indexing step adds latency |
| Reusable index — query multiple failures against same commit window | Setup complexity is higher than direct LLM approach |

### Solution 2: LLM-Powered Direct Diff Analysis with Chain-of-Thought

Feed the LLM the failing test/error context along with commit diffs directly (in batches):

1. **Collect context** — gather error log, failing test code, and the feature branch's changes
2. **Batch-analyze diffs** — for each commit, send diff + message to the LLM with a structured prompt: *"Does this commit conflict with the feature? Rate: HIGH / MEDIUM / LOW / NONE."*
3. **Aggregate and rank** — collect all ratings, sort by suspicion level, present final summary
4. **Cross-commit reasoning** — optional final pass where the LLM sees all HIGH/MEDIUM candidates together to reason about combined effects

| Pros | Cons |
|------|------|
| Simpler architecture — no vector DB needed | Higher token cost for large commit histories |
| Better at catching semantic conflicts (behavioral changes) | Needs batching strategy for repos with many commits |
| Chain-of-thought provides transparent, auditable explanations | Latency scales linearly with number of commits |
| Easier to implement as a quick prototype | Every commit is sent to LLM, even obviously irrelevant ones |

### Recommendation

**Solution 1 (RAG)** was chosen for implementation, enhanced with a **hybrid retrieval** approach that adds deterministic file-impact analysis to complement semantic search:

- The retrieval step acts as an intelligent pre-filter, reducing 15+ commits down to the 5–8 most relevant before LLM analysis — saving tokens and improving signal-to-noise ratio
- The vector store is reusable: if the same merge window causes multiple different failures, you don't re-embed the commits
- It mirrors the real-world scale better: in production, you might have 100+ commits and cannot send them all to an LLM
- The architecture naturally extends to a CI/CD integration where commits are indexed continuously

---

## Implementation Highlights

### Architecture: Hybrid Retrieval (File Impact + Semantic RAG)

A pure semantic (embedding-based) retrieval has a critical blind spot: **file paths are structural identifiers, not semantic concepts**. The embedding model captures the meaning of words like "billing" and "utils", but it cannot reliably determine that `src/billing/billing_utils.py` in the error log refers to the exact same file as `src/billing/billing_utils.py` modified in a commit. Two commits touching the same file could end up far apart in embedding space if their diff content discusses different things.

To address this, the implementation uses a **hybrid retrieval** approach:

```
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
                       │ (40% file + 60% sem)   │
            ┌──────────▼──────────┐             │
            │  LLM Analysis       │◄────────────┘
            │  (chain-of-thought) │  (error log context)
            └──────────┬──────────┘
                       │
            ┌──────────▼──────────┐
            │  Ranked Suspects    │
            │  + Root Cause Report│
            └─────────────────────┘
```

### Why Hybrid Retrieval?

| Signal | What it catches | What it misses |
|--------|----------------|----------------|
| **Semantic (embeddings)** | Behavioral/API changes where diff content is similar to the error | Same-file modifications where the diff content is about something different |
| **File Impact (deterministic)** | Any commit that touches the same files as the error/feature | Behavioral changes in a different file that affect the same API |
| **Hybrid (both)** | Covers both structural and semantic overlap | Minimal blind spots |

### File Impact Scoring

The file-impact analyzer extracts file paths from three sources:
1. **Error log** — parses tracebacks and file references (e.g., `src/billing/loyalty_engine.py:27`)
2. **Feature branch** — collects all files changed + files referenced in imports/diffs
3. **Combined set** — union of all impacted files

Each main branch commit is scored:
- **Exact file match: 3 points** — commit modifies the same file referenced in the error
- **Same directory: 1 point** — commit modifies a sibling file in the same package
- **Diff reference: 0.5 points** — commit's diff text mentions a filename from the impacted set

Example from our scenario:
```
m012hij  score=5.5  — billing_config.py (EXACT MATCH) + billing_defaults.yaml (same dir)
m009yza  score=2.0  — billing_utils.py (same dir) + currency_converter.py (same dir)
m007stu  score=3.0  — roaming_calculator.py (same dir) + roaming_rates.yaml (same dir)
```

### Hybrid Merge Formula

```
hybrid_score = 0.4 × normalized_file_impact + 0.6 × normalized_semantic_similarity
```

- Both scores are normalized to 0–1 range before combining
- Semantic similarity gets higher weight (0.6) because it captures behavioral/API changes
- File impact gets meaningful weight (0.4) to ensure structural matches are never ignored
- Commits that appear in BOTH signals get a significant boost

### Synthetic Scenario: Telco Billing System

The POC uses a realistic synthetic dataset simulating a telecom billing codebase:

- **Feature branch** (`feature/loyalty-discount`): Developer Alice Chen adds a tiered loyalty discount engine that integrates with the shared `calculate_line_item_charge()` utility in `billing_utils.py`. All 3 commits pass tests in isolation.

- **Main branch** (15 commits from 15 different developers): Includes CDR timezone fixes, API docs, usage alerts, payment gateway refactors, rate plan caching, roaming charges, integration tests, config restructuring, pytest upgrades, tax calculators, and concurrency fixes.

- **Primary culprit** — Commit `m009yza` by Jake Thompson: Refactored `calculate_line_item_charge()` to add `currency` and `billing_region` parameters for multi-currency support. This changed the function signature that Alice's loyalty engine depends on.

- **Secondary culprit** — Commit `m012hij` by Maria Gonzalez: Restructured `BillingConfig` from a flat YAML format to a nested environment-aware format, triggering config access warnings.

- **13 innocent commits** serve as noise that the system must correctly filter out.

### Key Design Decisions

1. **One document per commit**: Each commit (metadata + full diff) is stored as a single embedding. This ensures retrieval returns complete commit context rather than fragments.

2. **Hybrid retrieval with two complementary signals**: File-impact analysis provides deterministic path-matching that embeddings cannot reliably perform. Semantic search captures behavioral and API-level changes. Together, they cover both structural and semantic dimensions.

3. **File-impact data passed to LLM**: The LLM prompt includes file-impact scores alongside diffs, so it can factor in structural overlap when reasoning about causality. This helps the LLM avoid dismissing a commit that modifies the exact file mentioned in the error.

4. **Structured LLM prompt**: The analysis prompt enforces a systematic evaluation: for each candidate, the LLM must state what changed, whether it overlaps with the feature (checking the file-impact score), whether it could cause the specific error, and assign a suspicion rating.

5. **Streamlit UI with 4 tabs**: Merge Failure details, interactive Hybrid Analysis showing all pipeline steps, Ground Truth validation, and a full Commit Browser with culprit highlighting.

### Validated Results

The hybrid pipeline correctly:
- **File impact** flagged `m012hij` (secondary culprit) with the highest file score (5.5) due to exact match on `billing_config.py`
- **Semantic search** ranked `m009yza` (primary culprit) as #1 due to diff content about `calculate_line_item_charge`
- **Hybrid merge** surfaced both culprits in the **top 2 positions**
- The LLM rated `m009yza` as **HIGH suspicion** and `m012hij` as **MEDIUM suspicion**
- Provided a concrete code fix suggestion for the developer

---

## Project Structure

```
merge_rca/
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── generate_synthetic_data.py        # Generates realistic telco billing commit data
├── 01_index_commits.py               # Indexes commit diffs into ChromaDB vector store
├── 02_analyze_merge_failure.py       # Full hybrid analysis pipeline (CLI)
├── app.py                            # Streamlit interactive UI
├── synthetic_data/                   # Generated scenario data
│   ├── feature_branch.json           #   Feature branch commits (3)
│   ├── main_branch_commits.json      #   Main branch commits (15)
│   ├── merge_failure.json            #   Error log from failed merge
│   └── complete_scenario.json        #   Combined dataset with ground truth
└── chroma_db/                        # ChromaDB vector store (created by indexer)
```

---

## Steps to Run

### Prerequisites

- Python 3.10+
- Azure OpenAI access with:
  - A chat completion deployment (e.g., `gpt-4o-mini`)
  - An embedding deployment (e.g., `text-embedding-3-small`)
- Environment variables configured in the parent directory's `.env` file:
  ```
  AZURE_OPENAI_ENDPOINT=<your-endpoint>
  AZURE_OPENAI_API_KEY=<your-key>
  AZURE_OPENAI_API_VERSION=<api-version>
  AZURE_OPENAI_MODEL_NAME=<deployment-name>
  AZURE_OPENAI_EMBEDDING_ENDPOINT=<embedding-endpoint>
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=<embedding-deployment>
  AZURE_OPENAI_EMBEDDING_API_KEY=<embedding-key>
  ```

### Installation

```bash
cd merge_rca
pip install -r requirements.txt
```

### Step 1: Generate Synthetic Data

```bash
python generate_synthetic_data.py
```

Creates 4 JSON files in `synthetic_data/` with the telco billing merge failure scenario.

### Step 2: Index Commits into Vector Store

```bash
python 01_index_commits.py
```

Embeds all 15 main branch commits into ChromaDB. Creates the `chroma_db/` directory.

### Step 3a: Run Analysis (CLI)

```bash
python 02_analyze_merge_failure.py
```

Runs the full hybrid pipeline in the terminal:
1. File impact analysis (deterministic path matching)
2. Semantic retrieval (ChromaDB similarity search)
3. Hybrid merge (weighted combination)
4. LLM chain-of-thought analysis
5. Ranked suspects with explanations

### Step 3b: Run Analysis (Streamlit UI)

```bash
streamlit run app.py
```

Opens an interactive web UI at `http://localhost:8501` with four tabs:

| Tab | Description |
|-----|-------------|
| **Merge Failure** | View the error log, feature branch commits, and their diffs |
| **Hybrid Analysis** | Run the 4-step pipeline: file-impact scoring, semantic retrieval, hybrid merge, LLM reasoning. Each step's output is displayed |
| **Ground Truth** | Reveal the actual culprit commits and validate against the analysis results |
| **Commit Browser** | Browse all 15 main branch commits with diffs; culprits are highlighted |

---

## Technologies Used

| Technology | Role |
|------------|------|
| Azure OpenAI (gpt-4o-mini) | LLM for chain-of-thought root cause analysis |
| Azure OpenAI (text-embedding-3-small) | Embedding model for semantic search |
| ChromaDB | Vector store for commit diff embeddings |
| LangChain | RAG orchestration (retriever, prompts, LCEL chains) |
| Streamlit | Interactive web UI |
| Python | Core language |
