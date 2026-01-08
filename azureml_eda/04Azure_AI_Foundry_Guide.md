# Azure AI Foundry - Semantic Search for Healthcare Data

** Healthcare Training - Part 4: Semantic Search with Azure AI Foundry**

## Overview

This guide shows you how to implement semantic search using **Azure AI Foundry** (Azure AI Studio), Microsoft's unified platform for building AI applications with generative AI capabilities.

**What You'll Build:**
- AI-powered search using Azure OpenAI embeddings
- Vector-based semantic search with RAG (Retrieval Augmented Generation)
- Playground for testing queries
- API endpoints for integration
- Ground truth evaluation

**Time Required:** 2-3 hours

**Estimated Cost:** $2-5 for complete tutorial

---

## What is Azure AI Foundry?

### Azure AI Foundry (AI Studio) Overview

**Azure AI Foundry** is Microsoft's unified platform that combines:
- Azure OpenAI Service (GPT-4, embeddings)
- Azure AI Search (vector search)
- Prompt Flow (orchestration)
- Model catalog
- Evaluation tools

**Key Difference from Azure AI Search:**
- Uses **OpenAI embeddings** (text-embedding-ada-002 or text-embedding-3)
- Built-in **RAG (Retrieval Augmented Generation)**
- **Prompt engineering playground**
- **Model fine-tuning** capabilities
- **Unified interface** for all AI services

### Architecture Comparison

**Azure AI Search (Previous Guide):**
```
Data → Azure AI Search → Built-in semantic ranking → Results
```

**Azure AI Foundry (This Guide):**
```
Data → Azure OpenAI (embeddings) → Vector Index → 
Azure AI Search (vector storage) → RAG + GPT-4 → Results
```

---

## Prerequisites

### Required

- Azure subscription with access to:
  - Azure OpenAI Service (requires application approval)
  - Azure AI Services
- Dataset: `healthcare_data_enhanced.json`
- Web browser

### Cost Requirements

- **Azure AI Foundry:** Pay-as-you-go (no base cost)
- **Azure OpenAI:** 
  - Embeddings: $0.0001 per 1K tokens (~$0.10 for this dataset)
  - GPT-4 queries: $0.03 per 1K tokens
- **Azure AI Search:** Basic tier ($75/month, pro-rated)
- **Total for tutorial:** $2-5

### Important Notes

1. **Azure OpenAI Access:**
   - Requires application: https://aka.ms/oai/access
   - Approval takes 1-2 business days
   - Enterprise customers usually approved automatically

2. **Region Availability:**
   - Not all regions support all models
   - Recommended: East US, West Europe, or Sweden Central

---

## Architecture Overview

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure AI Foundry                         │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   AI Hub     │    │  AI Project  │    │ Prompt Flow  │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │Azure OpenAI  │    │  AI Search   │    │  Playground  │ │
│  │  Embeddings  │    │Vector Index  │    │   (Chat)     │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Upload:** Clinical notes uploaded to AI Studio
2. **Chunk:** Documents split into chunks
3. **Embed:** Azure OpenAI creates vector embeddings
4. **Index:** Vectors stored in Azure AI Search
5. **Query:** Natural language queries
6. **Retrieve:** Semantic search finds relevant chunks
7. **Generate:** GPT-4 generates answer (optional)

---

## Phase 1: Azure AI Foundry Setup

### Step 1.1: Access Azure AI Foundry

**Navigate to AI Studio:**

1. Go to https://ai.azure.com
2. Sign in with Azure credentials
3. You'll see the Azure AI Foundry home page

**First-time setup:**
- Accept terms and conditions
- Select your subscription
- Choose default resource group (or create new)

### Step 1.2: Create AI Hub

**AI Hub = Shared resources for multiple projects**

1. Click **+ New AI hub** (top right)
2. Configure:

```
Basics:
├── Hub name: <your name>-healthcare-hub
├── Subscription: [Your subscription]
├── Resource group: rg-<your name>-ai-foundry (create new)
├── Location: East US (or region with OpenAI access)
└── Connect Azure AI services: New

Azure AI Services:
├── Name: <your name>-ai-services
├── Pricing tier: S0 (Standard)
└── Include Azure OpenAI: ✓ Yes

Storage:
├── Storage account: (auto-create) citiusaistorage
└── Use for: Data storage and logs

Key Vault:
└── (auto-create) <your name>-kv

Application Insights:
└── (auto-create) <your name>-insights
```

3. Click **Next: Review + Create**
4. Click **Create**
5. Wait 3-5 minutes for deployment

**Cost Note:** Hub creation itself is free; you pay for underlying services when used.

### Step 1.3: Verify AI Hub Creation

**Check hub status:**

1. Go to **Management** → **AI hubs**
2. You should see **<your name>-healthcare-hub**
3. Status: **Succeeded**
4. Click on it to view details

