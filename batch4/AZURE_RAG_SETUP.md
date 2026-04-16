# AZURE_RAG.md

## Azure RAG in the Portal: Options, Trade-offs, and Step-by-Step Implementation

_Last updated: 2026-04-16_

This guide explains the main **Azure portal / Microsoft Foundry portal options** for implementing Retrieval-Augmented Generation (RAG) on Azure, with special focus on:

- **Azure AI Search index**
- **Azure AI Search knowledge base**
- **Foundry IQ knowledge bases**
- **How Azure AI Search and knowledge bases integrate with Foundry Agent Service**
- End-to-end steps for:
  - uploading files to **Azure Blob Storage**
  - indexing flow (**chunking, vectorization, metadata**)
  - retrieval flow (**app / API / agentic exposure**)

---

## 1) First, understand the Azure building blocks

### A. Azure AI Search index
An **Azure AI Search index** is the searchable store that holds your chunked text, metadata, and optionally vectors. It is the core data plane for classic search and classic RAG.

Typical fields in an index for RAG:
- `chunk_id`
- `parent_id` or `document_id`
- `title`
- `source_path` / `url`
- `content`
- `content_vector`
- metadata fields such as `file_name`, `created_at`, `department`, `acl`, `tags`

Use this when you want:
- maximum control over schema
- custom retrieval logic
- classic app/API-based RAG
- direct integration with Foundry Agent Service using the **Azure AI Search tool**

---

### B. Azure AI Search knowledge base
A **knowledge base in Azure AI Search** is a **top-level object for agentic retrieval**. It orchestrates retrieval over one or more **knowledge sources**. At query time, the `retrieve` method targets the knowledge base, which can do query planning / decomposition and multi-source retrieval.

Important point:

- The **knowledge base is not a replacement for storage/search indexes**
- It is an orchestration layer above knowledge sources
- Those knowledge sources can be:
  - an existing Azure AI Search index
  - Azure Blob Storage (which can generate downstream search objects)
  - other supported indexed/remote sources depending on current support

Use this when you want:
- agentic retrieval
- richer retrieval orchestration than plain “search this one index”
- a cleaner handoff to **Foundry Agent Service**

---

### C. Foundry IQ knowledge base
**Foundry IQ** is the managed knowledge layer in Microsoft Foundry for enterprise data. In practice, it is the **agent-facing knowledge experience** that connects agents to reusable, permission-aware knowledge.

Important relationship:
- **Foundry IQ is not a totally separate search engine from Azure AI Search**
- The current Azure guidance positions **Azure AI Search knowledge bases and knowledge sources** as the retrieval substrate
- In the Foundry portal, you can create or connect to these knowledge bases and then attach them to agents

So, from an architecture standpoint:

- **Azure AI Search index** = searchable chunk/vector store
- **Azure AI Search knowledge base** = retrieval orchestration layer
- **Foundry IQ knowledge base experience** = managed Foundry-facing layer for agents and reusable enterprise knowledge

---

### D. Foundry Agent Service integrations
There are two major integration patterns with agents:

#### Pattern 1: Agent + Azure AI Search tool
You connect an agent directly to **one Azure AI Search index**.

Good for:
- simple and controlled setups
- classic index-based grounding
- cases where you already built your index

Limits:
- targets **one index**
- less retrieval abstraction than knowledge-base-based approach

#### Pattern 2: Agent + Foundry IQ / Azure AI Search knowledge base
You connect the agent to a **knowledge base**. The knowledge base exposes the `knowledge_base_retrieve` MCP tool for agent integration.

Good for:
- agentic retrieval
- multiple sources / reusable knowledge layer
- better long-term architecture for agents

---

## 2) Recommended Azure portal options for RAG

Below are the most practical options you can achieve through Azure / Foundry portal experiences.

---

## Option 1 — Classic RAG with Azure Blob Storage -> Azure AI Search index -> your app/API

### What it is
You upload documents to **Azure Blob Storage**, use **Azure AI Search** to index them (often with integrated vectorization), and your application queries the index directly using search APIs. Your app then sends retrieved chunks to an LLM.

### Best for
- production teams that want **full control**
- non-agent chatbot / API apps
- hybrid retrieval with your own orchestration
- deterministic architectures

