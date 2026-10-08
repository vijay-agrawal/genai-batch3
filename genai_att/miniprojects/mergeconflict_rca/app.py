"""
Merge Conflict Analyzer - Streamlit App
==========================================
RAG-powered tool to identify which commit on the main branch caused
a feature branch's tests to fail after merge.

Uses: Azure OpenAI + ChromaDB + LangChain

Run: streamlit run app.py
"""

import os
import json
import streamlit as st
import warnings
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
warnings.filterwarnings("ignore")

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import re

CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chroma_db')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'synthetic_data')


# ── Data Loading ──────────────────────────────────────────────────────────

@st.cache_data
def load_scenario_data():
    """Load all synthetic scenario data."""
    with open(os.path.join(DATA_DIR, "complete_scenario.json")) as f:
        return json.load(f)


# ── RAG Components ────────────────────────────────────────────────────────

@st.cache_resource
def get_vector_store():
    """Load ChromaDB vector store with commit embeddings."""
    embeddings = AzureOpenAIEmbeddings(
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
        api_key=os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
    )
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )


def get_llm():
    return AzureChatOpenAI(
        temperature=0,
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        model=os.getenv("AZURE_OPENAI_MODEL_NAME")
    )


# ── File Impact Analysis Functions ────────────────────────────────────────
# File paths are structural identifiers, not semantic concepts.
# Embeddings cannot reliably match "src/billing/billing_utils.py" across
# documents. These functions use deterministic set-intersection instead.

def extract_files_from_error_log(error_log):
    """Parse file paths from error log tracebacks and messages."""
    file_pattern = r'((?:src|tests|lib|app)/[\w/]+\.(?:py|yaml|json|yml|js|ts|cfg))'
    matches = re.findall(file_pattern, error_log)
    return set(m.replace('\\', '/') for m in matches)


def extract_files_from_feature_branch(feature_branch):
    """Collect all files touched or referenced by the feature branch."""
    files = set()
    for commit in feature_branch['commits']:
        for f in commit['files_changed']:
            files.add(f.replace('\\', '/'))
        diff_files = re.findall(
            r'((?:src|tests|lib|app)/[\w/]+\.(?:py|yaml|json|yml|js|ts|cfg))',
            commit['diff']
        )
        files.update(f.replace('\\', '/') for f in diff_files)
    return files


def compute_file_impact_scores(main_commits, impacted_files):
    """
    Score each commit by file-path overlap with impacted files.
    Exact match = 3 pts, same directory = 1 pt, reference in diff = 0.5 pt.
    """
    impacted_dirs = set(os.path.dirname(f) for f in impacted_files)
    scored = []
    for i, commit in enumerate(main_commits):
        score = 0
        matched_files = []
        commit_files = [f.replace('\\', '/') for f in commit['files_changed']]
        for cf in commit_files:
            if cf in impacted_files:
                score += 3
                matched_files.append(f"{cf} (EXACT MATCH)")
            elif os.path.dirname(cf) in impacted_dirs:
                score += 1
                matched_files.append(f"{cf} (same directory)")
        diff_text = commit.get('diff', '')
        for impacted_file in impacted_files:
            basename = os.path.basename(impacted_file).replace('.py', '')
            if basename in diff_text and all(cf not in impacted_files for cf in commit_files):
                score += 0.5
                matched_files.append(f"references '{basename}' in diff")
        scored.append({
            'commit_index': i, 'commit': commit,
            'file_impact_score': score, 'matched_files': matched_files,
        })
    scored.sort(key=lambda x: x['file_impact_score'], reverse=True)
    return scored


def hybrid_merge(file_impact_results, semantic_results, main_commits, top_n=8):
    """Merge file-impact + semantic scores: 0.4 * file + 0.6 * semantic."""
    file_scores = {}
    max_file_score = max((r['file_impact_score'] for r in file_impact_results), default=1) or 1
    for r in file_impact_results:
        h = r['commit']['hash']
        file_scores[h] = {
            'raw_score': r['file_impact_score'], 'normalized': r['file_impact_score'] / max_file_score,
            'matched_files': r['matched_files'], 'commit': r['commit'],
        }
    semantic_ranks = {}
    for rank, doc in enumerate(semantic_results):
        h = doc.metadata['commit_hash']
        semantic_ranks[h] = {
            'rank': rank, 'normalized': 1.0 - (rank / max(len(semantic_results), 1)), 'doc': doc,
        }
    all_hashes = set(file_scores.keys()) | set(semantic_ranks.keys())
    combined = []
    for h in all_hashes:
        fs = file_scores.get(h, {'raw_score': 0, 'normalized': 0, 'matched_files': [], 'commit': None})
        ss = semantic_ranks.get(h, {'rank': -1, 'normalized': 0, 'doc': None})
        hybrid_score = 0.4 * fs['normalized'] + 0.6 * ss['normalized']
        commit = fs['commit'] or next((c for c in main_commits if c['hash'] == h), None)
        combined.append({
            'commit_hash': h, 'commit': commit,
            'file_impact_score': fs['raw_score'], 'file_impact_normalized': fs['normalized'],
            'matched_files': fs['matched_files'],
            'semantic_rank': ss['rank'], 'semantic_normalized': ss['normalized'],
            'hybrid_score': round(hybrid_score, 3),
            'in_semantic_results': ss['rank'] >= 0, 'in_file_impact': fs['raw_score'] > 0,
            'doc': ss.get('doc'),
        })
    combined.sort(key=lambda x: x['hybrid_score'], reverse=True)
    return combined[:top_n]