**Verify connected resources:**
- Azure OpenAI endpoint
- Azure AI Search
- Storage account
- Key Vault

---

## Phase 2: Create AI Project

### Step 2.1: Create Project

**Projects = Workspaces for specific AI applications**

1. In AI Studio, click **+ New project**
2. Or from Hub → **Projects** → **+ New project**

**Configure project:**

```
Project details:
├── Project name: <your name>-semantic-search
├── Hub: <your name>-healthcare-hub (select your hub)
└── Description: Semantic search for clinical notes
```

3. Click **Create**
4. Wait 30-60 seconds

**Navigate to project:**
- You'll automatically be taken to the project dashboard
- Bookmark: `https://ai.azure.com/projects/<your name>-semantic-search`

### Step 2.2: Project Overview

**Project dashboard sections:**

- **Playground:** Test chat and embeddings
- **Deployments:** Model deployments
- **Data + indexes:** Upload data, create indexes
- **Prompt flow:** Build AI workflows
- **Evaluation:** Test model performance
- **Deployments:** API endpoints

---

## Phase 3: Data Preparation & Upload

### Step 3.1: Prepare Data for AI Foundry

**AI Foundry works best with document formats:**
- PDF, TXT, MD, DOCX
- Or structured JSON with text fields

**Option 1: Convert to Individual Text Files (Recommended)**

Create a Python script `prepare_for_ai_studio.py`:

```python
import json
import os

# Load data
with open('healthcare_data_enhanced.json', 'r') as f:
    data = json.load(f)

# Create output directory
os.makedirs('clinical_notes_txt', exist_ok=True)

# Create one text file per visit
for patient in data['patients']:
    patient_id = patient['patient_id']
    patient_name = patient['demographics']['name']
    patient_age = patient['demographics']['age']
    
    for visit in patient['visits']:
        visit_id = visit['visit_id']
        
        # Create document content
        content = f"""Patient Information:
Patient ID: {patient_id}
Name: {patient_name}
Age: {patient_age}
Gender: {patient['demographics']['gender']}

Visit Information:
Visit ID: {visit_id}
Date: {visit['date']}
Department: {visit['department']}
Visit Type: {visit['type']}
Provider: {visit['provider']['name']} ({visit['provider']['specialty']})

Diagnoses:
{'; '.join([d['description'] for d in visit['diagnoses']])}

Clinical Notes:
{visit['clinical_notes']}

Vital Signs:
- Blood Pressure: {visit['vitals']['blood_pressure']}
- Heart Rate: {visit['vitals']['heart_rate']} bpm
- Temperature: {visit['vitals']['temperature']}°F
- BMI: {visit['vitals']['bmi']}
"""
        
        # Save as text file
        filename = f"{visit_id}_{patient_id}.txt"
        with open(f'clinical_notes_txt/{filename}', 'w') as f:
            f.write(content)

print(f"✓ Created {len(os.listdir('clinical_notes_txt'))} text files")
print(f"✓ Location: clinical_notes_txt/")
```

Run it:
```bash
python prepare_for_ai_studio.py
```

**Result:** 18 text files (one per visit)

**Option 2: Use JSON Directly**

Create `clinical_notes.jsonl` (JSON Lines format):

```python
import json

with open('healthcare_data_enhanced.json', 'r') as f:
    data = json.load(f)

with open('clinical_notes.jsonl', 'w') as out:
    for patient in data['patients']:
        for visit in patient['visits']:
            doc = {
                'id': visit['visit_id'],
                'patient_id': patient['patient_id'],
                'patient_name': patient['demographics']['name'],
                'content': f"{visit['clinical_notes']}\n\nDiagnoses: {'; '.join([d['description'] for d in visit['diagnoses']])}",
                'metadata': {
                    'date': visit['date'],
                    'department': visit['department'],
                    'age': patient['demographics']['age']
                }
            }
            out.write(json.dumps(doc) + '\n')

print("✓ Created clinical_notes.jsonl")
```

### Step 3.2: Upload Data to AI Studio

**Method 1: Upload via UI**

1. In your project → **Data + indexes** → **Data**
2. Click **+ New data**
3. Select **Upload files/folders**

**Configure upload:**

```
Data source:
├── Name: clinical-notes-data
├── Type: File
└── Description: Clinical notes from  Healthcare

Upload:
├── Source: Local files
└── Files: Select all .txt files from clinical_notes_txt/ folder
    (or clinical_notes.jsonl)
```

4. Click **Next**
5. Review and click **Create**
6. Wait for upload (30 seconds)

**Verify:**
- Go to **Data + indexes** → **Data**
- You should see **clinical-notes-data**
- Click to view uploaded files

**Method 2: Upload via Azure Storage Explorer**

1. Open Azure Storage Explorer
2. Connect to your AI Studio storage account (citiusaistorage)
3. Navigate to container (usually named with project GUID)
4. Create folder: `data/clinical_notes/`
5. Upload all text files

---

