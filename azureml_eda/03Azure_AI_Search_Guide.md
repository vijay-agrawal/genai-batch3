# Azure AI Search - Semantic Search for Healthcare Data

** Healthcare Training - Part 3: Semantic Search with Azure AI Search**

**IMPORTANT:** This guide uses **Azure AI Search** (formerly Azure Cognitive Search), which is a **standalone search service**. This is **NOT** Azure AI Foundry/AI Studio.


## Overview

This guide implements semantic search using **Azure AI Search** - a dedicated search service in Azure Portal (NOT Azure AI Foundry/AI Studio).

**What You'll Build:**
- Searchable index of clinical notes
- Semantic search with natural language queries
- REST API endpoint for your application
- No machine learning expertise required
- No compute management needed
- No Azure OpenAI required

**Time Required:** 1-2 hours

**Estimated Cost:** $0.10-$2.00 per month for this dataset

---

## Azure AI Search vs Azure AI Foundry

### Key Differences

| Aspect | Azure AI Search (THIS GUIDE) | Azure AI Foundry (Part 4) |
|--------|----------------------------|---------------------------|
| **Portal** | portal.azure.com | ai.azure.com |
| **Service Type** | Search service | AI Studio platform |
| **Embeddings** | Built-in semantic ranking | Azure OpenAI embeddings |
| **AI Generation** | No (search only) | Yes (GPT-4 answers) |
| **Setup** | 30 minutes | 2-3 hours |
| **Cost** | $75/month (Basic) | Pay-per-query |
| **OpenAI Required** | No | Yes |
| **Best For** | Pure search apps | AI chatbots/Q&A |

### What is Azure AI Search?

**Azure AI Search** (formerly Cognitive Search) is:
- A **standalone search service** in Azure
- Available through **Azure Portal** (portal.azure.com)
- Has **built-in semantic ranking** (no OpenAI needed)
- Provides **search results only** (not AI-generated answers)
- **Independent** from Azure AI Foundry/AI Studio

### What is Azure AI Foundry?

**Azure AI Foundry** (AI Studio) is:
- A **platform** at ai.azure.com
- Integrates **Azure OpenAI** + Azure AI Search + other AI services
- Provides **RAG** (Retrieval Augmented Generation)
- Generates **AI answers** with GPT-4/GPT-3.5
- Covered in **Part 4** (separate guide)

### When to Use Each

**Use Azure AI Search (THIS GUIDE) when:**
- ✅ You need search functionality only
- ✅ You don't need AI-generated answers
- ✅ You want fastest setup
- ✅ You prefer flat monthly cost
- ✅ You don't need OpenAI integration

**Use Azure AI Foundry (Part 4) when:**
- ✅ You want AI-generated answers
- ✅ You're building chatbots/Q&A systems
- ✅ You need GPT-4/GPT-3.5 integration
- ✅ You want RAG capabilities

---

## Prerequisites

### Required

- Azure subscription (free trial works)
- Dataset: `healthcare_data_enhanced.json`
- Web browser (for Azure Portal)

### NOT Required

- ❌ Azure AI Foundry access
- ❌ Azure AI Studio account
- ❌ Azure OpenAI approval
- ❌ GPT-4 access

### Cost Requirements

- **Free Tier Available:** Yes (limited features)
- **Recommended Tier:** Basic ($0.10 per hour ($75/month), pro-rated by hour)
- **For this tutorial:** <$2 for complete testing

---

## Architecture Overview

### How It Works

```
Clinical Notes (JSON)
        ↓
Azure Blob Storage
        ↓
Azure AI Search Indexer (automatic)
        ↓
Search Index (with built-in semantic ranking)
        ↓
Query API (REST endpoint)
        ↓
Your Application (search results)
```

**Note:** This does NOT involve:
- Azure AI Foundry
- Azure AI Studio
- Azure OpenAI
- GPT models

### Key Components

1. **Data Source:** Azure Blob Storage (stores your JSON)
2. **Indexer:** Automatically processes documents
3. **Index:** Searchable database of notes
4. **Semantic Ranker:** Built-in AI for relevance (no OpenAI)
5. **Query API:** REST endpoint for searches

---

## Phase 1: Azure AI Search Setup

### Step 1.1: Create Azure AI Search Service

**Navigate to Azure Portal:**

