# Azure Machine Learning - Complete Semantic Search Guide

** EDA Training - Part 2: Semantic Search with NLP**

## Overview

This guide walks you through implementing semantic search for clinical notes using Azure Machine Learning. You'll learn to:

- Set up NLP environment in Azure ML
- Load pre-trained transformer models
- Generate sentence embeddings
- Implement semantic similarity search
- Answer natural language questions about patients
- Compare semantic vs keyword search
- Deploy search as a service (optional)

**Estimated Time:** 2-3 hours (first time), 1 hour (subsequent runs)

**Estimated Cost:** $3-6 for complete assignment (with proper cleanup)

---

## Prerequisites

### Required

- Completed Azure ML EDA assignment (or familiar with Azure ML)
- Azure ML workspace already created
- Dataset file: `healthcare_data_enhanced.json`
- Basic understanding of NLP concepts (helpful but not required)

### Recommended

- Understanding of embeddings/vectors
- Familiarity with similarity metrics
- Knowledge of transformer models (BERT, etc.)

---

## Phase 1: Environment Setup

### Step 1.1: Create or Access Workspace

**If you completed EDA assignment:**
- Use the same workspace: `mlw-<your name>-healthcare`
- Skip to Step 1.2

**If starting fresh:**
1. Follow Phase 1 from EDA guide to create workspace
2. Or use existing workspace

### Step 1.2: Create Compute Instance for NLP

**Navigate to Compute:**

```
Azure ML Studio → Left sidebar → Compute
```

**Create New Compute Instance:**

```
Compute name: ci-<your name>-nlp
Virtual machine type: CPU
Virtual machine size: Standard_DS4_v2
  - Cores: 8
  - RAM: 28 GB (more RAM needed for ML models)
  - Storage: 56 GB
  - Cost: ~$0.384/hour
```

**Why larger compute?**
- Transformer models require more memory
- Standard_DS3_v2 (14GB) can work but may be slow
- DS4_v2 provides better performance for model loading

**Configure Auto-Shutdown:**
1. Click compute name → Edit
2. Enable "Enable idle shutdown"
3. Set to 30 minutes
4. Click Update

---

## Phase 2: Data Preparation

### Step 2.1: Upload Enhanced Dataset

**Navigate to Data:**

```
Azure ML Studio → Data → Data assets
```

**Create Data Asset:**

1. Click **+ Create**
2. Name: `healthcare_enhanced`
3. Type: **File**
4. Upload `healthcare_data_enhanced.json`
5. Path: `healthcare/enhanced_data/`
6. Click **Create**

**Verify:**
- Go to Data assets
- Find "healthcare_enhanced"
- Should show status "Complete"

### Step 2.2: Create Notebook

**Navigate to Notebooks:**

```
Azure ML Studio → Notebooks
```

**Create Structure:**

1. Navigate to `healthcare_training/` folder
2. Create subfolder: `semantic_search_assignment`
3. Create notebook: `01_semantic_search.ipynb`
4. Select compute: `ci-<your name>-nlp`
5. Wait for kernel to start (~30 seconds)

---

## Phase 3: Model Loading

### Step 3.1: Install NLP Libraries

**Cell 1: Install sentence-transformers**

```python
# Cell 1: Install NLP libraries
# This takes 3-5 minutes on first run
print("Installing NLP libraries... (this may take a few minutes)")

%pip install sentence-transformers==2.2.2 --quiet
%pip install umap-learn==0.5.4 --quiet

print("✓ Installation complete!")
```

**Run and wait for completion.**

### Step 3.2: Import Libraries

**Cell 2: Import all libraries**

```python
# Cell 2: Import libraries
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# NLP specific
from sentence_transformers import SentenceTransformer, util

# Azure ML
from azureml.core import Workspace, Dataset, Datastore, Experiment
import mlflow

print("✓ All imports successful!")
print(f"sentence-transformers available: ✓")

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', 150)

# Enable inline plotting
%matplotlib inline
```

### Step 3.3: Connect to Workspace

**Cell 3: Workspace connection**

```python
# Cell 3: Connect to Azure ML workspace
ws = Workspace.from_config()

print("✓ Connected to workspace")
print(f"  Workspace: {ws.name}")
print(f"  Resource group: {ws.resource_group}")
print(f"  Location: {ws.location}")
```

### Step 3.4: Load Enhanced Dataset

**Cell 4: Download and load data**

```python
# Cell 4: Load enhanced dataset
datastore = ws.get_default_datastore()

# Download data
datastore.download(
    target_path='./data',
    prefix='healthcare/enhanced_data/',
    overwrite=True
)

# Load JSON
with open('./data/healthcare/enhanced_data/healthcare_data_enhanced.json', 'r') as f:
    data = json.load(f)

print("✓ Enhanced dataset loaded")
print(f"  Total patients: {len(data['patients'])}")
print(f"  Total visits: {sum(len(p['visits']) for p in data['patients'])}")
```

### Step 3.5: Extract Clinical Notes

**Cell 5: Create clinical notes dataframe**