### Pros
- most control over schema, chunking strategy, filters, ranking, and prompting
- works well with existing application code
- easy to expose as REST API, backend service, or chat app
- supports classic vector and hybrid retrieval
- typically the clearest path for enterprise-grade governance

### Cons
- you build and maintain the orchestration yourself
- multi-step retrieval logic is your responsibility
- citations, multi-query decomposition, and agent behaviors need to be implemented in your app layer unless added separately

### When to prefer it
Choose this when:
- you already have backend code
- you want fine-grained control over retrieval and prompt construction
- you do not need Foundry agents immediately
- GA/stable patterns matter more than the newest retrieval abstraction

---

## Option 2 — Azure Blob Storage -> Azure AI Search knowledge source + knowledge base -> retrieve API / MCP / agents

### What it is
You still start from Blob Storage, but instead of thinking only in terms of “build an index and query it,” you define a **knowledge source** and a **knowledge base** in Azure AI Search. For blob sources, Azure AI Search can automatically generate the underlying objects:
- data source
- skillset
- index
- indexer

The knowledge base then orchestrates **agentic retrieval** over that source.

### Best for
- teams that want Azure-managed retrieval orchestration
- enterprise agentic RAG
- scenarios where you want a more future-facing Azure pattern without fully hand-coding orchestration

### Pros
- higher-level abstraction than raw index-based RAG
- good fit for agentic retrieval
- Azure manages more of the indexing plumbing
- easier connection to Foundry Agent Service
- supports knowledge-base retrieval via APIs or MCP

### Cons
- newer pattern; some pieces may be preview depending on exact feature path and API surface
- less low-level control than hand-built classic RAG
- terminology and portal flows are evolving

### When to prefer it
Choose this when:
- you want Azure to manage more of the retrieval stack
- you plan to use agents
- you want a knowledge-base-centric architecture instead of hardwiring agents to one index

---

## Option 3 — Existing Azure AI Search index -> Foundry Agent Service using Azure AI Search tool

### What it is
You create and manage your own Azure AI Search index, then attach it to an agent using the **Azure AI Search tool**.

### Best for
- teams that already have a good index
- simple grounding for a Foundry agent
- one-index agent solutions

### Pros
- simple bridge from classic RAG to agents
- reuse your existing index
- easy to validate citations from indexed content
- keeps the retrieval layer understandable

### Cons
- the tool can only target **one index**
- less flexible than a knowledge base for multi-source retrieval
- not the cleanest long-term abstraction if you expect many sources or reusable knowledge layers

### When to prefer it
Choose this when:
- you already built the index
- you want the quickest path from index to agent
- one index is enough

---

## Option 4 — Foundry IQ knowledge base -> Foundry Agent Service

### What it is
You use the Foundry portal’s **Foundry IQ** experience to create or connect knowledge bases and then connect them to agents.

### Best for
- reusable knowledge shared by many agents
- enterprise teams standardizing on Foundry
- permission-aware knowledge experiences

### Pros
- best conceptual fit for “enterprise knowledge layer for agents”
- reusable across multiple agents
- aligns with Microsoft’s newer agent architecture direction
- cleaner separation between knowledge and agent logic

### Cons
- under the hood still relies on Azure AI Search knowledge concepts for indexed enterprise retrieval
- some configurations still require understanding Azure AI Search resources, permissions, and networking
- preview surfaces may evolve

### When to prefer it
Choose this when:
- you want a strategic agent platform approach
- multiple agents will consume the same knowledge
- you want a reusable knowledge layer, not app-specific retrieval code

---

## 3) Decision guide

### Choose Option 1 if:
- you want **maximum control**
- you are exposing RAG through your own backend / API / web app
- you do not need agentic retrieval immediately

### Choose Option 2 if:
- you want **knowledge-base-driven retrieval**
- you expect to use agents or MCP-based retrieval later
- you want Azure-managed retrieval orchestration

### Choose Option 3 if:
- you already have an index
- you want the **fastest agent integration**
- one index is enough

### Choose Option 4 if:
- you are standardizing on Foundry agents
- you want a reusable knowledge layer across many agents
- permission-aware enterprise knowledge is important