1. Go to https://portal.azure.com (NOT ai.azure.com)
2. Sign in with Azure credentials
3. Click **+ Create a resource**
4. Search for **"Azure AI Search"** (formerly "Cognitive Search")
5. Click **Create**

**Configure Search Service:**

```
Basics Tab:
├── Subscription: [Your subscription]
├── Resource Group: rg-<your name>-healthcare (use existing or create new)
├── Service Name: <your name>-healthcare-search
│   (Must be globally unique: try <your name>-search-[yourname])
├── Location: East US (or your preferred region)
└── Pricing Tier: Basic
```

**Pricing Tier Selection:**

Click **"Change Pricing Tier"**

Available options:
- **Free:** 3 indexes, 50MB storage (no semantic search)
- **Basic:** $0.10/hour ($75 per month), 15 indexes, 2GB storage ✅ **RECOMMENDED**
- **Standard S1:** $250/month (overkill for learning)

**For this tutorial: Choose Basic**
- Pro-rated by hour: ~$0.10/hour
- You'll use <20 hours = <$2 total
- Delete when done to stop charges

**Important Note:**
- Semantic search requires Basic tier or higher
- Free tier does NOT support semantic search
- Semantic search is built-in (no Azure OpenAI needed)

**Important Settings:**

```
Scale Tab:
├── Replicas: 1 (minimum, sufficient)
└── Partitions: 1 (minimum, sufficient)

Networking Tab:
└── Public endpoint (all networks) ✓
```

**Create:**

1. Click **Review + Create**
2. Click **Create**
3. Wait 2-3 minutes for deployment
4. Click **Go to resource**

### Step 1.2: Get API Keys

**In your Search service:**

1. Left sidebar → **Keys**
2. Copy and save:
   - **Primary admin key** (for writing data)
   - **Query key** (for searching)
3. Note your **URL**: `https://<your name>-healthcare-search.search.windows.net`

**Keep these secure!** You'll need them later.

---

## Phase 2: Data Preparation

### Step 2.1: Create Storage Account (If Not Exists)

**Navigate to Storage:**

1. Azure Portal → **+ Create a resource**
2. Search **"Storage account"**
3. Click **Create**

**Configure:**

```
Basics:
├── Subscription: [Your subscription]
├── Resource Group: rg-<your name>-healthcare
├── Storage account name: citiushealthdata (lowercase, no hyphens)
├── Region: Same as search service (East US)
├── Performance: Standard
└── Redundancy: LRS (cheapest: ~$0.02/GB/month)

Advanced:
└── Allow Blob anonymous access: Enabled (for easier setup)
```

Click **Review + Create** → **Create**

### Step 2.2: Upload Data to Blob Storage

**Method 1: Azure Portal (Easiest)**

1. Go to your storage account
2. Left sidebar → **Containers**
3. Click **+ Container**
   - Name: `healthcare-data`
   - Public access level: **Blob (anonymous read)**
4. Click **Create**
5. Click on `healthcare-data` container
6. Click **Upload**
7. Select `healthcare_data_enhanced.json`
8. Click **Upload**

**Verify:** You should see the file listed in the container

### Step 2.3: Flatten JSON for Indexing

**Challenge:** Azure AI Search works best with flat JSON (one document = one clinical note)

**Solution:** Transform nested JSON into flat documents.

**Create transformation script `flatten_for_search.py`:**