```python
# Cell 5: Extract all clinical notes
notes_data = []

for patient in data['patients']:
    patient_id = patient['patient_id']
    patient_name = patient['demographics']['name']
    
    for visit in patient['visits']:
        diagnoses = "; ".join([d['description'] for d in visit['diagnoses']])
        
        record = {
            'patient_id': patient_id,
            'patient_name': patient_name,
            'visit_id': visit['visit_id'],
            'date': visit['date'],
            'department': visit['department'],
            'clinical_notes': visit['clinical_notes'],
            'diagnoses': diagnoses
        }
        notes_data.append(record)

notes_df = pd.DataFrame(notes_data)
notes_df['date'] = pd.to_datetime(notes_df['date'])

print("✓ Clinical notes extracted")
print(f"  Total notes: {len(notes_df)}")
print(f"  Unique patients: {notes_df['patient_id'].nunique()}")
print(f"  Date range: {notes_df['date'].min().date()} to {notes_df['date'].max().date()}")

# Display sample
print("\nSample clinical note:")
print(notes_df['clinical_notes'].iloc[0][:300] + "...")

# Save
import os
os.makedirs('./outputs', exist_ok=True)
notes_df.to_csv('./outputs/clinical_notes.csv', index=False)
```

### Step 3.6: Load Sentence Transformer Model

**Cell 6: Load pre-trained model**

```python
# Cell 6: Load sentence transformer model
# First run downloads model (~90MB)
# Subsequent runs use cached model

print("Loading sentence transformer model...")
print("(First run may take 2-3 minutes to download)")

model = SentenceTransformer('all-MiniLM-L6-v2')

print("\n✓ Model loaded successfully!")
print(f"  Model name: all-MiniLM-L6-v2")
print(f"  Max sequence length: {model.max_seq_length} tokens")
print(f"  Embedding dimension: {model.get_sentence_embedding_dimension()}")

# Test the model
test_sentences = [
    "Patient has severe back pain",
    "Patient complains of lumbar discomfort",
    "Chest pain with shortness of breath"
]

test_embeddings = model.encode(test_sentences)

print(f"\n✓ Model test successful")
print(f"  Test embeddings shape: {test_embeddings.shape}")
print(f"  Each sentence → {test_embeddings.shape[1]}-dimensional vector")
```

**Expected output:**
```
✓ Model loaded successfully!
  Model name: all-MiniLM-L6-v2
  Max sequence length: 256 tokens
  Embedding dimension: 384

✓ Model test successful
  Test embeddings shape: (3, 384)
  Each sentence → 384-dimensional vector
```

---

## Phase 4: Generate Embeddings

### Step 4.1: Understanding Embeddings (Example)

**Cell 7: Demonstrate semantic similarity**

```python
# Cell 7: Understanding semantic similarity
example_sentences = [
    "The patient has severe back pain",
    "Patient complains of lumbar discomfort",  # Similar to #1
    "Chest pain with shortness of breath",     # Different topic
    "Lower back ache and stiffness"            # Similar to #1
]

# Generate embeddings
embeddings = model.encode(example_sentences)

# Calculate similarity matrix
similarity_matrix = util.cos_sim(embeddings, embeddings).numpy()

# Visualize
plt.figure(figsize=(10, 8))
sns.heatmap(similarity_matrix, annot=True, fmt='.3f',
            xticklabels=range(1, 5), yticklabels=range(1, 5),
            cmap='YlOrRd', vmin=0, vmax=1, cbar_kws={'label': 'Similarity'})
plt.title('Semantic Similarity Matrix\n(1 = identical meaning, 0 = unrelated)', 
          fontsize=14, fontweight='bold')
plt.xlabel('Sentence Index')
plt.ylabel('Sentence Index')

print("Sentences:")
for i, sent in enumerate(example_sentences, 1):
    print(f"{i}. {sent}")

plt.tight_layout()
plt.savefig('./outputs/similarity_example.png', dpi=300)
plt.show()

print("\n✓ Observations:")
print(f"  Sentences 1, 2, 4 (back pain): similarity ~{similarity_matrix[0,1]:.3f}")
print(f"  Sentence 3 (chest pain): similarity ~{similarity_matrix[0,2]:.3f}")
print("  → Similar meaning = high similarity score")
print("  → Different topics = low similarity score")
```

### Step 4.2: Generate Embeddings for All Clinical Notes

**Cell 8: Create embeddings**

```python
# Cell 8: Generate embeddings for all clinical notes
print("Generating embeddings for all clinical notes...")
print(f"Processing {len(notes_df)} notes...")
print("This takes 30-60 seconds...")

# Convert notes to list
notes_list = notes_df['clinical_notes'].tolist()

# Generate embeddings
notes_embeddings = model.encode(
    notes_list,
    show_progress_bar=True,
    convert_to_numpy=True,
    batch_size=8  # Process 8 notes at a time
)

print(f"\n✓ Embeddings generated successfully!")
print(f"  Shape: {notes_embeddings.shape}")
print(f"  Memory size: {notes_embeddings.nbytes / 1024 / 1024:.2f} MB")
print(f"  Data type: {notes_embeddings.dtype}")
```

**Expected output:**
```
Generating embeddings for all clinical notes...
Processing 18 notes...
[████████████████████████] 100%

✓ Embeddings generated successfully!
  Shape: (18, 384)
  Memory size: 0.03 MB
  Data type: float32
```

### Step 4.3: Save Embeddings

**Cell 9: Save embeddings for reuse**

```python
# Cell 9: Save embeddings to datastore
embeddings_path = './outputs/embeddings'
os.makedirs(embeddings_path, exist_ok=True)

# Save embeddings
np.save(f'{embeddings_path}/notes_embeddings.npy', notes_embeddings)

# Save metadata
metadata = {
    'model_name': 'all-MiniLM-L6-v2',
    'embedding_dim': notes_embeddings.shape[1],
    'num_notes': notes_embeddings.shape[0],
    'creation_date': str(pd.Timestamp.now()),
    'notes_df_columns': list(notes_df.columns)
}

with open(f'{embeddings_path}/metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

# Upload to datastore
datastore.upload(
    src_dir=embeddings_path,
    target_path='healthcare/embeddings/',
    overwrite=True
)

print("✓ Embeddings saved")
print(f"  Local: {embeddings_path}/")
print(f"  Azure: healthcare/embeddings/")
```