---

# 4) Step-by-step implementation

---

## Option 1 Step-by-Step
## Blob Storage -> Azure AI Search index -> API / app / chatbot

### Step 1: Create storage and upload documents
1. In the **Azure portal**, create or open a **Storage Account**.
2. Go to **Data storage -> Containers**.
3. Create a container, for example `rag-docs`.
4. Open the container and click **Upload**.
5. Upload PDFs, Word files, HTML, text files, or other supported content.

**Notes**
- Keep a clean folder convention such as:
  - `hr/policies/...`
  - `finance/reports/...`
  - `legal/contracts/...`
- Good naming improves downstream metadata handling.

---

### Step 2: Create Azure AI Search service
1. In the Azure portal, create an **Azure AI Search** resource.
2. Choose region, pricing tier, networking, and identity model.
3. If using private networking, plan permissions carefully for indexers and agent integrations.

---

### Step 3: Import and vectorize data
Use the **Import data** wizard in Azure AI Search portal.

1. Open your search service.
2. Choose **Import data** / **Import and vectorize data**.
3. Select **Azure Blob Storage** as the data source.
4. Point to your storage account + container.
5. Configure extraction / enrichment:
   - text extraction from documents
   - chunking
   - optional embeddings generation via integrated vectorization
6. Choose or create embedding connections, typically Azure OpenAI.

---

### Step 4: Define chunking strategy
Azure AI Search integrated vectorization can chunk content during indexing.

Recommended practical chunking guidance:
- Start with **semantic or layout-aware chunking** if your documents are long and structured.
- For simpler docs, use moderate text chunks.
- Preserve enough local context to answer questions, but avoid huge chunks.

Recommended chunk metadata per chunk:
- `chunk_id`
- `document_id`
- `file_name`
- `title`
- `source_path` or `source_url`
- `page_number` where possible
- `section_heading`
- `last_modified`
- `department` / `document_type` / `tags`
- ACL/security metadata if needed

Why this matters:
- filters become easier
- citations become cleaner
- parent-child reconstruction becomes possible
- you can route by document type or business unit

---

### Step 5: Define index schema
Your index should usually contain:

#### Required or common fields
- `id` (key)
- `content` (retrievable searchable text)
- `content_vector` (vector field)
- `title`
- `source_url` or `storage_path`
- `document_id`
- `metadata_json` or explicit metadata fields
- optional `acl`

#### Design tips
- Keep both **vector** and **human-readable text** fields
- Keep a **source URL / path** for citations
- Keep **parent document identifiers**
- Prefer explicit filterable metadata fields over dumping everything into one JSON blob

---

### Step 6: Run indexing
The indexer pulls from Blob Storage and populates the index.

Key concepts:
- **pull model**: AI Search indexer reads from Blob Storage
- change detection can pick up updated blobs on later runs
- schedules can be configured for periodic refresh

---

### Step 7: Query the index from your application
Your app can now call Azure AI Search using:
- keyword search
- vector search
- hybrid search
- semantic ranking where applicable

Typical RAG runtime:
1. User asks question
2. App sends query to Azure AI Search
3. Search returns top chunks + metadata
4. App constructs prompt with citations / sources
5. App sends prompt + retrieved context to model
6. App returns grounded answer

---

### Step 8: Expose retrieval as API / app
Common exposure patterns:
- backend API in Python / .NET / Node
- internal copilot web app
- Teams bot or internal portal
- function app / container app serving RAG

**Good pattern**
- split the system into:
  - ingestion pipeline
  - retrieval service
  - orchestration / prompt layer
  - UI or agent channel

---

### Option 1 Summary
This is the most controllable RAG pattern in Azure. Use it when you want classic, well-understood RAG and you are comfortable owning orchestration.

---

## Option 2 Step-by-Step
## Blob Storage -> Azure AI Search knowledge source + knowledge base -> retrieve API / MCP / agentic RAG

### Step 1: Upload documents to Azure Blob Storage
Same as Option 1:
1. Create/open Storage Account
2. Create container
3. Upload files

---

### Step 2: Create Azure AI Search service
Create or open an **Azure AI Search** resource.

---