def format_candidate_commits_hybrid(hybrid_results):
    """Format hybrid-ranked candidates with file-impact data for LLM."""
    formatted = []
    for i, entry in enumerate(hybrid_results, 1):
        commit = entry['commit']
        matched_str = ", ".join(entry['matched_files']) if entry['matched_files'] else "None"
        semantic_str = f"Rank #{entry['semantic_rank']+1}" if entry['in_semantic_results'] else "Not in top semantic results"
        if entry['doc']:
            diff_content = entry['doc'].page_content
        else:
            diff_content = f"Commit Hash: {commit['hash']}\nMessage: {commit['message']}\nFiles Changed: {', '.join(commit['files_changed'])}\n\nCODE DIFF:\n{commit['diff']}"
        formatted.append(f"""### Candidate #{i} (Hybrid Score: {entry['hybrid_score']})
- **Commit:** {commit['hash']}
- **Author:** {commit['author']}
- **Date:** {commit['date']}
- **Message:** {commit['message']}
- **Files Changed:** {', '.join(commit['files_changed'])}
- **FILE IMPACT SCORE:** {entry['file_impact_score']:.1f} — Matched: [{matched_str}]
- **Semantic Retrieval:** {semantic_str}

**Diff:**
```
{diff_content}
```
""")
    return "\n---\n".join(formatted)


def format_feature_diff_summary(feature_branch):
    summaries = []
    for commit in feature_branch['commits']:
        summaries.append(f"**{commit['message']}**\n```\n{commit['diff'][:800]}\n```")
    return "\n\n".join(summaries)


# ── Prompts and Retrieval ────────────────────────────────────────────────

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


def build_retrieval_query(merge_failure, feature_branch):
    return f"""
Merge failure in telco billing system.
Feature branch: {feature_branch['branch_name']} by {feature_branch['developer']}
Feature description: {feature_branch['description']}

Error log summary:
{merge_failure['error_log'][:1500]}

Affected files: {', '.join(merge_failure['affected_files_in_feature'])}
"""


# ── Streamlit UI ──────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Merge Conflict Analyzer",
    page_icon="🔍",
    layout="wide"
)

st.title("Merge Conflict Root Cause Analyzer")
st.markdown(
    "**Hybrid AI tool** that identifies which commit on `main` broke your feature branch after merge. "
    "Combines **deterministic file-impact analysis** with **semantic RAG retrieval** and **LLM reasoning**."
)

# Load data
data = load_scenario_data()
feature_branch = data['feature_branch']
main_commits = data['main_branch_commits']
merge_failure = data['merge_failure']
ground_truth = data['ground_truth']

# ── Sidebar: Scenario Overview ────────────────────────────────────────────

st.sidebar.header("Scenario Overview")
st.sidebar.markdown(f"**Scenario:** {data['scenario']}")
st.sidebar.markdown("---")

st.sidebar.subheader("Feature Branch")
st.sidebar.markdown(f"**Branch:** `{feature_branch['branch_name']}`")
st.sidebar.markdown(f"**Developer:** {feature_branch['developer']}")
st.sidebar.markdown(f"**Commits:** {len(feature_branch['commits'])}")
st.sidebar.markdown(f"_{feature_branch['description']}_")

st.sidebar.markdown("---")
st.sidebar.subheader("Main Branch")
st.sidebar.markdown(f"**Commits since branch-off:** {len(main_commits)}")
st.sidebar.markdown(f"**Authors:** {len(set(c['author'] for c in main_commits))}")