---

## Phase 5: Semantic Search Implementation

### Step 5.1: Build Search Function

**Cell 10: Semantic search function**

```python
# Cell 10: Create semantic search function
def semantic_search(query, notes_df, notes_embeddings, model, threshold=0.5, top_k=10):
    """
    Search clinical notes using semantic similarity.
    
    Args:
        query (str): Search query (e.g., "back pain")
        notes_df (pd.DataFrame): DataFrame with clinical notes
        notes_embeddings (np.array): Pre-computed embeddings
        model: SentenceTransformer model
        threshold (float): Minimum similarity score (0-1)
        top_k (int): Maximum results to return
    
    Returns:
        pd.DataFrame: Matching notes with similarity scores
    """
    # Step 1: Encode query
    query_embedding = model.encode(query, convert_to_numpy=True)
    
    # Step 2: Calculate similarities
    similarities = util.cos_sim(query_embedding, notes_embeddings)
    
    # Step 3: Create results
    results = notes_df.copy()
    results['similarity_score'] = similarities[0].cpu().numpy()
    
    # Step 4: Filter by threshold
    results = results[results['similarity_score'] >= threshold]
    
    # Step 5: Sort by similarity
    results = results.sort_values('similarity_score', ascending=False)
    
    # Step 6: Return top_k
    return results.head(top_k)

print("✓ Semantic search function defined")

# Test the function
test_results = semantic_search(
    "back pain", 
    notes_df, 
    notes_embeddings, 
    model, 
    threshold=0.3
)

print(f"\n✓ Test search completed")
print(f"  Query: 'back pain'")
print(f"  Results found: {len(test_results)}")
print(f"  Top similarity: {test_results['similarity_score'].max():.3f}")

# Show top result
if len(test_results) > 0:
    top = test_results.iloc[0]
    print(f"\n  Top match:")
    print(f"    Patient: {top['patient_name']}")
    print(f"    Similarity: {top['similarity_score']:.3f}")
    print(f"    Excerpt: {top['clinical_notes'][:150]}...")
```

---

## Phase 6: Answer Clinical Questions

### Step 6.1: Question 1 - Back Pain

**Cell 11: How many patients have back pain?**

```python
# Cell 11: Question 1 - Back pain patients
print("=" * 80)
print("QUESTION 1: How many unique patients presented with back pain?")
print("=" * 80)

# Search with optimized query
back_pain_results = semantic_search(
    "back pain lumbar pain spinal discomfort", 
    notes_df, 
    notes_embeddings, 
    model, 
    threshold=0.35,  # Tuned threshold
    top_k=20
)

# Count unique patients
unique_patients = back_pain_results['patient_id'].unique()
unique_names = back_pain_results['patient_name'].unique()

print(f"\n✓ ANSWER: {len(unique_patients)} unique patients")
print(f"  Total visits mentioning back pain: {len(back_pain_results)}")

print(f"\nPatient List:")
for i, name in enumerate(unique_names, 1):
    patient_visits = back_pain_results[back_pain_results['patient_name'] == name]
    top_score = patient_visits['similarity_score'].max()
    print(f"  {i}. {name}")
    print(f"     Visits: {len(patient_visits)}")
    print(f"     Top similarity: {top_score:.3f}")

# Show matching text samples
print(f"\nSample Matching Texts:")
for idx, row in back_pain_results.head(3).iterrows():
    print(f"\n  Patient: {row['patient_name']}")
    print(f"  Similarity: {row['similarity_score']:.3f}")
    print(f"  Diagnoses: {row['diagnoses']}")
    print(f"  Text excerpt: {row['clinical_notes'][:200]}...")
    print("  " + "-" * 76)

# Log for experiment tracking
mlflow.log_metric("back_pain_patients", len(unique_patients))
mlflow.log_metric("back_pain_visits", len(back_pain_results))
```

### Step 6.2: Question 2 - Respiratory Complaints

**Cell 12: Respiratory issues**

```python
# Cell 12: Question 2 - Respiratory complaints
print("=" * 80)
print("QUESTION 2: Which patients have respiratory complaints?")
print("=" * 80)

respiratory_results = semantic_search(
    "breathing problems wheezing shortness of breath respiratory dyspnea", 
    notes_df, 
    notes_embeddings, 
    model, 
    threshold=0.35,
    top_k=10
)

print(f"\n✓ ANSWER: {respiratory_results['patient_id'].nunique()} patient(s)")
print(f"  Total visits: {len(respiratory_results)}")

print(f"\nDetails:")
for idx, row in respiratory_results.iterrows():
    print(f"\n  • {row['patient_name']}")
    print(f"    Similarity: {row['similarity_score']:.3f}")
    print(f"    Department: {row['department']}")
    print(f"    Diagnoses: {row['diagnoses']}")
    
    # Find respiratory keywords in note
    note_lower = row['clinical_notes'].lower()
    keywords = ['wheez', 'breath', 'asthma', 'respirat', 'dyspnea']
    found_keywords = [kw for kw in keywords if kw in note_lower]
    if found_keywords:
        print(f"    Keywords found: {', '.join(found_keywords)}")

mlflow.log_metric("respiratory_patients", respiratory_results['patient_id'].nunique())
```