### Step 3: Create a blob knowledge source
In the knowledge-source-based model, blob storage can be used as an **indexed knowledge source**.

For a blob knowledge source, Azure AI Search can automatically generate:
- the **data source**
- **skillset**
- **index**
- **indexer**

This is useful because you do not have to separately handcraft every object at the beginning.

---

### Step 4: Configure ingestion behavior
During knowledge source creation, configure:

#### a) Content extraction
- extract text from PDFs, Office docs, HTML, etc.

#### b) Chunking
- select chunking strategy appropriate for document size and structure
- preserve document identity and, where possible, page or section context

#### c) Vectorization
- optionally use Azure OpenAI-backed vectorization
- ensure query-time vectorization is aligned with index-time vectorization

#### d) Metadata
Capture:
- file path
- title
- source link
- modified date
- category
- department
- ACL / permission fields if required

---

### Step 5: Create the knowledge base
A **knowledge base** in Azure AI Search sits above one or more knowledge sources.

What the knowledge base does:
- stores retrieval defaults
- orchestrates retrieval pipeline
- supports **agentic retrieval**
- can be called via retrieval APIs or MCP-style integration

This is the key shift from “search my index” to “retrieve from my knowledge base”.

---

### Step 6: Test retrieval
Use the knowledge base retrieval API to validate:
- chunk relevance
- citations
- filters
- result completeness
- whether query decomposition helps for complex questions

---

### Step 7: Expose as API / app / MCP
You can expose this option in three ways:

#### A. App/API-based RAG
Your backend calls the knowledge base retrieval endpoint, then sends the returned grounding context to the model.

#### B. MCP-based retrieval
The knowledge base can be exposed through MCP-compatible tooling in the Azure agent ecosystem.

#### C. Agent integration
Attach the knowledge base to a Foundry agent for fully agentic retrieval.

---

### Step 8: Operational considerations
Best practices:
- version your prompts and retrieval settings
- test complex questions, not only simple keyword questions
- validate citations against source docs
- monitor retrieval latency and token usage
- track how chunk size affects answer quality

---

### Option 2 Summary
This is the stronger choice when you want Azure-managed, knowledge-base-centric RAG instead of wiring everything directly to one search index.

---

## Option 3 Step-by-Step
## Existing Azure AI Search index -> Foundry Agent Service with Azure AI Search tool

### Step 1: Build or reuse your search index
You can arrive here from Option 1 or from a custom ingestion pipeline.

Make sure your index has:
- searchable text fields
- at least one vector field
- at least one retrievable text field for citations
- a source URL/path field
- title field if possible

---

### Step 2: Create a Microsoft Foundry project
1. Open Microsoft Foundry portal.
2. Create or open a **Foundry project**.
3. Ensure you have a deployed model such as an Azure OpenAI chat model.

---

### Step 3: Create a project connection to Azure AI Search
From the Foundry project:
1. Add a connection to your Azure AI Search service
2. Use key-based or managed-identity auth as appropriate
3. For private networking, prefer keyless/managed identity where required

---

### Step 4: Attach Azure AI Search tool to the agent
Configure the agent’s Azure AI Search tool with:
- project connection
- index name
- `top_k`
- query type, such as:
  - `vector`
  - `semantic`
  - `vector_simple_hybrid`
  - `vector_semantic_hybrid`

A strong default for many RAG cases is:
- `vector_semantic_hybrid`

---

### Step 5: Configure citations and retrieval behavior
To get good citations:
- keep a retrievable source field
- keep readable text fields
- keep title/source URL in index
- test that the cited snippets match user-visible document content

---

### Step 6: Test in Foundry playground
Ask questions that you know are answered by specific documents.
Validate:
- answer correctness
- citation formatting
- source URLs
- whether retrieval returns the right chunks

---

### Step 7: Expose the agent
You can then expose the Foundry agent as:
- an internal assistant
- application backend
- chat experience
- API-driven service

---

### Option 3 Summary
This is the quickest way to bring an existing Azure AI Search index into Foundry Agent Service. It is excellent for pragmatic “index to agent” use cases.

---

## Option 4 Step-by-Step
## Foundry IQ knowledge base -> Foundry Agent Service

