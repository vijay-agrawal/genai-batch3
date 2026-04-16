# Azure Retrieval-Augmented Generation (RAG) Architecture and Implementation

This document provides a comprehensive overview of Azure offerings for Retrieval-Augmented Generation (RAG), comparing different implementation options and providing step-by-step instructions for each.

---

## 1. Azure Offerings for RAG

Azure provides several overlapping services to implement RAG. The choice depends on the required level of control, coding effort, and integration complexity.

### A. Azure AI Search (The Core Engine)
Formerly Azure Cognitive Search, this is the backbone for most RAG solutions on Azure. It provides a high-performance vector database, keyword search, and hybrid search capabilities.
- **Index:** A physical data structure that holds searchable content.
- **Skillsets:** AI transformations (OCR, translation, entity extraction) applied during ingestion.
- **Vector Store:** Native support for storing and searching high-dimensional embeddings.

### B. Azure AI Foundry Knowledge Bases
Azure AI Foundry (formerly AI Studio) offers a "Knowledge Base" abstraction. It simplifies the setup of RAG by automating the connection between data sources (like Blob Storage) and AI Search.
- **Foundry IQ:** Represents the intelligence layer within AI Foundry that orchestrates data chunking and vectorization automatically.

### C. Integration with AI Agents
Azure AI Foundry Agents allow you to attach a Knowledge Base as a **Tool**. When a user asks a question, the agent decides when to query the search index to ground its answer in your private data.

---

## 2. Comparison of RAG Options

| Option | Approach | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Option 1: AI Foundry (Knowledge Base)** | Low-code, UI-driven integration within AI Foundry. | Fastest setup; auto-chunking; built-in evaluation tools. | Less control over indexing logic and specific chunking strategies. |
| **Option 2: Custom AI Search Indexing** | Developer-centric using Search SDKs or Portal Indexers. | Maximum control over skillsets, custom chunking, and metadata. | Higher complexity; requires manual management of vectorization. |
| **Option 3: "On Your Data" (Azure OpenAI)** | Direct integration in the AOAI Playground. | One-click deployment to a web app; easiest for testing. | Harder to scale into complex multi-agent workflows. |

---

## 3. Implementation Steps: Option 1 (Azure AI Foundry Knowledge Base)

This is the recommended path for most enterprise RAG applications using the modern Azure AI stack.

### Step A: Upload Documents to Azure Blob Storage
1. Log in to the [Azure Portal](https://portal.azure.com).
2. Create a **Storage Account** (or use an existing one).
3. Navigate to **Containers** and create a new container (e.g., `rag-data`).
4. Click **Upload** and select your PDF, Word, or Markdown files.

### Step B: The Indexing Flow (AI Foundry)
1. Go to [Azure AI Foundry](https://ai.azure.com).
2. Create a new **Project**.
3. In the left navigation, select **Knowledge Base** (under "My Assets").
4. Click **+ Create Knowledge Base**.
5. **Connect Data:** Select "Azure Blob Storage" and point to your `rag-data` container.
6. **Indexing Settings:**
   - **Chunking:** Choose "Fixed-size" (e.g., 1024 tokens) or "Markdown-aware".
   - **Vectorization:** Select an embedding model (e.g., `text-embedding-3-small`).
   - **Metadata:** The system automatically maps file names and paths as metadata.
7. Click **Create** to trigger the ingestion job. This creates the AI Search index automatically.

### Step C: Retrieval Flow (Agentic / API)
1. **Agentic:**
   - In AI Foundry, go to **Agents**.
   - Create an Agent and click **+ Add Tool**.
   - Select the **Knowledge Base** you just created.
   - The agent will now automatically use this data to answer queries.
2. **Expose as API:**
   - Deploy the Agent to an **Endpoint**.
   - You will receive a REST API endpoint and Key to integrate into your front-end application.

---

## 4. Implementation Steps: Option 2 (Manual AI Search Integration)

Use this if you need custom processing (e.g., complex OCR or specific metadata enrichment).

### Step A: Upload Documents
*Same as Option 1 (Azure Blob Storage).*

### Step B: The Indexing Flow (Custom)
1. Go to your **Azure AI Search** resource in the portal.
2. Select **Import and vectorize data**.
3. **Data Source:** Connect to your Blob Storage container.
4. **Vectorization:** Select your Azure OpenAI resource and the embedding model.
5. **Advanced Content Extraction:** - Enable "Optical Character Recognition (OCR)" if files are scanned PDFs.
   - Add "Skillsets" to extract key phrases or entities to be stored as metadata for filtering.
6. **Schedule:** Set the indexer to run "Once" or "Daily" to sync new files.

### Step C: Retrieval Flow (App / API)
1. **App Integration:** - Use the `azure-search-documents` library in Python.
   - Code snippet for Hybrid Search:
     ```python
     results = search_client.search(
         search_text="How do I reset my password?",
         vector_queries=[VectorizableTextQuery(text="How do I reset my password?", k_nearest_neighbors=3, fields="vector")],
         select=["title", "content", "metadata_storage_path"]
     )
     ```
2. **Web App Deployment:**
   - In Azure AI Studio / OpenAI Studio, use the **"Deploy to a web app"** button. This creates a pre-configured React app hosted on Azure App Service that uses the index.

---

## 5. Integration Summary: AI Search + Agents

When building sophisticated RAG, use the following architectural pattern:

1. **Storage:** Blob Storage (Source of truth).
2. **Intelligence:** Azure AI Search (Hybrid retrieval).
3. **Orchestration:** **Azure AI Foundry Agents**. 
   - Connect the AI Search index as a **Vector Store Tool**.
   - The Agent uses its reasoning capability to decide if a query needs "Private Data" (Search Tool) or "General Knowledge."

---
*End of Documentation*