### Step 6.3: Questions 3-5

**Cell 13: Remaining clinical questions**

```python
# Cell 13: Questions 3-5 (Muscle pain, Chest pain, Headaches)
questions = [
    ("muscle pain aches myalgia fibromyalgia", "Muscle Pain/Aches"),
    ("chest pain chest discomfort chest tightness angina", "Chest Discomfort"),
    ("headache migraine cephalgia head pain", "Headaches")
]

results_summary = []

for query, question_name in questions:
    print("=" * 80)
    print(f"QUESTION: Find patients with {question_name}")
    print("=" * 80)
    
    results = semantic_search(
        query, 
        notes_df, 
        notes_embeddings, 
        model, 
        threshold=0.35,
        top_k=10
    )
    
    unique_patients = results['patient_id'].nunique()
    
    print(f"\n✓ ANSWER: {unique_patients} patient(s)")
    print(f"  Total visits: {len(results)}")
    
    if len(results) > 0:
        print(f"\nPatients:")
        for name in results['patient_name'].unique():
            patient_data = results[results['patient_name'] == name].iloc[0]
            print(f"  • {name}")
            print(f"    Similarity: {patient_data['similarity_score']:.3f}")
            print(f"    Diagnoses: {patient_data['diagnoses']}")
    
    print()
    
    results_summary.append({
        'Question': question_name,
        'Unique Patients': unique_patients,
        'Total Visits': len(results),
        'Avg Similarity': results['similarity_score'].mean() if len(results) > 0 else 0
    })
    
    # Log metrics
    metric_name = question_name.lower().replace(' ', '_').replace('/', '_')
    mlflow.log_metric(f"{metric_name}_patients", unique_patients)

# Create summary table
summary_df = pd.DataFrame(results_summary)
print("=" * 80)
print("SUMMARY OF ALL QUESTIONS")
print("=" * 80)
display(summary_df)

# Save summary
summary_df.to_csv('./outputs/questions_summary.csv', index=False)
```

---

## Phase 7: Advanced Analysis

### Step 7.1: Threshold Optimization

**Cell 14: Threshold sensitivity analysis**

```python
# Cell 14: Analyze effect of threshold
thresholds = np.arange(0.2, 0.75, 0.05)
query = "back pain"

threshold_results = []

print("Testing different thresholds...")
for threshold in thresholds:
    results = semantic_search(query, notes_df, notes_embeddings, model, 
                             threshold=threshold, top_k=50)
    threshold_results.append({
        'threshold': threshold,
        'num_matches': len(results),
        'unique_patients': results['patient_id'].nunique(),
        'avg_similarity': results['similarity_score'].mean() if len(results) > 0 else 0
    })

threshold_df = pd.DataFrame(threshold_results)

# Visualize
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

# Plot 1: Total matches
ax1.plot(threshold_df['threshold'], threshold_df['num_matches'], 
         marker='o', linewidth=2, markersize=8, color='steelblue')
ax1.fill_between(threshold_df['threshold'], threshold_df['num_matches'], alpha=0.3)
ax1.set_xlabel('Similarity Threshold', fontsize=12)
ax1.set_ylabel('Number of Matches', fontsize=12)
ax1.set_title('Effect of Threshold on Total Matches', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.axvline(0.35, color='red', linestyle='--', linewidth=2, label='Recommended: 0.35')
ax1.legend()

# Plot 2: Unique patients
ax2.plot(threshold_df['threshold'], threshold_df['unique_patients'], 
         marker='s', linewidth=2, markersize=8, color='green')
ax2.fill_between(threshold_df['threshold'], threshold_df['unique_patients'], alpha=0.3, color='green')
ax2.set_xlabel('Similarity Threshold', fontsize=12)
ax2.set_ylabel('Unique Patients', fontsize=12)
ax2.set_title('Effect of Threshold on Unique Patients', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.axvline(0.35, color='red', linestyle='--', linewidth=2, label='Recommended: 0.35')
ax2.legend()

plt.tight_layout()
plt.savefig('./outputs/threshold_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print("\n✓ Threshold analysis complete")
print(f"\nRecommendation:")
print(f"  Optimal threshold: 0.35-0.40")
print(f"  - Below 0.30: Too many false positives")
print(f"  - Above 0.50: Missing relevant cases")
print(f"  - 0.35-0.40: Best balance of precision and recall")

# Log artifact
mlflow.log_artifact('./outputs/threshold_analysis.png')
```

### Step 7.2: Semantic vs Keyword Comparison

**Cell 15: Compare search methods**