## Phase 4: Vector Index Creation

### Step 4.1: Create Vector Index

**Vector Index = Searchable database of embeddings**

1. In your project → **Data + indexes** → **Indexes**
2. Click **+ New index**

**Configure index:**

```
Index name: clinical-notes-vector-index

Data source:
├── Use existing data: ✓
└── Select: clinical-notes-data

Embeddings model:
├── Model: text-embedding-ada-002 (or text-embedding-3-small)
├── Deployment: Create new deployment
└── Deployment name: embeddings-ada-002

Index type:
└── Vector index (recommended)

Advanced settings:
├── Chunk size: 1000 tokens (default)
├── Chunk overlap: 100 tokens
└── Metadata fields: Include all
```

3. Click **Next: Review**
4. Click **Create**

**This process:**
- Deploys embedding model (if needed)
- Chunks documents into 1000-token pieces
- Creates embeddings for each chunk (using Azure OpenAI)
- Stores vectors in Azure AI Search
- Takes 2-5 minutes

**Monitor progress:**
- Status will show "Creating"
- Refresh page to see updates
- When complete: Status = "Succeeded"

### Step 4.2: Verify Index Creation

**Check index:**

1. **Data + indexes** → **Indexes**
2. Click on **clinical-notes-vector-index**
3. You should see:
   - Total chunks: ~20-30 (depending on chunking)
   - Embedding dimension: 1536 (for ada-002)
   - Status: Ready

**View sample embeddings:**
- Click **View data**
- See chunks with their metadata
- Each chunk has a 1536-dimensional vector (hidden)

---

## Phase 5: Deploy Search Endpoint

### Step 5.1: Test in Playground (Chat)

**Before deploying, test in playground:**

1. Go to **Playground** → **Chat**
2. Click **Add your data**
3. Select data source:

```
Data source: Azure AI Search
Index: clinical-notes-vector-index
Add data: ✓ Connected
```

4. **Setup:**
   - Retrieval mode: **Hybrid (vector + keyword)**
   - Top K: 5 (retrieve 5 most relevant chunks)

5. **Deploy chat model (if not already):**
   - Click **Deployments** → **+ Create new deployment**
   - Model: **gpt-4** or **gpt-35-turbo** (cheaper)
   - Deployment name: gpt-4-chat
   - Click **Create**

6. **Return to Playground:**
   - Select deployment: gpt-4-chat
   - Your data is connected

### Step 5.2: Test Queries in Playground

**Try natural language queries:**

**Query 1:**
```
How many patients have back pain?
```

**Expected response:**
```
Based on the clinical notes, I found 2-3 patients with back pain:
1. Thomas Anderson - presented with chronic lower back pain
2. [Patient name] - visited for lumbar strain
The clinical notes mention various terms like "lumbar discomfort," 
"lower back pain," and "spinal issues."
```

**Query 2:**
```
Which patients have respiratory issues?
```

**Query 3:**
```
Find all patients with muscle pain or fibromyalgia
```

**Query 4:**
```
Show me patients with chest discomfort
```

**Query 5:**
```
List patients who have headaches or migraines
```

**How it works:**
1. Your query is embedded using same model
2. Vector similarity search finds relevant chunks
3. GPT-4 reads chunks and generates answer
4. Citations show which documents were used

**View citations:**
- Each answer includes citations [doc1], [doc2]
- Click to see source chunks
- Verifies answer accuracy

### Step 5.3: Deploy as API Endpoint

**Create production endpoint:**

1. From Playground, click **Deploy**
2. Or go to **Deployments** → **+ New deployment**

**Configure deployment:**

```
Deployment type: Web app
Deployment name: clinical-search-api
Model deployment: gpt-4-chat
Data source: clinical-notes-vector-index

Web app settings:
├── Create new web app: ✓
├── Name: <your name>-clinical-search
├── Subscription: [Your subscription]
├── Resource group: rg-<your name>-ai-foundry
├── Region: East US
├── Pricing plan: Basic B1 (~$13/month, can stop when not used)
└── Enable chat history: ✓
```

3. Click **Deploy**
4. Wait 3-5 minutes for deployment

**Access deployed app:**
- You'll get a URL: `https://<your name>-clinical-search.azurewebsites.net`
- Open in browser
- You'll see a chat interface
- Try the same queries!

**Get API endpoint:**
1. Go to **Deployments** → **clinical-search-api**
2. Click **Test** or **Consume**
3. Copy:
   - **Endpoint URL**
   - **API Key**

---

## Phase 6: Query & Test

### Step 6.1: Advanced Playground Features

**Grounding with data:**

In Playground → **Chat**:

1. **System message customization:**
```
You are a healthcare data analyst assistant. 
Answer questions about patient clinical notes accurately.
Always cite your sources using document IDs.
If you don't find relevant information, say so clearly.
```