### Step 1: Prepare knowledge source(s)
You can use:
- Azure AI Search-backed indexed knowledge sources
- Blob-based indexed knowledge sources
- other currently supported sources in Foundry IQ such as SharePoint, OneLake, or web, depending on your scenario and availability

---

### Step 2: Create or connect a knowledge base in Foundry IQ
In the Foundry portal:
1. Open the **Foundry IQ** area / knowledge experience
2. Create a knowledge base
3. Add one or more knowledge sources
4. Confirm permissions, network access, and identity setup

---

### Step 3: Ensure ingestion quality
Whether the source is Blob or an existing Search index, validate:
- chunk size and coherence
- vector generation
- metadata completeness
- ACL synchronization where needed
- document freshness / reindex cadence

---

### Step 4: Connect Foundry Agent Service to the knowledge base
A Foundry agent can use the knowledge base via the `knowledge_base_retrieve` MCP tool.

High-level flow:
1. Agent receives user request
2. Agent invokes knowledge base retrieve tool
3. Knowledge base performs query planning / decomposition and retrieval
4. Results come back with grounding context / citations
5. Agent generates final answer

---

### Step 5: Validate permissions and roles
Common checks:
- the Foundry project managed identity can read from Azure AI Search
- correct Search roles are assigned
- project and search resource are in compatible tenant/security configuration
- private networking is configured correctly

---

### Step 6: Test reusable enterprise patterns
This is where Foundry IQ becomes powerful:
- many agents can share the same knowledge base
- different agents can have different instructions while reusing the same enterprise knowledge layer
- knowledge can be governed centrally while behavior varies by agent

---

### Option 4 Summary
This is the most strategic Azure direction for enterprise agents that need reusable, governed knowledge rather than one-off app retrieval logic.

---

# 5) Indexing flow in Azure: what actually happens

Regardless of option, the indexing story usually follows this pattern.

## A. Source ingestion
Documents start in:
- Azure Blob Storage
- SharePoint
- OneLake
- existing search indexes
- or other supported sources

## B. Extraction
The system extracts text and sometimes layout/image-derived content from source files.

## C. Chunking
Large documents are split into chunks because:
- embedding models have token limits
- retrieval works better on focused segments
- citations are more precise

## D. Metadata propagation
Metadata is attached to chunks or mapped into fields:
- file-level metadata
- parent-child relationships
- page or section context
- security/ACL fields
- category/tag fields

## E. Vectorization
Embeddings are generated for chunk text:
- at indexing time
- sometimes also at query time through integrated vectorization

## F. Index storage
Chunks + vectors + metadata are stored in the index.

## G. Retrieval
At query time you use:
- keyword
- vector
- hybrid
- semantic ranking
- or agentic retrieval via knowledge base

---

# 6) Metadata design recommendations

Do **not** stop at only `content` and `content_vector`.

Recommended metadata layers:

## Document-level metadata
- `document_id`
- `title`
- `file_name`
- `source_url`
- `created_at`
- `last_modified`
- `document_type`
- `business_unit`

## Chunk-level metadata
- `chunk_id`
- `chunk_number`
- `page_number`
- `section_heading`
- `token_count`
- `parent_id`

## Security metadata
- `acl_users`
- `acl_groups`
- `tenant_id`
- sensitivity label

## Why this matters
Good metadata enables:
- better filtering
- cleaner citations
- better debugging
- easier UI display
- access control enforcement
- document reconstruction

---

# 7) Agentic vs non-agentic retrieval

## Non-agentic retrieval
Typical classic RAG:
- one query in
- one retrieval call
- top-k chunks returned
- LLM answers

Good for:
- simpler apps
- predictable latency
- lower complexity

## Agentic retrieval
More advanced flow:
- system can decompose the query
- retrieval can fan out across sources/subqueries
- agent/tool loop can reason before answering

Good for:
- more complex enterprise questions
- multi-hop retrieval
- reusable agent patterns

Trade-off:
- usually more abstraction and sometimes more moving parts

---

# 8) Practical pros/cons table