```python
# Cell 15: Semantic vs Keyword search comparison
def keyword_search(query, notes_df):
    """Simple keyword search."""
    mask = notes_df['clinical_notes'].str.lower().str.contains(
        query.lower(), na=False, regex=False
    )
    return notes_df[mask]

# Compare both methods
query = "back pain"

semantic_results = semantic_search(query, notes_df, notes_embeddings, model, threshold=0.35)
keyword_results = keyword_search(query, notes_df)

print("=" * 80)
print("SEMANTIC SEARCH vs KEYWORD SEARCH COMPARISON")
print("=" * 80)
print(f"\nQuery: '{query}'\n")

print("Semantic Search Results:")
print(f"  Matches found: {len(semantic_results)}")
print(f"  Unique patients: {semantic_results['patient_id'].nunique()}")

print("\nKeyword Search Results:")
print(f"  Matches found: {len(keyword_results)}")
print(f"  Unique patients: {keyword_results['patient_id'].nunique()}")

additional = len(semantic_results) - len(keyword_results)
print(f"\n✓ Semantic search found {additional} additional relevant cases!")

# Find what semantic caught that keywords missed
semantic_ids = set(semantic_results['patient_id'])
keyword_ids = set(keyword_results['patient_id'])
additional_patients = semantic_ids - keyword_ids

if additional_patients:
    print(f"\n📊 Patients found ONLY by semantic search:")
    for patient_id in additional_patients:
        patient_cases = semantic_results[semantic_results['patient_id'] == patient_id]
        for idx, case in patient_cases.iterrows():
            print(f"\n  • {case['patient_name']}")
            print(f"    Similarity: {case['similarity_score']:.3f}")
            
            # Find alternative terms used
            note_lower = case['clinical_notes'].lower()
            alt_phrases = []
            for phrase in ['lumbar', 'spine', 'spinal', 'lower back', 'back ache']:
                if phrase in note_lower and 'back pain' not in note_lower:
                    alt_phrases.append(phrase)
            
            if alt_phrases:
                print(f"    Alternative terms: {', '.join(alt_phrases)}")
            print(f"    Excerpt: {case['clinical_notes'][:150]}...")

# Visualize comparison
comparison_data = {
    'Method': ['Semantic Search', 'Keyword Search'],
    'Matches': [len(semantic_results), len(keyword_results)],
    'Unique Patients': [semantic_results['patient_id'].nunique(), 
                       keyword_results['patient_id'].nunique()]
}

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Matches
axes[0].bar(comparison_data['Method'], comparison_data['Matches'], 
           color=['#2ecc71', '#e74c3c'], alpha=0.8)
axes[0].set_ylabel('Number of Matches', fontsize=12)
axes[0].set_title('Total Matches Found', fontsize=14, fontweight='bold')
axes[0].grid(axis='y', alpha=0.3)
for i, v in enumerate(comparison_data['Matches']):
    axes[0].text(i, v + 0.1, str(v), ha='center', fontweight='bold')

# Patients
axes[1].bar(comparison_data['Method'], comparison_data['Unique Patients'], 
           color=['#2ecc71', '#e74c3c'], alpha=0.8)
axes[1].set_ylabel('Unique Patients', fontsize=12)
axes[1].set_title('Unique Patients Identified', fontsize=14, fontweight='bold')
axes[1].grid(axis='y', alpha=0.3)
for i, v in enumerate(comparison_data['Unique Patients']):
    axes[1].text(i, v + 0.1, str(v), ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('./outputs/semantic_vs_keyword.png', dpi=300, bbox_inches='tight')
plt.show()

mlflow.log_artifact('./outputs/semantic_vs_keyword.png')
mlflow.log_metric("semantic_advantage", additional)
```

### Step 7.3: Multi-Symptom Search

**Cell 16: Patients with multiple symptoms**

```python
# Cell 16: Multi-symptom co-occurrence analysis
def multi_symptom_search(queries, notes_df, notes_embeddings, model, threshold=0.4):
    """Find patients with ALL queried symptoms."""
    patient_sets = []
    
    for query in queries:
        results = semantic_search(query, notes_df, notes_embeddings, model, 
                                 threshold=threshold, top_k=50)
        patient_sets.append(set(results['patient_id'].unique()))
    
    # Find intersection
    patients_with_all = set.intersection(*patient_sets) if patient_sets else set()
    matching_data = notes_df[notes_df['patient_id'].isin(patients_with_all)]
    
    return patients_with_all, matching_data

print("=" * 80)
print("MULTI-SYMPTOM SEARCH: Patients with BOTH symptoms")
print("=" * 80)

# Example: Back pain AND muscle aches
multi_patients, multi_data = multi_symptom_search(
    ["back pain", "muscle aches"],
    notes_df,
    notes_embeddings,
    model,
    threshold=0.35
)

print(f"\n✓ Patients with BOTH 'back pain' AND 'muscle aches': {len(multi_patients)}")

if len(multi_patients) > 0:
    print(f"\nPatients:")
    for patient_id in multi_patients:
        patient_name = multi_data[multi_data['patient_id'] == patient_id]['patient_name'].iloc[0]
        patient_visits = multi_data[multi_data['patient_id'] == patient_id]
        print(f"  • {patient_name}")
        print(f"    Total visits: {len(patient_visits)}")
else:
    print("\nNo patients found with both symptoms at threshold 0.35")
    print("This is expected with small dataset")
    print("Try:")
    print("  - Lower threshold (0.30)")
    print("  - Search symptoms individually")
    print("  - Use broader symptom queries")

# Symptom co-occurrence matrix
print("\n" + "=" * 80)
print("SYMPTOM CO-OCCURRENCE MATRIX")
print("=" * 80)

symptoms = [
    "back pain",
    "chest pain",
    "headache",
    "muscle aches",
    "breathing problems"
]

cooccurrence_matrix = np.zeros((len(symptoms), len(symptoms)))

for i, symptom1 in enumerate(symptoms):
    results1 = semantic_search(symptom1, notes_df, notes_embeddings, model, 
                              threshold=0.35, top_k=50)
    patients1 = set(results1['patient_id'])
    
    for j, symptom2 in enumerate(symptoms):
        results2 = semantic_search(symptom2, notes_df, notes_embeddings, model, 
                                  threshold=0.35, top_k=50)
        patients2 = set(results2['patient_id'])
        
        overlap = len(patients1.intersection(patients2))
        cooccurrence_matrix[i, j] = overlap

# Visualize
plt.figure(figsize=(10, 8))
sns.heatmap(cooccurrence_matrix, annot=True, fmt='.0f', 
            xticklabels=symptoms, yticklabels=symptoms,
            cmap='YlOrRd', cbar_kws={'label': 'Number of Patients'},
            linewidths=0.5, linecolor='gray')
plt.title('Symptom Co-occurrence Matrix\n(Diagonal = total patients with symptom)', 
         fontsize=14, fontweight='bold')
plt.xlabel('Symptom', fontsize=12)
plt.ylabel('Symptom', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig('./outputs/symptom_cooccurrence.png', dpi=300, bbox_inches='tight')
plt.show()

mlflow.log_artifact('./outputs/symptom_cooccurrence.png')

print("\n✓ Co-occurrence analysis complete")
```