2. **Parameters:**
   - Temperature: 0.3 (more factual, less creative)
   - Max response: 800 tokens
   - Top P: 0.95
   - Frequency penalty: 0
   - Presence penalty: 0

3. **Retrieval settings:**
   - Strictness: 3 (medium - balance between recall and precision)
   - Retrieved documents: 5
   - Semantic ranker: Enabled

### Step 6.2: Evaluate Search Quality

**Use Evaluation feature:**

1. Go to **Evaluation** → **+ New evaluation**
2. Create test dataset:

```yaml
# test_queries.jsonl
{"query": "patients with back pain", "ground_truth": "Thomas Anderson, PT-2024-001"}
{"query": "respiratory complaints", "ground_truth": "Jennifer Thompson"}
{"query": "muscle aches or fibromyalgia", "ground_truth": "Linda Martinez, Rachel Kim"}
{"query": "chest discomfort cases", "ground_truth": "Michael Chen"}
{"query": "migraine or headache patients", "ground_truth": "Rachel Kim"}
```

3. **Run evaluation:**
   - Upload test queries
   - Automatic metrics:
     - Groundedness (answers based on retrieved docs)
     - Relevance (answer matches query)
     - Coherence (well-structured response)
     - Fluency (grammatical quality)

4. **View results:**
   - Overall score (0-5)
   - Per-query breakdown
   - Failed cases for review

### Step 6.3: Compare Retrieval Methods

**Test different retrieval modes:**

**Vector only:**
```
Retrieval type: Vector
Top K: 5
```

**Keyword only:**
```
Retrieval type: Keyword
Top K: 5
```

**Hybrid (recommended):**
```
Retrieval type: Hybrid (vector + keyword)
Top K: 5
```

**Compare results:**
- Hybrid typically gives best results
- Vector: Better for semantic similarity
- Keyword: Better for exact terms (e.g., medical codes)

---

## Phase 7: Python Integration

### Step 7.1: Install Azure AI SDK

```bash
pip install azure-ai-projects azure-ai-inference azure-identity
```

### Step 7.2: Python Search Client

**Create `ai_foundry_search.py`:**

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage

# Configuration
PROJECT_CONNECTION_STRING = "your-project-connection-string"  # From AI Studio
DEPLOYMENT_NAME = "gpt-4-chat"
INDEX_NAME = "clinical-notes-vector-index"

# Initialize client
credential = DefaultAzureCredential()
project_client = AIProjectClient.from_connection_string(
    conn_str=PROJECT_CONNECTION_STRING,
    credential=credential
)

# Get chat client
chat_client = project_client.inference.get_chat_completions_client()

def search_clinical_notes(query, top_k=5):
    """
    Search clinical notes using RAG.
    
    Args:
        query: Natural language query
        top_k: Number of documents to retrieve
    
    Returns:
        AI-generated response with citations
    """
    
    # Configure data source
    data_source = {
        "type": "azure_search",
        "parameters": {
            "endpoint": project_client.search_endpoint,
            "index_name": INDEX_NAME,
            "authentication": {
                "type": "api_key",
                "key": project_client.search_key
            },
            "top_n_documents": top_k,
            "query_type": "vector_simple_hybrid",
            "semantic_configuration": "default"
        }
    }
    
    # Create messages
    messages = [
        SystemMessage(
            content="You are a healthcare data analyst. "
                   "Answer questions about patient clinical notes. "
                   "Always cite your sources."
        ),
        UserMessage(content=query)
    ]
    
    # Get completion with grounding
    response = chat_client.complete(
        model=DEPLOYMENT_NAME,
        messages=messages,
        data_sources=[data_source],
        temperature=0.3,
        max_tokens=800
    )
    
    return response

def print_response(response):
    """Pretty print response with citations."""
    
    # Get message
    message = response.choices[0].message
    content = message.content
    
    print(f"\n{'='*80}")
    print("RESPONSE:")
    print(f"{'='*80}\n")
    print(content)
    
    # Get citations if available
    if hasattr(message, 'context') and message.context:
        citations = message.context.get('citations', [])
        if citations:
            print(f"\n{'='*80}")
            print("SOURCES:")
            print(f"{'='*80}\n")
            for i, citation in enumerate(citations, 1):
                print(f"{i}. {citation.get('filepath', 'Unknown')}")
                print(f"   Relevance: {citation.get('relevance_score', 'N/A')}")
                print()

# Example usage
if __name__ == "__main__":
    
    # Question 1: Back pain
    print("\n=== QUESTION 1: Patients with back pain ===")
    response = search_clinical_notes(
        "How many patients have back pain or lumbar issues?"
    )
    print_response(response)
    
    # Question 2: Respiratory
    print("\n=== QUESTION 2: Respiratory complaints ===")
    response = search_clinical_notes(
        "Which patients have respiratory issues or breathing problems?"
    )
    print_response(response)
    
    # Question 3: Multiple conditions
    print("\n=== QUESTION 3: Patients with both back and muscle pain ===")
    response = search_clinical_notes(
        "Find patients who have both back pain and muscle aches"
    )
    print_response(response)