st.sidebar.markdown("---")
st.sidebar.subheader("How It Works")
st.sidebar.markdown("""
1. **File Impact Analysis** — deterministic path overlap scoring
2. **Semantic Retrieval** — ChromaDB embedding similarity
3. **Hybrid Merge** — 40% file + 60% semantic
4. **LLM Analysis** — chain-of-thought ranking
""")

# ── Main Content: Tabs ────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "Merge Failure",
    "Hybrid Analysis (File Impact + RAG)",
    "Ground Truth",
    "Commit Browser"
])

# ── Tab 1: Merge Failure Details ──────────────────────────────────────────

with tab1:
    st.header("Merge Failure Details")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Source Branch", feature_branch['branch_name'])
    with col2:
        st.metric("Target Branch", merge_failure['target_branch'])
    with col3:
        st.metric("Status", merge_failure['merge_status'])

    st.subheader("Error Log")
    st.code(merge_failure['error_log'], language="text")

    st.subheader("Feature Branch Commits")
    for commit in feature_branch['commits']:
        with st.expander(f"[{commit['hash']}] {commit['message']}"):
            st.markdown(f"**Author:** {commit['author']} | **Date:** {commit['date']}")
            st.markdown(f"**Files:** {', '.join(commit['files_changed'])}")
            st.code(commit['diff'], language="diff")

# ── Tab 2: RAG Analysis ──────────────────────────────────────────────────

with tab2:
    st.header("Hybrid Root Cause Analysis (File Impact + RAG)")

    st.markdown("""
    **Pipeline:**

    1. **File Impact Analysis** (deterministic) — exact path matching between commit files and error/feature files
    2. **Semantic Retrieval** (embedding-based) — ChromaDB cosine similarity on diff content
    3. **Hybrid Merge** — weighted combination (40% file-impact + 60% semantic)
    4. **LLM Chain-of-Thought** — deep analysis on top-ranked candidates

    _File paths are structural identifiers, not semantic concepts. Embeddings alone
    cannot reliably match `billing_utils.py` across documents. The file-impact step
    provides a deterministic signal that complements semantic search._
    """)

    k_value = st.slider(
        "Number of commits to retrieve (Top-K)",
        min_value=3, max_value=15, value=8,
        help="How many candidate commits to retrieve from the vector store"
    )

    if st.button("Run Analysis", type="primary"):

        # Step 1: File Impact Analysis
        with st.spinner("Step 1/4: Running file impact analysis..."):
            error_files = extract_files_from_error_log(merge_failure['error_log'])
            feature_files = extract_files_from_feature_branch(feature_branch)
            impacted_files = error_files | feature_files
            file_impact_results = compute_file_impact_scores(main_commits, impacted_files)

        st.subheader("Step 1: File Impact Analysis")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Files extracted from error log:**")
            for f in sorted(error_files):
                st.code(f, language="text")
        with col_b:
            st.markdown("**Files from feature branch (changed + imported):**")
            for f in sorted(feature_files):
                st.code(f, language="text")

        st.markdown("**File impact scores (commits with overlapping files):**")
        has_impact = False
        for r in file_impact_results:
            if r['file_impact_score'] > 0:
                has_impact = True
                c = r['commit']
                st.markdown(
                    f"- `{c['hash']}` **score={r['file_impact_score']:.1f}** — "
                    f"{c['author']} — _{c['message']}_ — "
                    f"Matched: {', '.join(r['matched_files'])}"
                )
        if not has_impact:
            st.info("No commits have direct file overlap (all scores = 0)")

        # Step 2: Semantic Retrieval
        with st.spinner("Step 2/4: Retrieving semantically similar commits from ChromaDB..."):
            vector_store = get_vector_store()
            query = build_retrieval_query(merge_failure, feature_branch)
            semantic_results = vector_store.as_retriever(
                search_type='similarity',
                search_kwargs={'k': k_value}
            ).invoke(query)

        st.markdown("---")
        st.subheader("Step 2: Semantic Retrieval (ChromaDB)")
        for i, doc in enumerate(semantic_results, 1):
            meta = doc.metadata
            st.markdown(
                f"**#{i}** `{meta['commit_hash']}` — "
                f"{meta['author']} — _{meta['message']}_"
            )

        # Step 3: Hybrid Merge
        hybrid_results = hybrid_merge(file_impact_results, semantic_results, main_commits, top_n=k_value)

        st.markdown("---")
        st.subheader("Step 3: Hybrid Ranking (40% file-impact + 60% semantic)")
        for i, entry in enumerate(hybrid_results, 1):
            c = entry['commit']
            signals = []
            if entry['in_file_impact']:
                signals.append(f"file-impact={entry['file_impact_score']:.1f}")
            if entry['in_semantic_results']:
                signals.append(f"semantic=#{entry['semantic_rank']+1}")
            signal_str = " | ".join(signals) if signals else "low signal"
            st.markdown(
                f"**#{i}** `{c['hash']}` **hybrid={entry['hybrid_score']:.3f}** "
                f"({signal_str}) — {c['author']} — _{c['message']}_"
            )

        # Step 4: LLM Analysis
        with st.spinner("Step 4/4: Running LLM chain-of-thought analysis..."):
            prompt = ChatPromptTemplate.from_template(ANALYSIS_PROMPT)
            chain = prompt | get_llm() | StrOutputParser()

            analysis = chain.invoke({
                "branch_name": feature_branch['branch_name'],
                "developer": feature_branch['developer'],
                "feature_description": feature_branch['description'],
                "feature_diff_summary": format_feature_diff_summary(feature_branch),
                "error_log": merge_failure['error_log'],
                "candidate_commits": format_candidate_commits_hybrid(hybrid_results),
            })

        # Display Results
        st.markdown("---")
        st.subheader("Step 4: LLM Root Cause Analysis")
        st.markdown(analysis)

        # Store in session for comparison
        st.session_state['analysis_result'] = analysis
        st.session_state['hybrid_results'] = hybrid_results