```python
import json

# Load nested data
with open('healthcare_data_enhanced.json', 'r') as f:
    data = json.load(f)

# Flatten to one document per clinical note
flattened_docs = []

for patient in data['patients']:
    patient_id = patient['patient_id']
    patient_name = patient['demographics']['name']
    patient_age = patient['demographics']['age']
    patient_gender = patient['demographics']['gender']
    
    for visit in patient['visits']:
        # Create one document per visit
        doc = {
            'id': visit['visit_id'],  # Unique ID
            'patient_id': patient_id,
            'patient_name': patient_name,
            'patient_age': patient_age,
            'patient_gender': patient_gender,
            'visit_id': visit['visit_id'],
            'visit_date': visit['date'],
            'department': visit['department'],
            'visit_type': visit['type'],
            'provider_name': visit['provider']['name'],
            'provider_specialty': visit['provider']['specialty'],
            'clinical_notes': visit['clinical_notes'],
            'diagnoses': '; '.join([d['description'] for d in visit['diagnoses']]),
            'icd10_codes': ', '.join([d['icd10_code'] for d in visit['diagnoses']]),
            'blood_pressure': visit['vitals']['blood_pressure'],
            'heart_rate': visit['vitals']['heart_rate'],
            'temperature': visit['vitals']['temperature'],
            'weight_lbs': visit['vitals']['weight_lbs'],
            'bmi': visit['vitals']['bmi'],
            'total_charge': visit['billing']['total_charge']
        }
        flattened_docs.append(doc)

# Save as JSON Lines (one JSON object per line)
with open('clinical_notes_flattened.json', 'w') as f:
    for doc in flattened_docs:
        f.write(json.dumps(doc) + '\n')

print(f"✓ Created {len(flattened_docs)} flattened documents")
print(f"✓ Saved to: clinical_notes_flattened.json")
```

**Run the script:**

```bash
python flatten_for_search.py
```

**Result:** `clinical_notes_flattened.json` with 18 documents (one per visit)

**Upload flattened file:**

1. Go to storage account → `healthcare-data` container
2. Upload `clinical_notes_flattened.json`
3. This file will be indexed by Azure AI Search

---

## Phase 3: Index Creation

### Step 3.1: Create Data Source Connection

**In your Azure AI Search service:**

1. Left sidebar → **Data sources**
2. Click **+ Add data source**

**Configure data source:**

```
Name: healthcare-data-source
Data source type: Azure Blob Storage
Connection string: [Click "Choose an existing connection"]
  └── Select your storage account: citiushealthdata
  └── Select container: healthcare-data
Container name: healthcare-data (auto-filled)
Blob folder: (leave empty)
Description: Clinical notes from  Healthcare
```

3. Click **Save**

**Verify:** You should see "healthcare-data-source" in your data sources list

### Step 3.2: Create Index Using Import Wizard

**Start Import Wizard:**

1. Left sidebar → **Import data**
2. Select data source: **healthcare-data-source**
3. Choose file: **clinical_notes_flattened.json**
4. Click **Next: Add cognitive skills (Optional)**

**Skip Cognitive Skills:**