```

### Step 7.3: Get Connection String

**Find your connection string:**

1. Go to your project in AI Studio
2. Click **Settings** (gear icon) → **Project properties**
3. Copy **Connection string**
4. It looks like:
   ```
   azureml://subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.MachineLearningServices/workspaces/<workspace>
   ```

**Alternative - Use direct API:**

```python
import os
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

# Direct endpoint approach
ENDPOINT = "https://<your name>-ai-services.openai.azure.com/"
API_KEY = "your-api-key"
DEPLOYMENT = "gpt-4-chat"

client = ChatCompletionsClient(
    endpoint=ENDPOINT,
    credential=AzureKeyCredential(API_KEY)
)
```

### Step 7.4: Jupyter Notebook Integration

**Create `ai_foundry_analysis.ipynb`:**

```python
# Cell 1: Setup
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_CONNECTION_STRING = "your-connection-string"

credential = DefaultAzureCredential()
project_client = AIProjectClient.from_connection_string(
    conn_str=PROJECT_CONNECTION_STRING,
    credential=credential
)

print("✓ Connected to AI Foundry project")
```

```python
# Cell 2: Define search function
def ai_search(query, top_k=5):
    """Wrapper for AI search."""
    chat_client = project_client.inference.get_chat_completions_client()
    
    response = chat_client.complete(
        model="gpt-4-chat",
        messages=[{"role": "user", "content": query}],
        data_sources=[{
            "type": "azure_search",
            "parameters": {
                "endpoint": project_client.search_endpoint,
                "index_name": "clinical-notes-vector-index",
                "top_n_documents": top_k
            }
        }]
    )
    
    return response.choices[0].message.content

# Test
result = ai_search("patients with back pain")
print(result)
```

```python
# Cell 3: Answer all questions
questions = [
    "How many patients have back pain or lumbar issues?",
    "Which patients have respiratory complaints?",
    "Find patients with muscle pain or myalgia",
    "Show me cases of chest discomfort or chest pain",
    "List patients with headaches or migraines"
]

results = []

for i, question in enumerate(questions, 1):
    print(f"\n{'='*80}")
    print(f"Question {i}: {question}")
    print(f"{'='*80}\n")
    
    answer = ai_search(question, top_k=10)
    print(answer)
    
    results.append({
        'Question': question,
        'Answer': answer[:200] + "..."  # Truncate for display
    })

# Create summary
results_df = pd.DataFrame(results)
display(results_df)
```

```python
# Cell 4: Compare with direct vector search
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Direct search client (without GPT generation)
search_client = SearchClient(
    endpoint=project_client.search_endpoint,
    index_name="clinical-notes-vector-index",
    credential=AzureKeyCredential(project_client.search_key)
)

# Vector search only
query = "back pain"
vector_results = search_client.search(
    search_text=query,
    query_type="semantic",
    top=10
)

print("Direct vector search results (no GPT):")
for result in vector_results:
    print(f"  - Score: {result['@search.score']}")
    print(f"    Content: {result['content'][:100]}...")
    print()
```

---

## Phase 8: Advanced Features

### Step 8.1: Prompt Flow for Complex Workflows

**Create custom RAG flow:**

1. Go to **Prompt flow** → **+ Create**
2. Select template: **Chat with your data**
3. Name: `clinical-search-flow`

**Customize flow:**

```yaml
Flow steps:
1. Embed query (using text-embedding-ada-002)
2. Search vector index
3. Rerank results (semantic ranker)
4. Generate prompt with context
5. Call GPT-4 for answer
6. Post-process response
7. Return JSON with answer + citations
```

**Benefits:**
- Full control over RAG pipeline
- Add custom logic (e.g., filter by date)
- A/B test different prompts
- Log all steps for debugging

### Step 8.2: Fine-tuning (Optional)

**Fine-tune GPT-3.5 on medical terminology:**

1. **Prepare training data:**
   - Format: JSON Lines
   - Example:
   ```json
   {"messages": [{"role": "system", "content": "You are a medical assistant"}, {"role": "user", "content": "What is lumbar pain?"}, {"role": "assistant", "content": "Lumbar pain refers to lower back pain..."}]}
   ```

2. **Upload training data:**
   - Go to **Data + indexes** → **Data**
   - Upload training JSONL file

3. **Create fine-tuning job:**
   - **Model catalog** → **gpt-35-turbo**
   - Click **Fine-tune**
   - Select training data
   - Configure hyperparameters
   - Start training (takes 1-2 hours)

4. **Deploy fine-tuned model:**
   - After training completes
   - Deploy as new endpoint
   - Use in place of base GPT-3.5

**Cost:** ~$8-20 for training this dataset

### Step 8.3: Model Monitoring

**Set up monitoring:**

1. Go to **Monitoring** → **Model monitoring**
2. Enable for your deployment
3. View metrics:
   - Request count
   - Latency (p50, p95, p99)
   - Token usage
   - Error rate
   - Cost per request

**Set alerts:**
- High latency (>5 seconds)
- High error rate (>5%)
- High cost (>$10/day)

---

## Cost Analysis

### Detailed Pricing Breakdown

**Azure AI Foundry Components:**

```
1. Azure OpenAI Service:
   ├── Embeddings (text-embedding-ada-002):
   │   ├── Cost: $0.0001 per 1K tokens
   │   ├── This dataset: ~100K tokens = $0.01
   │   └── Indexing (one-time): $0.01
   │
   ├── GPT-4 Queries:
   │   ├── Input: $0.03 per 1K tokens
   │   ├── Output: $0.06 per 1K tokens
   │   ├── Per query (avg): ~500 input + 200 output = $0.027
   │   └── 50 queries for testing: $1.35
   │
   └── GPT-3.5-Turbo (cheaper alternative):
       ├── Input: $0.0005 per 1K tokens
       ├── Output: $0.0015 per 1K tokens
       ├── Per query: ~$0.00055
       └── 50 queries: $0.03