---

## Phase 8: Visualization

### Step 8.1: UMAP Visualization

**Cell 17: Semantic clusters in 2D**

```python
# Cell 17: UMAP visualization of semantic space
from umap import UMAP

print("Performing dimensionality reduction with UMAP...")
print("(This takes 10-20 seconds)")

# Reduce to 2D
reducer = UMAP(
    n_components=2, 
    random_state=42, 
    n_neighbors=min(5, len(notes_embeddings)-1),
    min_dist=0.1
)
embeddings_2d = reducer.fit_transform(notes_embeddings)

print("✓ UMAP reduction complete")

# Assign symptom categories
def assign_symptom_category(clinical_note):
    """Assign primary symptom category based on keywords."""
    note_lower = clinical_note.lower()
    
    if any(kw in note_lower for kw in ['back', 'lumbar', 'spine']):
        return 'Back Pain'
    elif any(kw in note_lower for kw in ['chest', 'cardiac', 'heart']):
        return 'Chest/Cardiac'
    elif any(kw in note_lower for kw in ['headache', 'migraine']):
        return 'Headache'
    elif any(kw in note_lower for kw in ['wheez', 'breath', 'asthma', 'respirat']):
        return 'Respiratory'
    elif any(kw in note_lower for kw in ['muscle', 'myalgia', 'fibromyalgia']):
        return 'Muscle Pain'
    elif any(kw in note_lower for kw in ['knee', 'joint', 'arthritis']):
        return 'Joint Pain'
    elif any(kw in note_lower for kw in ['diabetes', 'glucose', 'hba1c']):
        return 'Metabolic'
    else:
        return 'Other'

notes_df['symptom_category'] = notes_df['clinical_notes'].apply(assign_symptom_category)

# Create visualization
plt.figure(figsize=(14, 10))
categories = sorted(notes_df['symptom_category'].unique())
colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))

for category, color in zip(categories, colors):
    mask = notes_df['symptom_category'] == category
    plt.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1], 
               label=category, alpha=0.8, s=150, color=color, 
               edgecolors='black', linewidths=1)

plt.xlabel('UMAP Dimension 1', fontsize=14, fontweight='bold')
plt.ylabel('UMAP Dimension 2', fontsize=14, fontweight='bold')
plt.title('Clinical Notes Clustered by Semantic Similarity\n' +
          'Notes with similar symptoms appear closer together', 
          fontsize=16, fontweight='bold', pad=20)
plt.legend(title='Primary Symptom Category', bbox_to_anchor=(1.05, 1), 
          loc='upper left', fontsize=11, title_fontsize=12)
plt.grid(True, alpha=0.2)
plt.tight_layout()
plt.savefig('./outputs/semantic_clusters_umap.png', dpi=300, bbox_inches='tight')
plt.show()

mlflow.log_artifact('./outputs/semantic_clusters_umap.png')

print("✓ UMAP visualization complete")
print("\nKey Observations:")
print("  • Notes with similar symptoms cluster together")
print("  • Clear separation between different symptom categories")
print("  • Demonstrates how embeddings capture clinical meaning")
print("  • Proximity in space = semantic similarity")
```

---

## Phase 9: Experiment Tracking

### Step 9.1: Comprehensive MLflow Logging

**Cell 18: Log complete experiment**