# ── Tab 3: Ground Truth ──────────────────────────────────────────────────

with tab3:
    st.header("Ground Truth (for validation)")
    st.markdown("_This tab reveals the actual culprit commits, used to validate the RAG analysis._")

    st.subheader("Primary Culprit")
    gt_primary = ground_truth['primary_culprit']
    st.error(f"**Commit:** `{gt_primary['commit_hash']}` by **{gt_primary['author']}**")
    st.markdown(f"**Reason:** {gt_primary['reason']}")

    # Show the actual diff
    primary_commit = next(c for c in main_commits if c['hash'] == gt_primary['commit_hash'])
    with st.expander("View Commit Diff"):
        st.code(primary_commit['diff'], language="diff")

    st.subheader("Secondary Culprit")
    gt_secondary = ground_truth['secondary_culprit']
    st.warning(f"**Commit:** `{gt_secondary['commit_hash']}` by **{gt_secondary['author']}**")
    st.markdown(f"**Reason:** {gt_secondary['reason']}")

    secondary_commit = next(c for c in main_commits if c['hash'] == gt_secondary['commit_hash'])
    with st.expander("View Commit Diff"):
        st.code(secondary_commit['diff'], language="diff")

    # Compare with analysis if available
    if 'analysis_result' in st.session_state:
        st.markdown("---")
        st.subheader("Validation")
        analysis = st.session_state['analysis_result']
        found_primary = gt_primary['commit_hash'] in analysis
        found_secondary = gt_secondary['commit_hash'] in analysis

        col1, col2 = st.columns(2)
        with col1:
            if found_primary:
                st.success(f"Primary culprit `{gt_primary['commit_hash']}` was identified in the analysis")
            else:
                st.error(f"Primary culprit `{gt_primary['commit_hash']}` was NOT found")
        with col2:
            if found_secondary:
                st.success(f"Secondary culprit `{gt_secondary['commit_hash']}` was identified in the analysis")
            else:
                st.warning(f"Secondary culprit `{gt_secondary['commit_hash']}` was not in top results")

# ── Tab 4: Commit Browser ────────────────────────────────────────────────

with tab4:
    st.header("Main Branch Commit Browser")
    st.markdown(f"Browse all **{len(main_commits)}** commits on main between branch-off and merge.")

    for i, commit in enumerate(main_commits):
        # Highlight the guilty commits
        is_primary = commit['hash'] == ground_truth['primary_culprit']['commit_hash']
        is_secondary = commit['hash'] == ground_truth['secondary_culprit']['commit_hash']

        prefix = ""
        if is_primary:
            prefix = "🔴 "
        elif is_secondary:
            prefix = "🟡 "

        with st.expander(
            f"{prefix}#{i+1} [{commit['hash']}] {commit['author']} — {commit['message']}",
            expanded=is_primary
        ):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Author:** {commit['author']}")
            with col2:
                st.markdown(f"**Date:** {commit['date']}")
            with col3:
                st.markdown(f"**Files:** {', '.join(commit['files_changed'])}")

            if is_primary:
                st.error("PRIMARY CULPRIT — This commit changed the `calculate_line_item_charge()` function signature")
            elif is_secondary:
                st.warning("SECONDARY CULPRIT — This commit restructured the billing config format")

            st.code(commit['diff'], language="diff")