2. Azure AI Search:
   ├── Basic tier: $75/month = $0.10/hour
   ├── Vector storage: Included in tier
   ├── Testing time: 2 hours
   └── Cost: $0.20

3. Azure Web App (for deployed endpoint):
   ├── Basic B1: $13/month = $0.018/hour
   ├── Testing time: 2 hours
   └── Cost: $0.04

4. Storage (for data files):
   ├── Blob storage: $0.02/GB/month
   ├── Data size: 0.1 GB
   └── Cost: $0.002 (negligible)

TOTAL FOR TUTORIAL:
├── Embeddings (one-time): $0.01
├── GPT-4 queries (50): $1.35
├── AI Search (2 hours): $0.20
├── Web App (2 hours): $0.04
└── Total: ~$1.60
```

**Using GPT-3.5 instead of GPT-4:**
- Total: ~$0.30 (saves $1.00+)

### Cost Optimization Strategies

**1. Use GPT-3.5-Turbo for Testing**
```python
# Change deployment to gpt-35-turbo
# 50x cheaper than GPT-4
# Still good quality for most tasks
```

**2. Delete Resources After Learning**
```bash
# Stop Web App: $0/month
# Delete AI Search: $0/month
# Keep AI Hub: No base cost (pay-per-use)
```

**3. Use Smaller Embedding Model**
```python
# text-embedding-3-small (NEW)
# Cost: $0.00002 per 1K tokens (5x cheaper)
# Dimension: 1536 → 512 (smaller, faster)
```

**4. Optimize Chunk Size**
```python
# Smaller chunks = more embeddings = higher cost
# Larger chunks = fewer embeddings = lower cost
# Sweet spot: 1000-1500 tokens per chunk
```

**5. Batch Queries**
```python
# Instead of 50 individual queries
# Batch into 5 queries with 10 sub-questions each
# Saves on API overhead
```

### Cost Comparison

**AI Foundry vs Other Approaches:**

| Approach | Setup Cost | Per Query | 50 Queries | Monthly (Production) |
|----------|-----------|-----------|------------|---------------------|
| **AI Foundry + GPT-4** | $0.25 | $0.027 | **$1.60** | $90-150 |
| **AI Foundry + GPT-3.5** | $0.25 | $0.00055 | **$0.30** ✅ | $20-40 |
| Azure AI Search (prev guide) | $0.20 | $0 | **$0.20** | $75 |
| Azure ML + Transformers | $5-10 | $0 | **$5-10** | $50-100 |
| Custom OpenAI API | $0 | $0.03 | **$1.50** | Variable |

**Best Value:**
- **Learning:** AI Foundry + GPT-3.5 ($0.30)
- **Production (read-heavy):** Azure AI Search ($75/month flat)
- **Production (write-heavy):** AI Foundry + GPT-3.5 (pay per use)

---

## Phase 9: Cleanup & Cost Savings

### Step 9.1: Stop Billable Resources

**To minimize costs immediately:**

**1. Stop Web App:**
```bash
# Azure Portal → App Services → <your name>-clinical-search
# Click "Stop"
# Cost: $0 when stopped
```

**2. Pause AI Search:**
```bash
# Cannot pause, only delete
# Go to AI Search service → Delete
# Recreate when needed (data persists in storage)
```

**3. Keep AI Hub/Project:**
```bash
# AI Hub: No base cost
# Project: No base cost
# Only pay for API calls
# Safe to keep
```

### Step 9.2: Complete Cleanup

**Delete all resources:**

1. Azure Portal → Resource Groups
2. Select **rg-<your name>-ai-foundry**
3. Click **Delete resource group**
4. Type name to confirm
5. Click **Delete**

**This removes:**
- AI Hub
- AI Project
- Azure OpenAI
- AI Search
- Web App
- Storage
- All data

**Cost:** $0 ongoing

### Step 9.3: Keep Only What You Need

**Minimal cost setup:**

Keep:
- ✓ AI Hub (no base cost)
- ✓ AI Project (no base cost)
- ✓ Storage with data ($0.002/month)

Delete:
- ✗ Web App deployment
- ✗ AI Search service

**Cost:** ~$0.01/month

**Recreate when needed:**
- Reindex from storage (5 minutes)
- Deploy endpoint (5 minutes)
- Total downtime: 10 minutes

---

## Troubleshooting

### Issue 1: Azure OpenAI Access Denied

**Symptoms:**
- "Access denied" when creating hub
- OpenAI deployment fails

**Solutions:**

1. **Apply for access:**
   - https://aka.ms/oai/access
   - Fill out form
   - Wait 1-2 business days

2. **Check subscription type:**
   - Enterprise: Usually auto-approved
   - Personal: Requires manual approval

3. **Try different region:**
   - Some regions have waitlists
   - Try: East US, West Europe, Sweden Central

### Issue 2: Index Creation Fails

**Symptoms:**
- Index status: Failed
- Error: "Unable to chunk documents"

**Solutions:**

1. **Check file format:**
   - Must be .txt, .pdf, .docx, .md, or .jsonl
   - Ensure UTF-8 encoding
   - No special characters in filenames

2. **Verify data upload:**
   - Go to Data → clinical-notes-data
   - All files should be listed
   - No errors in upload status

3. **Reduce chunk size:**
   - If files are very large
   - Try chunk size: 500 instead of 1000

### Issue 3: Poor Search Results

**Symptoms:**
- Irrelevant results
- Missing expected documents
- Low confidence scores

**Solutions:**

1. **Adjust retrieval settings:**
   - Increase Top K (5 → 10)
   - Change to Hybrid mode
   - Enable semantic ranker

2. **Improve chunking:**
   - Smaller chunks for precise matching
   - Larger chunks for context

3. **Refine queries:**
   - Be more specific
   - Include medical terminology
   - Use synonyms

### Issue 4: High Costs

**Symptoms:**
- Unexpected charges
- Bills higher than expected

**Solutions:**

1. **Check token usage:**
   - Azure Portal → OpenAI resource → Metrics
   - View token consumption
   - Identify high-volume operations

2. **Optimize queries:**
   - Reduce max_tokens (800 → 400)
   - Use GPT-3.5 instead of GPT-4
   - Cache common queries

3. **Set spending limits:**
   - Azure Portal → Cost Management
   - Create budget alerts
   - Set daily limits

### Issue 5: Python SDK Errors

**Symptoms:**
- Import errors
- Authentication failures

**Solutions:**

1. **Update SDK:**
```bash
pip install --upgrade azure-ai-projects azure-ai-inference
```

2. **Check authentication:**
```bash
# Use Azure CLI
az login
az account show