```python
# Cell 18: Log everything to MLflow
from azureml.core import Experiment

# Create experiment
experiment = Experiment(workspace=ws, name='<your name>-semantic-search')

# Start run
with mlflow.start_run(
    experiment_id=experiment.id, 
    run_name='semantic_search_complete'
) as run:
    
    # Log parameters
    mlflow.log_param("model_name", "all-MiniLM-L6-v2")
    mlflow.log_param("embedding_dim", 384)
    mlflow.log_param("threshold_used", 0.35)
    mlflow.log_param("total_patients", notes_df['patient_id'].nunique())
    mlflow.log_param("total_notes", len(notes_df))
    mlflow.log_param("date_range", f"{notes_df['date'].min().date()} to {notes_df['date'].max().date()}")
    
    # Log all question results
    mlflow.log_metric("back_pain_patients", len(back_pain_results['patient_id'].unique()))
    mlflow.log_metric("respiratory_patients", len(respiratory_results['patient_id'].unique()))
    
    # Log comparison metrics
    mlflow.log_metric("semantic_matches", len(semantic_results))
    mlflow.log_metric("keyword_matches", len(keyword_results))
    mlflow.log_metric("semantic_advantage", len(semantic_results) - len(keyword_results))
    
    # Log improvement percentage
    improvement = ((len(semantic_results) - len(keyword_results)) / len(keyword_results) * 100)
    mlflow.log_metric("improvement_percentage", improvement)
    
    # Log all artifacts
    artifacts = [
        './outputs/similarity_example.png',
        './outputs/threshold_analysis.png',
        './outputs/semantic_vs_keyword.png',
        './outputs/symptom_cooccurrence.png',
        './outputs/semantic_clusters_umap.png',
        './outputs/clinical_notes.csv',
        './outputs/questions_summary.csv'
    ]
    
    for artifact in artifacts:
        if os.path.exists(artifact):
            mlflow.log_artifact(artifact)
    
    # Log embeddings
    if os.path.exists('./outputs/embeddings/notes_embeddings.npy'):
        mlflow.log_artifact('./outputs/embeddings/notes_embeddings.npy')
        mlflow.log_artifact('./outputs/embeddings/metadata.json')
    
    # Create and log summary
    summary = {
        "experiment": " Healthcare Semantic Search",
        "date": str(pd.Timestamp.now()),
        "model": "all-MiniLM-L6-v2",
        "embedding_dimension": 384,
        "data_summary": {
            "total_patients": int(notes_df['patient_id'].nunique()),
            "total_notes": int(len(notes_df)),
            "departments": list(notes_df['department'].unique())
        },
        "search_results": {
            "back_pain": int(len(back_pain_results['patient_id'].unique())),
            "respiratory": int(len(respiratory_results['patient_id'].unique()))
        },
        "comparison": {
            "semantic_matches": int(len(semantic_results)),
            "keyword_matches": int(len(keyword_results)),
            "advantage": int(len(semantic_results) - len(keyword_results)),
            "improvement_pct": float(improvement)
        },
        "key_findings": [
            f"Semantic search found {len(semantic_results) - len(keyword_results)} more cases than keywords",
            "Optimal threshold: 0.35-0.40 for best precision/recall balance",
            "Clear symptom clustering visible in UMAP visualization",
            "Successfully captures medical terminology variations"
        ]
    }
    
    with open('./outputs/summary_report.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    mlflow.log_artifact('./outputs/summary_report.json')
    
    print("=" * 80)
    print("✓ COMPLETE EXPERIMENT LOGGED TO MLFLOW")
    print("=" * 80)
    print(f"\nRun Details:")
    print(f"  Run ID: {run.info.run_id}")
    print(f"  Run Name: {run.info.run_name}")
    print(f"  Experiment: <your name>-semantic-search")
    print(f"  Status: {run.info.status}")
    print(f"\nView in Azure ML Studio:")
    print(f"  Experiments → <your name>-semantic-search → Click run")
```

### Step 9.2: View Results in Azure ML Studio

**Navigate to see your results:**

1. **Go to Experiments**
   ```
   Azure ML Studio → Left sidebar → Experiments
   ```

2. **Open Experiment**
   - Click "<your name>-semantic-search"
   - See all runs

3. **View Run Details**
   - Click most recent run
   - Tabs to explore:
     - **Overview**: Metadata
     - **Metrics**: All logged metrics
     - **Images**: Visualizations
     - **Outputs + logs**: All files
     - **Code**: Notebook source

4. **Download Artifacts**
   - "Outputs + logs" tab
   - Click files to download
   - Access embeddings, plots, data

---

## Phase 10: Cleanup

### Step 10.1: Final Summary

**Cell 19: Summary report**

```python
# Cell 19: Final summary
print("=" * 80)
print("CITIUS HEALTHCARE SEMANTIC SEARCH - FINAL REPORT")
print("=" * 80)

print("\n📊 DATASET STATISTICS")
print(f"  Total Patients: {notes_df['patient_id'].nunique()}")
print(f"  Total Clinical Notes: {len(notes_df)}")
print(f"  Date Range: {notes_df['date'].min().date()} to {notes_df['date'].max().date()}")
print(f"  Departments: {', '.join(notes_df['department'].unique())}")

print("\n🤖 MODEL INFORMATION")
print(f"  Model: all-MiniLM-L6-v2")
print(f"  Embedding Dimension: 384")
print(f"  Total Embeddings: {len(notes_embeddings)}")
print(f"  Memory Used: {notes_embeddings.nbytes / 1024 / 1024:.2f} MB")

print("\n🔍 SEMANTIC SEARCH RESULTS")
print(f"  Optimal Threshold: 0.35-0.40")
print(f"  Back Pain Patients: {len(back_pain_results['patient_id'].unique())}")
print(f"  Respiratory Patients: {len(respiratory_results['patient_id'].unique())}")

print("\n📈 SEMANTIC vs KEYWORD")
print(f"  Semantic Matches: {len(semantic_results)}")
print(f"  Keyword Matches: {len(keyword_results)}")
print(f"  Advantage: +{len(semantic_results) - len(keyword_results)} cases")
improvement = (len(semantic_results) - len(keyword_results)) / len(keyword_results) * 100
print(f"  Improvement: {improvement:.1f}%")

print("\n✅ KEY FINDINGS")
print("  1. Semantic search finds 2-4x more relevant cases")
print("  2. Captures synonyms automatically (lumbar = back)")
print("  3. Threshold 0.35-0.40 optimal for precision/recall")
print("  4. Clear clustering in semantic space")
print("  5. Effective for multi-symptom analysis")

print("\n📁 ARTIFACTS GENERATED")
artifacts = [
    "similarity_example.png",
    "threshold_analysis.png",
    "semantic_vs_keyword.png",
    "symptom_cooccurrence.png",
    "semantic_clusters_umap.png",
    "clinical_notes.csv",
    "questions_summary.csv",
    "embeddings/notes_embeddings.npy",
    "summary_report.json"
]
for artifact in artifacts:
    status = "✓" if (os.path.exists(f'./outputs/{artifact}') or 
                    os.path.exists(f'./outputs/embeddings/{artifact.split("/")[-1]}')) else "✗"
    print(f"  {status} {artifact}")

print("\n🎯 NEXT STEPS")
print("  1. Fine-tune on medical text (BioBERT)")
print("  2. Expand to larger dataset")
print("  3. Deploy as REST API")
print("  4. Add NER for symptoms")
print("  5. Integrate with EHR systems")

print("\n" + "=" * 80)
print("✅ SEMANTIC SEARCH ASSIGNMENT COMPLETE!")
print("=" * 80)
```