- Click **Skip to: Customize target index**
- (We'll use built-in semantic search instead)

**Define Index Schema:**

You'll see fields detected from your JSON. Configure them:

```
Index name: clinical-notes-index

Fields Configuration:
┌──────────────────┬──────────┬────────────┬────────┬──────────┬─────────┐
│ Field Name       │ Type     │ Retrievable│Filterable│Sortable │Searchable│
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ id               │ Edm.String│ ✓         │ ✓        │         │         │
│ (Key field)      │           │           │          │         │         │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ patient_id       │ Edm.String│ ✓         │ ✓        │         │         │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ patient_name     │ Edm.String│ ✓         │ ✓        │ ✓       │ ✓       │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ patient_age      │ Edm.Int32 │ ✓         │ ✓        │ ✓       │         │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ patient_gender   │ Edm.String│ ✓         │ ✓        │         │         │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ visit_id         │ Edm.String│ ✓         │ ✓        │         │         │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ visit_date       │Edm.DateTimeOffset│ ✓  │ ✓        │ ✓       │         │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ department       │ Edm.String│ ✓         │ ✓        │         │ ✓       │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ visit_type       │ Edm.String│ ✓         │ ✓        │         │         │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ provider_name    │ Edm.String│ ✓         │ ✓        │         │ ✓       │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ clinical_notes   │ Edm.String│ ✓         │          │         │ ✓       │
│                  │           │           │          │         │(Primary) │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ diagnoses        │ Edm.String│ ✓         │          │         │ ✓       │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ icd10_codes      │ Edm.String│ ✓         │ ✓        │         │ ✓       │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ blood_pressure   │ Edm.String│ ✓         │          │         │         │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ heart_rate       │ Edm.Int32 │ ✓         │ ✓        │ ✓       │         │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ bmi              │ Edm.Double│ ✓         │ ✓        │ ✓       │         │
├──────────────────┼──────────┼────────────┼──────────┼─────────┼─────────┤
│ total_charge     │ Edm.Double│ ✓         │ ✓        │ ✓       │         │
└──────────────────┴──────────┴────────────┴──────────┴─────────┴─────────┘
```

**Key Settings:**

- **id:** Set as Key field (check "Key" box)
- **clinical_notes:** Mark as Searchable (main content field)
- **patient_name, department, provider_name, diagnoses:** Mark as Searchable
- **patient_age, visit_date, heart_rate, bmi, total_charge:** Mark as Filterable and Sortable

**Click "Next: Create an indexer"**

### Step 3.3: Configure Indexer

**Indexer settings:**

```
Name: clinical-notes-indexer
Schedule: Once (for now; can change to recurring later)
Parse mode: JSON array (since file has multiple JSON objects)
```

**Advanced options:**

```
Base-64 Encode Keys: ✓ (checked)
Max failed items: 0
Max failed items per batch: 0
```

**Click "Submit"**

The indexer will run immediately and import your data.

**Monitor Progress:**

1. Left sidebar → **Indexers**
2. Click on **clinical-notes-indexer**
3. You should see:
   - Status: Success
   - Documents processed: 18 (or your total)
   - Documents failed: 0

**If indexing fails:**
- Check data source connection
- Verify JSON format (use JSON validator)
- Review error messages in indexer execution history

---

## Phase 4: Semantic Configuration

### Step 4.1: Enable Semantic Search (Built-in)

**Azure AI Search has built-in semantic search!**
- No Azure OpenAI needed
- No Azure AI Foundry needed
- Built into the service

**Configure semantic search:**

1. Go to your Search service
2. Left sidebar → **Semantic ranking**
3. Enable: **Free plan** (1000 queries/month free on Basic tier)
4. Click **+ Add semantic configuration**

**Create configuration:**

```
Name: clinical-semantic-config

Title field: patient_name
  (This appears in search results as the title)

Content fields (in priority order):
  1. clinical_notes (Priority: High)
  2. diagnoses (Priority: High)
  3. department (Priority: Medium)

Keyword fields:
  ├── patient_id
  ├── visit_id
  └── icd10_codes
```

**Explanation:**

- **Title field:** Shows as the result heading
- **Content fields:** Text to analyze semantically (clinical notes are key)
- **Keyword fields:** Used for exact matching and filtering

4. Click **Save**

### Step 4.2: Verify Semantic Configuration

**Check configuration:**

1. Go to **Indexes**
2. Click on **clinical-notes-index**
3. Navigate to **Semantic configurations** tab
4. You should see **clinical-semantic-config**

**Note on pricing:**
- Semantic search on Basic tier: First 1000 queries/month FREE
- After 1000: ~$500/month (but for learning you'll use <20 queries)
- For this tutorial: FREE

---

## Phase 5: Query Implementation

### Step 5.1: Test Basic Search (Portal)

**Use Search Explorer:**

1. In your Search service → **Search explorer**
2. Select index: **clinical-notes-index**

**Try basic search:**

```
Query: back pain
```

Click **Search**

**Expected results:** Documents mentioning "back pain"

**Results include:**
- patient_name
- clinical_notes (with highlights)
- department
- visit_date
- Relevance score

### Step 5.2: Test Semantic Search (Portal)

**Enable semantic search in query:**

In Search explorer:

1. View: **JSON view**
2. Enter query:

```json
{
  "search": "patients with lower back pain",
  "queryType": "semantic",
  "semanticConfiguration": "clinical-semantic-config",
  "top": 10
}
```

3. Click **Search**

**What's different with semantic search?**

Semantic search understands:
- "lower back pain" = "lumbar discomfort"
- "back issues" = "spinal problems"
- Contextual meaning, not just keywords
- Better ranking based on relevance

**Without Azure OpenAI or AI Foundry!**

### Step 5.3: Advanced Query Examples

**Example 1: Filter by department**

```json
{
  "search": "breathing problems",
  "queryType": "semantic",
  "semanticConfiguration": "clinical-semantic-config",
  "filter": "department eq 'Primary Care'",
  "top": 10
}
```

**Example 2: Sort by date**

```json
{
  "search": "chest pain",
  "queryType": "semantic",
  "semanticConfiguration": "clinical-semantic-config",
  "orderby": "visit_date desc",
  "top": 5
}
```

**Example 3: Filter by age range**

```json
{
  "search": "diabetes management",
  "queryType": "semantic",
  "semanticConfiguration": "clinical-semantic-config",
  "filter": "patient_age gt 50",
  "top": 10
}
```

**Example 4: Multiple filters**

```json
{
  "search": "chronic pain",
  "queryType": "semantic",
  "semanticConfiguration": "clinical-semantic-config",
  "filter": "patient_age ge 40 and patient_gender eq 'F'",
  "orderby": "visit_date desc",
  "top": 10
}
```

**Example 5: Search specific fields**

```json
{
  "search": "back pain",
  "queryType": "semantic",
  "semanticConfiguration": "clinical-semantic-config",
  "searchFields": "clinical_notes,diagnoses",
  "select": "patient_name,clinical_notes,diagnoses,visit_date",
  "top": 10
}
```

---

## Phase 6: Testing & Validation

### Step 6.1: Answer Clinical Questions

**Question 1: How many patients have back pain?**

**Query:**
```json
{
  "search": "back pain lumbar discomfort spine",
  "queryType": "semantic",
  "semanticConfiguration": "clinical-semantic-config",
  "searchFields": "clinical_notes,diagnoses",
  "select": "patient_id,patient_name,clinical_notes,diagnoses",
  "top": 20
}
```

**Manually count unique patient_ids from results**

**Expected:** 2-3 patients

**Question 2: Which patients have respiratory issues?**

**Query:**
```json
{
  "search": "breathing problems respiratory wheezing asthma dyspnea",
  "queryType": "semantic",
  "semanticConfiguration": "clinical-semantic-config",
  "searchFields": "clinical_notes,diagnoses",
  "select": "patient_name,department,diagnoses",
  "top": 10
}
```

**Expected:** 1-2 patients

**Question 3: Find patients with muscle pain**

**Query:**
```json
{
  "search": "muscle pain aches myalgia fibromyalgia",
  "queryType": "semantic",
  "semanticConfiguration": "clinical-semantic-config",
  "searchFields": "clinical_notes,diagnoses",
  "select": "patient_name,diagnoses",
  "top": 10
}
```

**Expected:** 2-3 patients

**Question 4: Chest discomfort cases**

**Query:**
```json
{
  "search": "chest pain discomfort tightness angina",
  "queryType": "semantic",
  "semanticConfiguration": "clinical-semantic-config",
  "searchFields": "clinical_notes",
  "select": "patient_name,department,diagnoses",
  "top": 10
}
```

**Expected:** 1-2 patients

**Question 5: Headache patients**

**Query:**
```json
{
  "search": "headache migraine cephalgia",
  "queryType": "semantic",
  "semanticConfiguration": "clinical-semantic-config",
  "searchFields": "clinical_notes,diagnoses",
  "select": "patient_name,diagnoses",
  "top": 10
}
```

**Expected:** 1 patient

### Step 6.2: Compare Semantic vs Simple Search

**Test the same query with both modes:**

**Simple (keyword) search:**
```json
{
  "search": "back pain",
  "queryType": "simple",
  "top": 10
}
```

**Semantic search:**
```json
{
  "search": "back pain",
  "queryType": "semantic",
  "semanticConfiguration": "clinical-semantic-config",
  "top": 10
}
```

**Observations:**

- **Semantic finds:** "lumbar discomfort", "lower back ache", "spinal pain"
- **Simple only finds:** exact phrase "back pain"
- **Semantic understands:** medical terminology variations
- **Semantic ranks:** by relevance, not just keyword match

**All without Azure OpenAI or AI Foundry!**

---

## Phase 7: Integration with Python

### Step 7.1: Install Azure Search SDK

```bash
pip install azure-search-documents azure-identity
```

### Step 7.2: Python Search Client

**Create `azure_search_client.py`:**

```python
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Configuration (from Azure Portal)
SEARCH_SERVICE_NAME = "<your name>-healthcare-search"
SEARCH_INDEX_NAME = "clinical-notes-index"
SEARCH_API_KEY = "YOUR_SEARCH_API_KEY_HERE"

# Create endpoint URL
endpoint = f"https://{SEARCH_SERVICE_NAME}.search.windows.net"

# Create search client
search_client = SearchClient(
    endpoint=endpoint,
    index_name=SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_API_KEY)
)

def semantic_search(query, top=10, filters=None):
    """
    Perform semantic search on clinical notes.
    
    Args:
        query (str): Natural language query
        top (int): Number of results
        filters (str): OData filter expression
    
    Returns:
        list: Search results
    """
    results = search_client.search(
        search_text=query,
        query_type="semantic",
        semantic_configuration_name="clinical-semantic-config",
        top=top,
        filter=filters,
        select=["patient_name", "clinical_notes", "diagnoses", 
                "department", "visit_date", "patient_id"]
    )
    
    return list(results)

def print_results(results):
    """Pretty print search results."""
    print(f"\n{'='*80}")
    print(f"Found {len(results)} results")
    print(f"{'='*80}\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.get('patient_name', 'Unknown')}")
        print(f"   Department: {result.get('department', 'N/A')}")
        print(f"   Date: {result.get('visit_date', 'N/A')}")
        print(f"   Diagnoses: {result.get('diagnoses', 'N/A')}")
        print(f"   Score: {result.get('@search.score', 0):.4f}")
        
        # Show excerpt
        notes = result.get('clinical_notes', '')
        excerpt = notes[:200] + "..." if len(notes) > 200 else notes
        print(f"   Excerpt: {excerpt}")
        print()

# Example usage
if __name__ == "__main__":
    # Question 1: Back pain
    print("\n=== QUESTION 1: Patients with back pain ===")
    results = semantic_search("back pain lumbar discomfort", top=10)
    print_results(results)
    
    # Count unique patients
    unique_patients = set(r.get('patient_id') for r in results)
    print(f"Unique patients with back pain: {len(unique_patients)}")
    
    # Question 2: Respiratory issues
    print("\n=== QUESTION 2: Respiratory complaints ===")
    results = semantic_search("breathing problems respiratory issues", top=10)
    print_results(results)
    
    # Question 3: Filter by department
    print("\n=== QUESTION 3: Primary Care visits ===")
    results = semantic_search(
        "chronic pain", 
        top=10, 
        filters="department eq 'Primary Care'"
    )
    print_results(results)
```

### Step 7.3: Run Python Client

```bash
python azure_search_client.py
```

**Expected output:**
- Results for back pain query
- Count of unique patients
- Respiratory issue cases
- Filtered results by department

**Note:** This uses only Azure AI Search, no AI Foundry or OpenAI!

### Step 7.4: Jupyter Notebook Integration

**Create `azure_search_analysis.ipynb`:**

```python
# Cell 1: Setup
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import pandas as pd
import matplotlib.pyplot as plt

SEARCH_SERVICE_NAME = "<your name>-healthcare-search"
SEARCH_INDEX_NAME = "clinical-notes-index"
SEARCH_API_KEY = "YOUR_KEY_HERE"

endpoint = f"https://{SEARCH_SERVICE_NAME}.search.windows.net"
search_client = SearchClient(
    endpoint=endpoint,
    index_name=SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_API_KEY)
)

print("✓ Connected to Azure AI Search")
print("✓ No Azure AI Foundry or OpenAI required!")
```

```python
# Cell 2: Define search function
def semantic_search(query, top=20):
    """Semantic search wrapper."""
    results = search_client.search(
        search_text=query,
        query_type="semantic",
        semantic_configuration_name="clinical-semantic-config",
        top=top,
        select=["patient_id", "patient_name", "patient_age", 
                "department", "diagnoses", "clinical_notes", "visit_date"]
    )
    return list(results)

# Test
test_results = semantic_search("back pain", top=5)
print(f"Found {len(test_results)} results")
```

```python
# Cell 3: Answer all clinical questions
questions = {
    "Back Pain": "back pain lumbar discomfort spinal pain",
    "Respiratory": "breathing problems wheezing respiratory",
    "Muscle Pain": "muscle aches myalgia pain",
    "Chest Pain": "chest pain discomfort tightness",
    "Headache": "headache migraine"
}

results_summary = []

for question, query in questions.items():
    results = semantic_search(query, top=20)
    
    # Get unique patients
    unique_patients = len(set(r.get('patient_id') for r in results))
    
    results_summary.append({
        'Symptom': question,
        'Query': query,
        'Total Results': len(results),
        'Unique Patients': unique_patients
    })
    
    print(f"\n{question}:")
    print(f"  Query: {query}")
    print(f"  Results: {len(results)}")
    print(f"  Unique patients: {unique_patients}")

# Create summary DataFrame
summary_df = pd.DataFrame(results_summary)
display(summary_df)
```

```python
# Cell 4: Visualize results
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Total results
axes[0].barh(summary_df['Symptom'], summary_df['Total Results'], color='steelblue')
axes[0].set_xlabel('Total Search Results')
axes[0].set_title('Search Results by Symptom Category')
axes[0].grid(axis='x', alpha=0.3)

# Plot 2: Unique patients
axes[1].barh(summary_df['Symptom'], summary_df['Unique Patients'], color='coral')
axes[1].set_xlabel('Unique Patients')
axes[1].set_title('Unique Patients by Symptom')
axes[1].grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig('azure_search_results.png', dpi=300)
plt.show()

print("\n✓ Analysis complete!")
print("✓ Using Azure AI Search only (no AI Foundry)")
```

```python
# Cell 5: Compare semantic vs simple search
query = "back pain"

# Semantic search
semantic_results = list(search_client.search(
    search_text=query,
    query_type="semantic",
    semantic_configuration_name="clinical-semantic-config",
    top=20
))

# Simple search
simple_results = list(search_client.search(
    search_text=query,
    query_type="simple",
    top=20
))

print(f"Comparison for query: '{query}'")
print(f"  Semantic search: {len(semantic_results)} results")
print(f"  Simple search: {len(simple_results)} results")
print(f"  Advantage: {len(semantic_results) - len(simple_results)} additional cases")
print("\n✓ Semantic search powered by Azure AI Search built-in AI")
print("✓ No Azure OpenAI or AI Foundry required")
```

---

## Cost Analysis

### Detailed Pricing Breakdown

**Azure AI Search - Basic Tier:**

```
Base Cost: $75/month = $0.10/hour

Pro-rated calculation for this tutorial:
├── Setup & configuration: 0.5 hours = $0.05
├── Testing queries: 1 hour = $0.10
├── Python integration: 0.5 hours = $0.05
└── Total: 2 hours = $0.20

Semantic Search:
├── First 1000 queries/month: FREE on Basic tier
└── Usage in tutorial: ~20 queries = $0.00
```

**Storage (Blob Storage):**

```
Storage used: ~0.1 GB
Cost: $0.02 per GB per month
Total: $0.002/month = negligible
```

**Total Cost for Tutorial:**

```
One-time setup & testing: ~$0.20
Monthly if kept running: $75/month (Basic tier)
Recommendation: Delete after learning = $0.20 total
```

**Important Notes:**
- ✅ No Azure OpenAI costs ($0)
- ✅ No Azure AI Foundry costs ($0)
- ✅ No GPT-4 charges ($0)
- ✅ Just search service costs

### Cost Optimization Strategies

**1. Use Free Tier for Basic Testing**
```
Limitations:
├── No semantic search (keyword only)
├── 50MB storage limit
├── 3 indexes max
└── Suitable for: Basic keyword search testing
```

**2. Pro-rate Basic Tier**
```
Strategy:
├── Create service only when needed
├── Test for 2-3 hours
├── Delete immediately after
└── Cost: $0.20-$0.30 per session
```

**3. Standard Tier (Production)**
```
When to upgrade:
├── Production deployment
├── >2GB data
├── High query volume (>50 queries/sec)
└── Cost: $250+/month
```

### Cost Comparison with Other Approaches

| Solution | Setup Cost | Monthly Cost | Total (Learning) | Requires OpenAI |
|----------|-----------|--------------|------------------|----------------|
| **Azure AI Search (THIS)** | $0.20 | $75 (delete after) | **$0.20** ✅ | ❌ No |
| Azure AI Foundry | $0.25 | Pay-per-query | $0.30-1.60 | ✅ Yes |
| Azure ML + Transformers | $5-10 | $5-10 | $15-20 | ❌ No |
| Custom OpenAI API | $0 | Pay per query | $5-10 | ✅ Yes |

**Winner for pure search: Azure AI Search ($0.20)**

---

## Cleanup & Cost Savings

### Step 1: Delete Search Service

**To avoid ongoing charges:**

1. Azure Portal → Your search service
2. Click **Delete**
3. Confirm deletion
4. Cost stops immediately

**Optional: Keep storage account** (costs $0.002/month)

### Step 2: Delete Entire Resource Group

**Complete cleanup:**

1. Azure Portal → Resource groups
2. Select `rg-<your name>-healthcare`
3. Click **Delete resource group**
4. Type resource group name to confirm
5. Click **Delete**

**This deletes:**
- Search service
- Storage account
- All data

**Cost drops to $0**

### Step 3: Verify Deletion

1. Azure Portal → **Cost Management + Billing**
2. View charges for today
3. Should show $0 for search service after deletion

---

## Troubleshooting

### Issue 1: Indexer Fails

**Solutions:**

1. **Check JSON format:**
```json
// Each line should be a valid JSON object
{"id": "1", "field": "value"}
{"id": "2", "field": "value"}
```

2. **Verify blob access**
3. **Check field mappings**

### Issue 2: No Search Results

**Solutions:**

1. Verify index has documents
2. Check searchable fields
3. Try simpler query

### Issue 3: Semantic Search Not Working

**Solutions:**

1. **Verify tier:** Basic or higher required
2. **Check semantic configuration**
3. **Correct query syntax**

---

## Best Practices

### Index Design

1. **Choose searchable fields wisely**
2. **Optimize field types**
3. **Configure analyzers for medical terminology**

### Query Optimization

1. **Use filters efficiently**
2. **Limit results with top parameter**
3. **Cache common queries**

### Security

1. **Use query keys for read-only**
2. **Enable CORS if needed**
3. **Configure firewall rules**

---

## Summary

### What You Built

✅ **Semantic search system using Azure AI Search**  
✅ **REST API endpoint**  
✅ **Answers to 5 clinical questions**  
✅ **Better than keyword search**  
✅ **No Azure OpenAI required**  
✅ **No Azure AI Foundry required**  
✅ **Cost: $0.20 for learning**  

### Key Advantages

- **No ML expertise required**
- **No Azure OpenAI needed**
- **No AI Foundry needed**
- **Built-in semantic understanding**
- **30-minute setup**
- **Flat monthly cost**
- **99.9% SLA**

### Total Cost

```
Setup & testing: ~$0.20
Delete immediately: No ongoing costs
Production (Basic): $75/month
```

---

## Comparison: Azure AI Search vs Azure AI Foundry

| Feature | Azure AI Search (THIS GUIDE) | Azure AI Foundry (Part 4) |
|---------|----------------------------|---------------------------|
| **Portal** | portal.azure.com | ai.azure.com |
| **Service** | Standalone search | AI Studio platform |
| **Embeddings** | Built-in semantic | Azure OpenAI |
| **Answers** | Search results only | AI-generated with GPT-4 |
| **Setup** | 30 minutes | 2-3 hours |
| **Cost (learning)** | $0.20 | $0.30-1.60 |
| **Cost (production)** | $75/month flat | Pay-per-query |
| **OpenAI Required** | No | Yes |
| **AI Foundry Required** | No | Yes |
| **Best For** | Pure search | AI chatbots/Q&A |

### When to Use Azure AI Search

**Choose Azure AI Search (THIS GUIDE) when:**
- ✅ You need search functionality only
- ✅ You don't need AI-generated answers
- ✅ You want fastest setup (30 min)
- ✅ You prefer flat monthly cost
- ✅ You don't have Azure OpenAI access
- ✅ You don't need AI Foundry

### When to Use Azure AI Foundry

**Choose Azure AI Foundry (Part 4) when:**
- ✅ You want AI-generated answers
- ✅ You're building chatbots
- ✅ You need GPT-4 integration
- ✅ You want RAG capabilities
- ✅ You have Azure OpenAI access

---

## Completion Checklist

- [ ] Azure AI Search service created (NOT AI Foundry)
- [ ] Data uploaded to Blob Storage
- [ ] Index created with all fields
- [ ] Semantic configuration added (built-in, no OpenAI)
- [ ] Indexer run successfully
- [ ] Basic searches tested in portal
- [ ] Semantic searches tested
- [ ] All 5 clinical questions answered
- [ ] Python client tested
- [ ] Cost optimizations applied
- [ ] Resources deleted (if learning only)

**Congratulations! You've completed Azure AI Search (standalone service) without Azure AI Foundry or OpenAI!** 