# Or use connection string
PROJECT_CONNECTION_STRING = "your-string"
```

3. **Verify permissions:**
   - Azure Portal → AI Hub → Access control
   - Ensure you have Contributor role

---

## Best Practices

### Data Preparation

1. **Clean text thoroughly:**
   - Remove special characters
   - Fix encoding issues
   - Standardize formatting

2. **Add rich metadata:**
   - Patient demographics
   - Visit dates
   - Department/specialty
   - Helps with filtering

3. **Optimize chunk size:**
   - Medical notes: 800-1200 tokens
   - Shorter for precise search
   - Longer for context

### Query Optimization

1. **Write clear prompts:**
   - Be specific about what you want
   - Include expected format
   - Specify data sources

2. **Use system messages:**
   - Define assistant role
   - Set tone and style
   - Add domain knowledge

3. **Implement caching:**
   - Cache common queries
   - Reduce API calls
   - Lower costs

### Production Deployment

1. **Monitor performance:**
   - Track latency
   - Monitor token usage
   - Log failed queries

2. **Implement rate limiting:**
   - Prevent abuse
   - Control costs
   - Ensure fair usage

3. **Add error handling:**
   - Retry logic
   - Fallback responses
   - User-friendly errors

### Security

1. **Secure API keys:**
   - Use Key Vault
   - Rotate regularly
   - Never commit to code

2. **Implement RBAC:**
   - Least privilege access
   - Separate read/write roles
   - Audit access logs

3. **Data privacy:**
   - Encrypt at rest
   - Secure transit (HTTPS)
   - Comply with HIPAA (if applicable)

---

## Comparison Summary

### AI Foundry vs Azure AI Search

| Feature | Azure AI Foundry | Azure AI Search |
|---------|-----------------|-----------------|
| **Semantic Understanding** | OpenAI embeddings (best) | Built-in semantic | 
| **Setup Time** | 2-3 hours | 30 minutes |
| **ML Expertise** | Minimal | None |
| **Cost (learning)** | $0.30-1.60 | $0.20-0.50 |
| **Cost (production)** | Pay-per-query | $75/month flat |
| **Answer Generation** | Yes (GPT-4) | No (search only) |
| **Custom Prompts** | Yes | No |
| **Fine-tuning** | Yes | No |
| **Best For** | AI applications | Search-only apps |

### When to Use AI Foundry

**Choose AI Foundry when:**
- ✅ You want AI-generated answers (not just search)
- ✅ You need custom prompts for your domain
- ✅ You want to integrate GPT-4/3.5 capabilities
- ✅ You're building conversational AI
- ✅ You want best-in-class semantic understanding
- ✅ You have budget for per-query costs

**Choose Azure AI Search when:**
- ✅ You only need search (no answer generation)
- ✅ You prefer flat monthly cost
- ✅ You want simplest setup
- ✅ You have high query volume
- ✅ You don't need GPT-4 capabilities

---

## Next Steps

### Enhance Your AI Project

1. **Add more data sources:**
   - Lab results
   - Imaging reports
   - Treatment plans

2. **Implement multi-turn conversation:**
   - Remember conversation history
   - Follow-up questions
   - Context awareness

3. **Add specialized agents:**
   - Triage agent
   - Diagnosis agent
   - Treatment recommendation agent

### Integrate with Applications

1. **Build web app:**
   - React frontend
   - Call AI Foundry API
   - Display results with citations

2. **Create mobile app:**
   - iOS/Android
   - Offline caching
   - Voice input

3. **Integrate with EHR:**
   - HL7/FHIR connectors
   - Real-time data sync
   - Compliance tracking

### Advanced AI Capabilities

1. **Multimodal search:**
   - Add medical images
   - X-rays, MRIs, CT scans
   - Vision + text search

2. **Real-time analytics:**
   - Stream processing
   - Alert generation
   - Trend detection

3. **Predictive models:**
   - Readmission risk
   - Disease progression
   - Treatment outcomes

---

## Summary

### What You Built

✅ **Complete AI-powered search system**  
✅ **RAG with GPT-4 answer generation**  
✅ **Playground for testing**  
✅ **Deployed web endpoint**  
✅ **Python integration**  
✅ **Citation tracking**  
✅ **Cost: $0.30-1.60**  

### Key Advantages of AI Foundry

- **Best semantic understanding** (OpenAI embeddings)
- **AI-generated answers** (not just search)
- **Custom prompts** for your domain
- **Unified platform** for all AI needs
- **Latest models** (GPT-4, GPT-4 Turbo)
- **Evaluation tools** built-in
- **Pay-per-use** pricing

### Total Cost Summary

```
Setup & Testing:
├── Embeddings: $0.01
├── Queries (GPT-3.5): $0.03
├── Queries (GPT-4): $1.35
├── AI Search: $0.20
└── Web App: $0.04