| Option | Portal path | Best for | Pros | Cons |
|---|---|---|---|---|
| Option 1: Blob -> AI Search index -> app/API | Azure portal | Classic RAG apps | Maximum control, stable architecture, custom orchestration | You own retrieval orchestration and citations |
| Option 2: Blob -> knowledge source + knowledge base | Azure portal / Search knowledge objects | Managed agentic retrieval | Higher-level abstraction, easier future agent integration | Newer pattern, evolving surfaces |
| Option 3: Existing index -> Foundry agent with AI Search tool | Foundry portal + Search | Fastest index-to-agent route | Reuses existing index, simple setup | One index per tool, less reusable than knowledge bases |
| Option 4: Foundry IQ knowledge base -> Foundry agent | Foundry portal | Enterprise reusable knowledge for agents | Strategic, reusable, permission-aware | Requires understanding Foundry + Search + roles/networking |

---

# 9) Suggested recommendation by scenario

## Scenario A: “I want a production chatbot/API and I need control”
Use **Option 1**.

## Scenario B: “I want Azure to manage retrieval more intelligently”
Use **Option 2**.

## Scenario C: “I already have a good AI Search index and want a Foundry agent quickly”
Use **Option 3**.

## Scenario D: “I want a shared enterprise knowledge layer for many agents”
Use **Option 4**.

---

# 10) Recommended implementation sequence for most teams

A practical sequence for many enterprises is:

1. Start with **Blob Storage**
2. Build an **Azure AI Search index** using integrated vectorization
3. Validate retrieval quality with classic app/API RAG
4. If agents are needed, first attach the index directly to a Foundry agent
5. Then move to a **knowledge base / Foundry IQ** model when you need:
   - multi-source retrieval
   - reusable enterprise knowledge
   - more agentic patterns

This sequence reduces risk because you first validate the underlying retrieval quality before increasing orchestration complexity.

---

# 11) Key pitfalls to avoid

- Creating vectors but forgetting retrievable human-readable text fields
- Not storing a source URL/path for citations
- Overlarge chunks that reduce precision
- Missing page/section metadata for documents where citations matter
- Storing all metadata in one JSON field instead of filterable fields
- Not testing role/network access early, especially with Foundry agents
- Using agent abstractions before validating the base search quality
- Assuming Foundry IQ removes the need to understand Azure AI Search fundamentals

---

# 12) Bottom line

The **Azure AI Search index** remains the foundational retrieval store for Azure RAG.

The newer layers are:
- **Azure AI Search knowledge base** for **agentic retrieval orchestration**
- **Foundry IQ** as the **managed knowledge layer / agent-facing experience**
- **Foundry Agent Service** as the consumer of either:
  - a direct Azure AI Search index, or
  - a knowledge base

In practice:

- If you want **control**, start with **index-based RAG**
- If you want **agentic, reusable knowledge**, move toward **knowledge bases + Foundry IQ**

---

# References

Official Microsoft documentation used for this guide:

1. Azure AI Search RAG overview  
   https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview

2. Azure AI Search integrated vectorization  
   https://learn.microsoft.com/en-us/azure/search/vector-search-integrated-vectorization

3. Azure AI Search indexer overview  
   https://learn.microsoft.com/en-us/azure/search/search-indexer-overview

4. Azure AI Search knowledge base creation  
   https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-create-knowledge-base

5. Azure AI Search knowledge source overview  
   https://learn.microsoft.com/en-us/azure/search/agentic-knowledge-source-overview

6. Blob knowledge source for agentic retrieval  
   https://learn.microsoft.com/en-us/azure/search/agentic-knowledge-source-how-to-blob

7. Connect Azure AI Search index to Foundry agents  
   https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/ai-search

8. Connect agents to Foundry IQ knowledge bases  
   https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/foundry-iq-connect

9. What is Foundry IQ?  
   https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-foundry-iq

10. Foundry IQ FAQ  
    https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/foundry-iq-faq

11. Upload blobs in Azure portal  
    https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-portal

12. Azure AI Search import data wizard  
    https://learn.microsoft.com/en-us/azure/search/search-import-data-portal

13. Vector search quickstart in portal  
    https://learn.microsoft.com/en-us/azure/search/search-get-started-portal-import-vectors

14. Index projections  
    https://learn.microsoft.com/en-us/azure/search/search-how-to-define-index-projections