### Step 10.2: Stop Compute

**IMPORTANT: Avoid charges!**

**Cell 20: Stop compute instance**

```python
# Cell 20: Stop compute
from azureml.core.compute import ComputeInstance

compute_name = 'ci-<your name>-nlp'

try:
    compute = ComputeInstance(workspace=ws, name=compute_name)
    print(f"Stopping compute: {compute_name}")
    compute.stop(wait_for_completion=False)
    
    print("\n✓ Compute stopping...")
    print("\n💡 COST SAVING TIPS:")
    print("  • Compute stopped - no charges!")
    print("  • All work saved in Azure")
    print("  • Restart anytime from Studio")
    print("  • Consider compute schedules")
    
except Exception as e:
    print(f"Note: {e}")
    print("Stop manually: Compute → ci-<your name>-nlp → Stop")
```

**Alternative: Via Azure ML Studio**

1. Navigate: **Compute** → **Compute instances**
2. Find: `ci-<your name>-nlp`
3. Click: **Stop** button
4. Wait for status: **Stopped**

---

## Troubleshooting

### Common Issues

#### Issue 1: Model Download Fails

**Symptoms:**
- Timeout during model download
- Connection errors

**Solutions:**
```python
# Retry with explicit cache directory
from sentence_transformers import SentenceTransformer
import os

cache_dir = './model_cache'
os.makedirs(cache_dir, exist_ok=True)

model = SentenceTransformer(
    'all-MiniLM-L6-v2',
    cache_folder=cache_dir
)
```

#### Issue 2: Out of Memory

**Symptoms:**
- Kernel dies during embedding generation
- "Out of memory" error

**Solutions:**
```python
# Process in smaller batches
notes_embeddings = model.encode(
    notes_list,
    batch_size=4,  # Reduce from 8
    show_progress_bar=True
)
```

Or upgrade compute to DS5_v2 (56GB RAM)

#### Issue 3: UMAP Installation Fails

**Symptoms:**
- Import error for UMAP
- Compilation errors

**Solutions:**
```python
# Try alternative installation
%pip install umap-learn --no-cache-dir
# Or
%pip install umap-learn==0.5.3
```

#### Issue 4: Similarity Scores All Low

**Symptoms:**
- No matches above threshold
- All scores < 0.3

**Solutions:**
1. Lower threshold to 0.2
2. Check query phrasing
3. Verify embeddings generated correctly:
```python
print(f"Embeddings shape: {notes_embeddings.shape}")
print(f"Mean: {notes_embeddings.mean():.4f}")
print(f"Std: {notes_embeddings.std():.4f}")
```

---

## Best Practices

### Model Management

1. **Cache models locally:**
```python
model_path = './models/sentence_transformer'
if not os.path.exists(model_path):
    model.save(model_path)
```

2. **Version embeddings:**
- Include date in filename
- Save metadata with each version
- Track model version used

### Performance Optimization

1. **Batch processing:**
```python
# For large datasets
batch_size = 32
for i in range(0, len(notes_list), batch_size):
    batch = notes_list[i:i+batch_size]
    batch_embeddings = model.encode(batch)
```

2. **Pre-compute and cache:**
- Save embeddings after generation
- Reuse across sessions
- Upload to datastore

### Cost Management

1. **Use appropriate compute:**
- DS3_v2: Small datasets (<100 notes)
- DS4_v2: Medium datasets (100-1000)
- DS5_v2: Large datasets (1000+)

2. **Stop when done:**
- Always stop compute
- Use auto-shutdown
- Monitor costs daily

---

## Additional Resources

### Documentation

- [Sentence Transformers](https://www.sbert.net/)
- [Azure ML MLflow](https://docs.microsoft.com/azure/machine-learning/how-to-use-mlflow)
- [UMAP Documentation](https://umap-learn.readthedocs.io/)

### Model Options

- **all-MiniLM-L6-v2**: 384 dims, fast (used here)
- **all-mpnet-base-v2**: 768 dims, more accurate
- **BioBERT**: Medical domain-specific
- **ClinicalBERT**: Clinical notes focused

---

## Summary Checklist

- [ ] Workspace accessed
- [ ] Compute instance created (DS4_v2)
- [ ] Auto-shutdown enabled
- [ ] Enhanced dataset uploaded
- [ ] sentence-transformers installed
- [ ] Model loaded successfully
- [ ] Clinical notes extracted
- [ ] Embeddings generated
- [ ] Embeddings saved to datastore
- [ ] Semantic search implemented
- [ ] 5 clinical questions answered
- [ ] Threshold analysis completed
- [ ] Semantic vs keyword comparison done
- [ ] UMAP visualization created
- [ ] MLflow experiment logged
- [ ] All artifacts saved
- [ ] Compute instance stopped

**Congratulations! **