Total: $0.30 (GPT-3.5) or $1.60 (GPT-4)

Production (monthly):
├── Embeddings: $1-5
├── Queries: $20-100
├── AI Search: $75
├── Web App: $13
└── Total: $110-195/month
```

---

## Additional Resources

### Documentation

- [Azure AI Foundry](https://learn.microsoft.com/azure/ai-studio/)
- [Azure OpenAI Service](https://learn.microsoft.com/azure/ai-services/openai/)
- [RAG Tutorial](https://learn.microsoft.com/azure/ai-studio/tutorials/deploy-chat-web-app)
- [Prompt Flow](https://learn.microsoft.com/azure/ai-studio/how-to/prompt-flow)

### Learning Paths

- [Build AI Solutions](https://learn.microsoft.com/training/paths/build-ai-solutions/)
- [OpenAI Service](https://learn.microsoft.com/training/paths/develop-ai-solutions-azure-openai/)
- [Responsible AI](https://learn.microsoft.com/training/paths/responsible-ai-business/)

### Community

- [Azure AI Community](https://techcommunity.microsoft.com/t5/ai-azure-ai-services/ct-p/Azure-AI-Services)
- [GitHub Samples](https://github.com/Azure-Samples/azureai-samples)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/azure-ai-studio)

---

## Completion Checklist

- [ ] Azure OpenAI access approved
- [ ] AI Hub created
- [ ] AI Project created
- [ ] Data uploaded (text files or JSONL)
- [ ] Embedding model deployed
- [ ] Vector index created
- [ ] Chat model deployed (GPT-4 or GPT-3.5)
- [ ] Playground testing completed
- [ ] All 5 clinical questions answered
- [ ] Web endpoint deployed (optional)
- [ ] Python integration tested
- [ ] Cost optimizations applied
- [ ] Resources cleaned up (if done learning)

**Congratulations on completing the Azure AI Foundry semantic search tutorial!** 

You now have the skills to build production-grade AI applications with the latest OpenAI models!