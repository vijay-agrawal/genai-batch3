# Azure RAG: Architecture Guide

This guide covers the two recommended ways to implement Retrieval-Augmented Generation (RAG) on Azure, grounded in the demos in this folder. The **data/** directory contains the actual documents used throughout — resume PDFs, a financial statement, and regulatory/policy documents.

---

## Data in This Project

### `data/` folder contents

| File | Type | Key metadata |
|---|---|---|
| `kunal.pdf` | Resume | candidate_name: Kunal Sharma |
| `pankaj_cv.pdf` | Resume | candidate_name: Pankaj Gupta |
| `pooja.pdf` | Resume | candidate_name: Pooja Mehta |
| `rahul.pdf` | Resume | candidate_name: Rahul Verma |
| `hdfc_financial_statement_2024.pdf` | Financial statement | company: HDFC, year: 2024 |
| `electricity_bill.pdf` | Utility bill | doc_type: utility |
| `rbi_risk_basel_extracts.md` | Regulatory | doc_type: regulation, category: risk |
| `Bank Market Risk Policy.md` | Policy | doc_type: policy, category: market_risk |
| `VAR Backtesting policy.md` | Policy | doc_type: policy, category: var |
| `regulations.docx` | Regulatory | doc_type: regulation |
| `regulations2.docx` | Regulatory | doc_type: regulation |

### Metadata registry (from `rag_metadatafilter_demo.py`)

```python
CANDIDATE_REGISTRY = {
    "kunal":     {"name": "Kunal Sharma",  "linkedin": "https://www.linkedin.com/in/kunal-sharma"},
    "pankaj_cv": {"name": "Pankaj Gupta",  "linkedin": "https://www.linkedin.com/in/pankaj-gupta"},
    "pooja":     {"name": "Pooja Mehta",   "linkedin": "https://www.linkedin.com/in/pooja-mehta"},
    "rahul":     {"name": "Rahul Verma",   "linkedin": "https://www.linkedin.com/in/rahul-verma"},
}

DOC_TYPE_REGISTRY = {
    "hdfc_financial_statement_2024": {"doc_type": "financial", "company": "HDFC", "year": 2024},
    "rbi_risk_basel_extracts":       {"doc_type": "regulation", "category": "risk"},
    "Bank Market Risk Policy":       {"doc_type": "policy",     "category": "market_risk"},
    "VAR Backtesting policy":        {"doc_type": "policy",     "category": "var"},
    "regulations":                   {"doc_type": "regulation"},
    "regulations2":                  {"doc_type": "regulation"},
    "electricity_bill":              {"doc_type": "utility"},
}
```

---

## Azure AI Offerings Overview

Azure RAG is composed of three distinct layers: where documents live, how they get indexed, and how they get retrieved. Understanding which service fills each role — and what it costs — is essential before choosing your architecture.

---

### Data Storage

| Service | What it is | Cost Factor | Typical Use Cases |
|---|---|---|---|
| **Azure Blob Storage** | Object storage for files (PDFs, DOCX, Markdown, images) | **Least expensive** — ~$0.018/GB/month (hot tier); effectively free for small document sets like this demo | Primary document repository; feeds all downstream indexing pipelines; durable, versioned source-of-truth for all RAG architectures |

Blob Storage is the starting point for both options in this guide. Cost is negligible at demo scale; even at 10 GB it is less than $0.20/month.

---

### Indexing

| Service | What it is | Cost Factor | Typical Use Cases |
|---|---|---|---|
| **Azure AI Foundry Knowledge Base** | Fully managed RAG data store inside Foundry — handles chunking, embedding, and indexing automatically, backed by AI Search under the hood | **Moderate / pay-per-use** — you pay for embedding tokens during ingestion (typically a few cents for this demo); no persistent search SKU fee; effectively serverless at rest | Best-fit for most RAG workloads: fast UI-driven setup, no index schema to design, built-in test panel, production-ready without operational overhead |
| **Azure AI Search** | Managed search service with vector, keyword, and hybrid search; supports OData metadata filtering and semantic ranking | **Expensive / always-on** — billed **per hour from creation regardless of query volume**; Basic ~$74/month, Standard S1 ~$730/month; no pause, sleep, or scale-to-zero option | Enterprise-scale RAG needing fine-grained OData filters, semantic ranking tuning, existing search infrastructure, or Prompt Flow evaluation pipelines |

---

### Retrieval

| Service | What it is | Cost Factor | Typical Use Cases |
|---|---|---|---|
| **Foundry KB "Test" panel** | Built-in test UI inside the Knowledge Base — enter a query, see retrieved chunks, scores, and source metadata; supports filter expressions | **Free** (included in any Foundry project) | Validate KB quality before deploying an agent; iterate on chunk size and metadata; no code needed — ideal for rapid feedback loops |
| **Azure AI Foundry Agents** | Agent framework that automatically decides when to call the KB or AI Search, handles multi-turn conversation, and supports additional tools (code interpreter, functions) | **Moderate** — pay per token for Azure OpenAI model calls; agent orchestration itself adds negligible overhead | End-to-end conversational RAG; multi-turn Q&A across document types; combining retrieval with code execution (e.g., computing financial ratios from retrieved numbers) |

---

## Recommended Options

Two architectures cover the vast majority of RAG needs. **Option 1 is recommended for most teams** — lower cost, less setup, and equivalent retrieval quality for the document set in this project.

---

## Option 1 — Azure Blob Storage + Foundry Knowledge Base + Agent (Recommended)

**Architecture:** `data/*.pdf` → Blob Storage → Foundry Knowledge Base (chunking + embedding + indexing) → Foundry Agent → Grounded response

**Why choose this:** Fully managed end-to-end. No index schema to design, no search SKU billing around the clock. The built-in Test panel lets you validate retrieval quality before deploying an agent.

### Step 1 — Upload documents to Blob Storage

1. **portal.azure.com** → create or open a **Storage Account**.
2. Create a **Blob Container** (e.g., `hr-docs`).
3. Upload all files from `data/`: resumes, `hdfc_financial_statement_2024.pdf`, policy `.md` files, `.docx` regulation files.

### Step 2 — Create an Azure AI Foundry Project

1. Go to **ai.azure.com** → **+ New project**.
2. **Project name**: `hr-docs-rag`. Select or create a Hub (provisions Azure OpenAI in the same resource group).
3. **Region**: East US (or same region as your Azure OpenAI resource).
4. Click **Create project** (~3 minutes).

### Step 3 — Create the Knowledge Base

1. Left sidebar → **Knowledge bases** (under **Build**) → **+ New knowledge base**.
2. **Name**: `hr-docs-kb`.
3. **Description**: `Resumes for Kunal, Pankaj, Pooja, Rahul; HDFC financial statement 2024; RBI Basel extracts; bank market risk and VAR backtesting policies`.
4. **Embedding model**: `text-embedding-3-small`.
5. Click **Next**.
6. **Data source**: point to the `hr-docs` Blob container (or upload files directly).
7. Click **Next**.
8. **Chunking method**: Fixed-size, **chunk size**: 500 tokens, **overlap**: 50 tokens. Parse mode: `auto`.
9. Click **Next**.
10. Add **Metadata fields**:

    | Field | Type | Filterable | Retrievable |
    |---|---|---|---|
    | `candidate_name` | String | ✓ | ✓ |
    | `linkedin_url` | String | — | ✓ |
    | `doc_type` | String | ✓ | ✓ |
    | `company` | String | ✓ | ✓ |
    | `year` | Integer | ✓ | ✓ |
    | `category` | String | ✓ | ✓ |
    | `filename` | String | ✓ | ✓ |

11. Tag each uploaded document with its metadata values (e.g., `kunal.pdf` → `candidate_name=Kunal Sharma`, `doc_type=resume`).
12. Click **Create**. Wait for status → **Ready** (~2–5 minutes).

### Step 4 — Test retrieval in the KB "Test" panel

The Test panel is the fastest way to validate your KB before wiring up an agent. Use it to catch chunking or metadata issues early.

1. Open `hr-docs-kb` → click **Test**.
2. Run sample queries:
   - `What are Pankaj's technical skills?` — expect chunks from `pankaj_cv.pdf`
   - `Net profit in HDFC 2024` — expect chunks from `hdfc_financial_statement_2024.pdf`
   - `VAR backtesting confidence level` — expect chunks from `VAR Backtesting policy.md`
3. Click **Advanced options** → add a filter expression: `doc_type eq 'resume' and candidate_name eq 'Rahul Verma'` → confirm only Rahul's chunks appear.
4. Adjust chunk size or metadata and re-ingest if results look off — doing this here is far cheaper than debugging inside an agent.

### Step 5 — Create a Foundry Agent

1. Left sidebar → **Agents** → **+ New agent**.
2. **Agent name**: `HR & Finance RAG Agent`.
3. **Model deployment**: `gpt-4o` or `gpt-4o-mini`.
4. **Temperature**: `0`.
5. **Instructions**:
   ```
   You are an expert HR assistant and financial analyst.

   For candidate/resume questions, use the knowledge base and filter by
   candidate_name when a specific person is mentioned. Always cite the
   candidate's name and LinkedIn URL when available.

   For financial questions about HDFC, filter by doc_type=financial.

   For risk, policy, or regulatory questions, filter by doc_type=policy
   or doc_type=regulation and use the category field when relevant
   (market_risk, var, risk).

   Always cite the source filename and page number in your response.
   ```
6. **Tools** → **+ Add tool** → **Knowledge base** → select `hr-docs-kb`.
   - Max retrieval results: `5`
   - Semantic search: ON
   - Enable metadata filtering: ON
7. Optionally add **Code Interpreter** (lets the agent write Python to compute ratios from retrieved HDFC numbers).
8. Test multi-turn queries in the agent playground:
   ```
   User: Compare the technical skills of Kunal and Pankaj.
   User: Which of them has more experience?
   User: What does the HDFC annual report say about capital adequacy?
   User: How does that compare to the RBI Basel requirements?
   ```

### Step 6 — Deploy as API

1. **Deploy** → **Deploy as API**. Note the Agent ID.
2. Call from Python:
   ```python
   from azure.ai.projects import AIProjectClient
   from azure.identity import DefaultAzureCredential

   client = AIProjectClient.from_connection_string(
       conn_str=os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"),
       credential=DefaultAzureCredential()
   )
   agent  = client.agents.get_agent(agent_id="your-agent-id")
   thread = client.agents.create_thread()
   client.agents.create_message(
       thread_id=thread.id, role="user",
       content="What are Pooja Mehta's key strengths based on her resume?"
   )
   run  = client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)
   msgs = client.agents.list_messages(thread_id=thread.id)
   print(msgs.data[0].content[0].text.value)
   ```

---

## Option 2 — Azure Blob Storage + Azure AI Search + Agent

**Architecture:** `data/*.pdf` → Blob Storage → Azure AI Search Index (vector + OData metadata fields) → Foundry Agent (via AI Search connection) → Grounded response

> ### Cost Caveat — Read Before Provisioning
>
> **Azure AI Search is not serverless and not on-demand.** It bills by the hour from the moment the resource is created — regardless of whether a single search query is ever made. There is **no pause, sleep, or scale-to-zero option**.
>
> | Tier | Hourly rate | Monthly cost (24/7) | Notes |
> |---|---|---|---|
> | **Free** | $0 | $0 | 50 MB storage, 3 indexes, no vector search, no SLA — for this demo only |
> | **Basic** | ~$0.101/hr | **~$74/month** | 2 GB storage, 15 indexes, 1 replica — minimum paid tier |
> | **Standard S1** | ~$1.006/hr | **~$730/month** | 25 GB storage, 50 indexes, production SLA |
> | **Standard S2/S3** | $2–$6+/hr | $1,400–$4,300+/month | High-scale enterprise |
>
> **Repercussions of always-on billing:**
> - A Basic resource left running for a month costs ~$74 even with zero searches, zero documents, and zero users.
> - Standard S1 costs ~$730/month whether you run 1 query or 10 million.
> - Adding replicas (for high availability) or partitions (for larger indexes) multiplies these costs proportionally — 2 replicas on Standard S1 = ~$1,460/month.
> - Teams used to serverless or consumption-based Azure services (Functions, Container Apps) are frequently surprised by this billing model.
>
> **Workarounds:**
> - **Use the Free tier** for this demo and early prototyping. Hard limits apply (no vector search on Free) — but it is genuinely free.
> - **Delete the resource when not in use.** Export your index schema (JSON from the portal) first, so you can recreate it later. This is the only true way to stop billing — there is no pause button.
> - **Automate teardown with Azure CLI** — a simple script can delete the resource at end of day and recreate + re-index from Blob Storage in the morning using a saved indexer definition. This is operationally complex but eliminates overnight charges for dev environments.
> - **Prefer Option 1** for any workload that doesn't require custom OData compound filters or enterprise-scale semantic ranking tuning. Foundry Knowledge Base achieves equivalent RAG quality at a fraction of the operational cost and management overhead.

**When to choose Option 2 over Option 1:** You need OData compound metadata filters (`candidate_name eq 'Kunal' and year gt 2022`), fine-grained semantic ranking control, integration with an existing AI Search index, or Prompt Flow evaluation pipelines.

### Step 1 — Create Azure AI Search resource

1. **portal.azure.com** → **Create a resource** → search `Azure AI Search` → **Create**.
2. **Pricing tier**: `Free` for this demo; `Basic` for persistent dev use.
3. **Region**: same as your Azure OpenAI resource (East US recommended).
4. Click **Review + create** → **Create** (~2 minutes).
5. **Billing starts immediately upon creation.**

### Step 2 — Upload documents to Blob Storage

Same as Option 1 Step 1 — create an `hr-docs` container and upload all `data/` files.

### Step 3 — Create the Index schema

1. AI Search resource → **Indexes** → **+ Add index** → **Index name**: `hr-docs-index`.
2. Add fields:

   | Field name | Type | Retrievable | Filterable | Searchable |
   |---|---|---|---|---|
   | `id` | Edm.String | ✓ | — | — |
   | `content` | Edm.String | ✓ | — | ✓ |
   | `filename` | Edm.String | ✓ | ✓ | — |
   | `candidate_name` | Edm.String | ✓ | ✓ | ✓ |
   | `linkedin_url` | Edm.String | ✓ | — | — |
   | `doc_type` | Edm.String | ✓ | ✓ | — |
   | `company` | Edm.String | ✓ | ✓ | — |
   | `year` | Edm.Int32 | ✓ | ✓ | — |
   | `category` | Edm.String | ✓ | ✓ | — |
   | `page_number` | Edm.Int32 | ✓ | ✓ | — |
   | `content_vector` | Collection(Edm.Single) | — | — | — |

3. For `content_vector`: enable **Vector search**, Dimensions `1536`, Algorithm HNSW (`m=4`, `efConstruction=400`).
4. **Vector Search** tab → add a **Vectorizer** pointing to your `text-embedding-3-small` Azure OpenAI deployment.
5. Click **Save**.

### Step 4 — Import data from Blob Storage

1. Index page → **Import data** → **Data source**: `Azure Blob Storage` → select the `hr-docs` container.
2. Enable **Extract text from images (OCR)** if needed for scanned PDFs.
3. **Indexer name**: `hr-docs-indexer`. Schedule: `Once`.
4. Click **Submit** and wait for completion.
5. Verify in **Search explorer** → run `*` → confirm all documents appear.

### Step 5 — Enrich metadata (one-time Python script)

The blob indexer doesn't know that `kunal.pdf` maps to "Kunal Sharma". Run this once after indexing:

```python
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

CANDIDATE_REGISTRY = {
    "kunal.pdf":     {"candidate_name": "Kunal Sharma",  "doc_type": "resume", "linkedin_url": "https://www.linkedin.com/in/kunal-sharma"},
    "pankaj_cv.pdf": {"candidate_name": "Pankaj Gupta",  "doc_type": "resume", "linkedin_url": "https://www.linkedin.com/in/pankaj-gupta"},
    "pooja.pdf":     {"candidate_name": "Pooja Mehta",   "doc_type": "resume", "linkedin_url": "https://www.linkedin.com/in/pooja-mehta"},
    "rahul.pdf":     {"candidate_name": "Rahul Verma",   "doc_type": "resume", "linkedin_url": "https://www.linkedin.com/in/rahul-verma"},
    "hdfc_financial_statement_2024.pdf": {"doc_type": "financial", "company": "HDFC", "year": 2024},
}

client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name="hr-docs-index",
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY"))
)
results = client.search("*", select=["id", "filename"])
updates = [
    {"id": doc["id"], **CANDIDATE_REGISTRY.get(doc.get("filename", ""), {"doc_type": "other"})}
    for doc in results
]
client.merge_documents(documents=updates)
```

### Step 6 — Test retrieval in Search Explorer

1. AI Search resource → **Search explorer** → **JSON view**.
2. Query for a specific candidate:
   ```json
   {
     "search": "technical skills programming languages",
     "vectorQueries": [{"kind": "text", "text": "technical skills programming languages", "fields": "content_vector", "k": 5}],
     "filter": "candidate_name eq 'Kunal Sharma'",
     "select": "candidate_name,filename,page_number,content",
     "top": 5
   }
   ```
3. Query for financial documents:
   ```json
   {
     "search": "net profit revenue 2024",
     "vectorQueries": [{"kind": "text", "text": "net profit revenue 2024", "fields": "content_vector", "k": 5}],
     "filter": "doc_type eq 'financial' and year eq 2024",
     "select": "filename,company,year,content",
     "top": 5
   }
   ```

### Step 7 — Connect AI Search to a Foundry Agent

1. **ai.azure.com** → your project → **Settings** → **Connections** → **+ New connection** → **Azure AI Search**.
2. **Name**: `hr-docs-search-connection`. Enter your AI Search endpoint and admin API key.
3. Create a Foundry Agent (same instructions as Option 1 Step 5), but under **Tools** add an **Azure AI Search** tool (not Knowledge Base), pointing to `hr-docs-index` via `hr-docs-search-connection`.
4. Test and deploy as in Option 1 Step 6.

---

## Comparison

| | Option 1 — Foundry KB + Agent | Option 2 — AI Search + Agent |
|---|---|---|
| **Setup complexity** | Low — UI-driven, no schema design | High — manual index schema, vectorizer, metadata enrichment script |
| **Cost model** | Serverless / pay-per-use | Always-on hourly billing from day 1 |
| **Minimum monthly cost** | ~$0 at rest (only embedding token cost during ingestion) | ~$74/mo (Basic) to ~$730/mo (Standard S1) |
| **Metadata filtering** | Basic field match | Full OData (`eq`, `gt`, `lt`, `and`, `or`, compound expressions) |
| **Semantic ranking** | Built-in | Configurable but requires Standard tier |
| **Test UI** | Built-in KB Test panel with filter support | Search Explorer in portal (JSON queries) |
| **Vector search on free tier** | Yes | No (Free tier does not support vector search) |
| **Best for** | Most RAG workloads; dev, staging, and production | Enterprise, fine-grained OData filters, existing AI Search indexes |

---

## Metadata Filtering Reference

| Use case | Foundry KB / AI Search OData filter |
|---|---|
| Specific candidate | `candidate_name eq 'Kunal Sharma'` |
| All resumes | `doc_type eq 'resume'` |
| HDFC financials | `doc_type eq 'financial'` |
| Policy + regulation (AI Search only — compound OR) | `doc_type eq 'policy' or doc_type eq 'regulation'` |
| VAR policy only | `doc_type eq 'policy' and category eq 'var'` |
| Risk docs | `doc_type eq 'regulation' and category eq 'risk'` |

---

## Chunking Strategy for This Dataset

| Document type | File(s) | Chunk size | Overlap |
|---|---|---|---|
| Resume PDFs (short, structured) | `kunal.pdf`, `pankaj_cv.pdf`, `pooja.pdf`, `rahul.pdf` | 500 tokens | 50 tokens |
| Multi-page financial report | `hdfc_financial_statement_2024.pdf` | 1000 tokens | 200 tokens |
| Policy markdown | `Bank Market Risk Policy.md`, `VAR Backtesting policy.md` | 512 tokens | 64 tokens |
| Regulatory extracts | `rbi_risk_basel_extracts.md` | 512 tokens | 64 tokens |
| Word documents | `regulations.docx`, `regulations2.docx` | 1000 tokens | 200 tokens |

---

## Key Environment Variables Reference

### Azure OpenAI (both options)
```
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/v1
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_MODEL_NAME=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://<resource>.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings
AZURE_OPENAI_EMBEDDING_API_KEY=<key>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-small
```

### Azure AI Search (Option 2 only)
```
AZURE_SEARCH_ENDPOINT=https://hr-docs-search.search.windows.net
AZURE_SEARCH_API_KEY=<admin-or-query-key>
AZURE_SEARCH_INDEX_NAME=hr-docs-index
```

### Azure AI Foundry (both options)
```
AZURE_AI_PROJECT_CONNECTION_STRING=<region>.api.azureml.ms;<subscription-id>;<resource-group>;<project-name>
```

---

## Ingestion Flow Summary

```
data/ folder
├── kunal.pdf, pankaj_cv.pdf, pooja.pdf, rahul.pdf   (resumes)
├── hdfc_financial_statement_2024.pdf                 (financial)
├── Bank Market Risk Policy.md                        (policy)
├── VAR Backtesting policy.md                         (policy)
├── rbi_risk_basel_extracts.md                        (regulation)
├── regulations.docx, regulations2.docx               (regulation)
└── electricity_bill.pdf                              (utility)
         │
         ▼
  Azure Blob Storage  (hr-docs container)
         │
         ├─── Option 1: Foundry Knowledge Base ──────────────────────────┐
         │       Chunk → Embed (text-embedding-3-small) → Index          │
         │       Test panel (validate retrieval, no code needed)         │
         │       → Foundry Agent → Grounded response                     │
         │                                                                │
         └─── Option 2: Azure AI Search ──────────────────────────────── ┘
                 Blob Indexer → hr-docs-index (vector + OData fields)
                 + one-time metadata enrichment script
                 → Foundry Agent (AI Search connection)
                 → Grounded response
```
