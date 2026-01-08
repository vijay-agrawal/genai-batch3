# EDA with Azure Machine Learning

## Overview

This guide walks you through executing the complete EDA assignment using Azure Machine Learning Studio. You'll learn to:

- Set up Azure ML workspace and resources
- Upload and manage healthcare data in Azure
- Execute Jupyter notebooks on cloud compute
- Track experiments with MLflow
- Generate and store visualizations
- Implement best practices for cloud-based data science

**Estimated Time:** 3-4 hours (first time), 1-2 hours (subsequent runs)

**Estimated Cost:** $2-5 for complete assignment (with proper cleanup)

---

## Prerequisites

### Required

- Azure subscription
- Basic Python knowledge
- Familiarity with Jupyter notebooks
- Dataset file: `healthcare_data.json`

### Recommended

- Completed local version of EDA assignment (for context)
- Understanding of healthcare data structures
- Basic knowledge of Azure portal

---

## Phase 1: Workspace Setup

### Step 1.1: Create Azure Machine Learning Workspace

**Navigate to Azure Portal:**

1. Go to https://portal.azure.com
2. Sign in with your credentials
3. Click **+ Create a resource**
4. Search for **"Azure Machine Learning"**
5. Click **Create**

**Configure Workspace:**

```
Subscription: [Your subscription]
Resource Group: rg-<your name>-healthcare (Create new) or use the assigned rg
Workspace Name: mlw-<your name>-healthcare
Region: East US (or closest to you)
Storage account: (Auto-created)
Key vault: (Auto-created)
Application insights: (Auto-created)
Container registry: None (Auto-created when needed)
```

**Review and Create:**

1. Click **Review + Create**
2. Wait for validation
3. Click **Create**
4. Wait 3-5 minutes for deployment
5. Click **Go to resource**

### Step 1.2: Launch Azure ML Studio

1. In your workspace resource page
2. Click **Launch studio** button
3. Bookmark the URL: `https://ml.azure.com`
4. This is your main working interface

**Verify Access:**
- You should see the workspace name in top-left
- Left sidebar shows: Home, Notebooks, Automated ML, Designer, Data, etc.

---

## Phase 2: Data Upload

### Step 2.1: Upload Data via Azure ML Studio

**Navigate to Data Assets:**

```
Azure ML Studio → Left sidebar → Data
```

**Create Data Asset:**

1. Click **+ Create**
2. Select **Data asset type**: File
3. Click **Next**

**Configure Basic Info:**

```
Name: healthcare_data
Description:  Healthcare synthetic patient data for EDA training
Type: File
```

4. Click **Next**

**Select Data Source:**

1. Choose **From local files**
2. Click **Next**

**Upload File:**

1. Click **Upload files**
2. Select `healthcare_data.json` from your computer
3. Click **Next**

**Configure Storage:**

```
Datastore: workspaceblobstore (default)
Path: /healthcare/data/
```

4. Click **Next**

**Review and Create:**

1. Verify all settings
2. Click **Create**
3. Wait for upload (10-30 seconds)
4. Status changes to **Complete**

**Verify Upload:**

- Go to Data → Data assets
- You should see "healthcare_data" listed
- Click on it to view details

### Step 2.2: Alternative - Upload via Azure Storage Explorer

**If you prefer using Storage Explorer:**

1. Download Azure Storage Explorer from https://azure.microsoft.com/features/storage-explorer/
2. Install and launch
3. Connect to your Azure account
4. Navigate to: Storage Accounts → [your-workspace-storage] → Blob Containers → azureml-blobstore-xxxxx
5. Create folder: `healthcare/data/`
6. Upload `healthcare_data.json` to this folder

---

## Phase 3: Compute Setup

### Step 3.1: Create Compute Instance

**Navigate to Compute:**

```
Azure ML Studio → Left sidebar → Compute
```

**Create New Compute Instance:**

1. Click **+ New** under "Compute instances" tab
2. Enter configuration:

```
Compute name: ci-<your name>-eda
Virtual machine type: CPU
Virtual machine size: Standard_DS3_v2
  - Cores: 4
  - RAM: 14 GB
  - Storage: 28 GB temp
  - Cost: ~$0.192/hour
```

3. Click **Create**
4. Wait 3-5 minutes for provisioning
5. Status changes: Creating → Running

**Configuration Notes:**

- **Standard_DS3_v2** is sufficient for this assignment
- **Standard_DS2_v2** (7GB RAM) works but may be slower
- **Standard_DS4_v2** (28GB RAM) is faster but costs more (~$0.384/hour)

### Step 3.2: Configure Auto-Shutdown (Important!)

**Set Up Cost-Saving Auto-Shutdown:**

1. In Compute instances list, click your compute name
2. Click **Edit** button
3. Enable **"Enable idle shutdown"**
4. Set: **"Shut down after 30 minutes of inactivity"**
5. Click **Update**

**Cost Savings:**
- Prevents forgetting to stop compute
- Can save $100+ per month
- Doesn't affect saved work

---

## Phase 4: Notebook Execution

### Step 4.1: Create Folder Structure

**Navigate to Notebooks:**

```
Azure ML Studio → Left sidebar → Notebooks
```

**Create Folders:**

1. Click **+ New folder** icon
2. Create: `healthcare_training`
3. Inside that, create:
   - `eda_assignment`
   - `data`
   - `outputs`

**Folder Structure:**

```
Users/[your-name]/
└── healthcare_training/
    ├── data/
    ├── eda_assignment/
    └── outputs/
```

### Step 4.2: Create New Notebook

**In `eda_assignment` folder:**

1. Click **+ Create new file**
2. Name: `01_eda_data_exploration.ipynb`
3. File type: **Notebook**
4. Click **Create**

**Select Compute:**

1. Top-right dropdown: Select **ci-<your name>-eda**
2. Wait ~30 seconds for kernel to start
3. Kernel indicator turns green when ready
4. Should show: **Python 3.10 - SDK v2**

---

## Phase 5: EDA Implementation

### Step 5.1: Install Dependencies

**Cell 1: Install packages**

```python
# Cell 1: Install required packages
%pip install pandas numpy matplotlib seaborn scipy --quiet

print("✓ Packages installed successfully!")
```

Click **Run** button or press **Shift+Enter**

### Step 5.2: Import Libraries and Connect to Workspace

**Cell 2: Import libraries**

```python
# Cell 2: Import libraries
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import re

# Azure ML specific
from azureml.core import Workspace, Dataset, Datastore

print("✓ Imports successful!")
print(f"pandas version: {pd.__version__}")
print(f"numpy version: {np.__version__}")

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', 150)
```

**Cell 3: Connect to workspace**

```python
# Cell 3: Connect to Azure ML workspace
# This automatically detects the workspace when running in Azure ML
ws = Workspace.from_config()

print(f"✓ Connected to workspace")
print(f"  Workspace name: {ws.name}")
print(f"  Resource group: {ws.resource_group}")
print(f"  Location: {ws.location}")
print(f"  Subscription ID: {ws.subscription_id}")
```

### Step 5.3: Load Data from Datastore

**Cell 4: Download data**

```python
# Cell 4: Download data from datastore
datastore = ws.get_default_datastore()
print(f"✓ Using datastore: {datastore.name}")

# Define path
data_path = 'healthcare/data/healthcare_data.json'

# Download file
datastore.download(
    target_path='./data',
    prefix=data_path,
    overwrite=True
)

print("✓ Data downloaded successfully!")
print(f"  Location: ./data/{data_path}")
```

**Cell 5: Load JSON data**

```python
# Cell 5: Load JSON data
file_path = './data/healthcare/data/healthcare_data.json'

with open(file_path, 'r') as f:
    data = json.load(f)

print("✓ Data loaded successfully!")
print(f"  Total patients: {len(data['patients'])}")
print(f"  Data version: {data['metadata']['version']}")
print(f"  Date range: {data['metadata']['date_range']}")
```

### Step 5.4: Initial Data Exploration

**Cell 6: Explore structure**

```python
# Cell 6: Explore JSON structure
print("=" * 80)
print("DATA STRUCTURE EXPLORATION")
print("=" * 80)

print("\n1. Top-level keys:")
print(f"   {list(data.keys())}")

print("\n2. Patient record keys:")
print(f"   {list(data['patients'][0].keys())}")

print("\n3. Visit record keys:")
print(f"   {list(data['patients'][0]['visits'][0].keys())}")

print("\n4. Sample patient (first 500 characters):")
print(json.dumps(data['patients'][0], indent=2)[:500] + "...")

print("\n5. Lab results structure:")
if data['patients'][0]['visits'][0]['lab_results']:
    print(f"   {list(data['patients'][0]['visits'][0]['lab_results'][0].keys())}")
```

### Step 5.5: Create Patient Summary DataFrame

**Cell 7: Patient-level data**

```python
# Cell 7: Create patient summary dataframe
patient_data = []

for patient in data['patients']:
    record = {
        'patient_id': patient['patient_id'],
        'name': patient['demographics']['name'],
        'age': patient['demographics']['age'],
        'gender': patient['demographics']['gender'],
        'city': patient['demographics']['contact']['address']['city'],
        'insurance_provider': patient['insurance']['provider'],
        'deductible_met': patient['insurance']['deductible_met'],
        'num_chronic_conditions': len(patient['medical_history']['chronic_conditions']),
        'num_allergies': len(patient['medical_history']['allergies']),
        'num_visits': len(patient['visits'])
    }
    patient_data.append(record)

patients_df = pd.DataFrame(patient_data)

print("✓ Patient summary created")
print(f"  Total patients: {len(patients_df)}")
print(f"  Columns: {list(patients_df.columns)}")

display(patients_df)

# Save to outputs
os.makedirs('./outputs', exist_ok=True)
patients_df.to_csv('./outputs/patients_summary.csv', index=False)
print("\n✓ Saved to ./outputs/patients_summary.csv")
```

### Step 5.6: Flatten Visits Data

**Cell 8: Visit-level dataframe**

```python
# Cell 8: Flatten visits data
visits_data = []

for patient in data['patients']:
    patient_id = patient['patient_id']
    patient_name = patient['demographics']['name']
    patient_age = patient['demographics']['age']
    
    for visit in patient['visits']:
        visit_record = {
            'patient_id': patient_id,
            'patient_name': patient_name,
            'patient_age': patient_age,
            'visit_id': visit['visit_id'],
            'date': visit['date'],
            'type': visit['type'],
            'department': visit['department'],
            'provider_name': visit['provider']['name'],
            'provider_specialty': visit['provider']['specialty'],
            # Vitals
            'blood_pressure': visit['vitals']['blood_pressure'],
            'heart_rate': visit['vitals']['heart_rate'],
            'temperature': visit['vitals']['temperature'],
            'weight_lbs': visit['vitals']['weight_lbs'],
            'height_inches': visit['vitals']['height_inches'],
            'bmi': visit['vitals']['bmi'],
            # Billing
            'total_charge': visit['billing']['total_charge'],
            'insurance_paid': visit['billing']['insurance_paid'],
            'patient_responsibility': visit['billing']['patient_responsibility'],
            # Notes
            'clinical_notes': visit['clinical_notes'],
            # Diagnosis count
            'num_diagnoses': len(visit['diagnoses']),
            'num_medications': len(visit['medications_prescribed']),
            'num_lab_tests': len(visit['lab_results'])
        }
        visits_data.append(visit_record)

visits_df = pd.DataFrame(visits_data)
visits_df['date'] = pd.to_datetime(visits_df['date'])

# Extract systolic BP for analysis
visits_df['systolic_bp'] = visits_df['blood_pressure'].apply(
    lambda x: int(x.split('/')[0]) if pd.notna(x) else None
)
visits_df['diastolic_bp'] = visits_df['blood_pressure'].apply(
    lambda x: int(x.split('/')[1]) if pd.notna(x) else None
)

print("✓ Visits dataframe created")
print(f"  Total visits: {len(visits_df)}")
print(f"  Date range: {visits_df['date'].min().date()} to {visits_df['date'].max().date()}")
print(f"  Departments: {visits_df['department'].unique()}")
print(f"  Visit types: {visits_df['type'].unique()}")

display(visits_df.head())

# Save
visits_df.to_csv('./outputs/visits_flattened.csv', index=False)
print("\n✓ Saved to ./outputs/visits_flattened.csv")
```

### Step 5.7: Explode Lab Results

**Cell 9: Lab results dataframe**

```python
# Cell 9: Explode lab results
lab_results_data = []

for patient in data['patients']:
    patient_id = patient['patient_id']
    patient_name = patient['demographics']['name']
    
    for visit in patient['visits']:
        visit_id = visit['visit_id']
        visit_date = visit['date']
        
        for lab in visit['lab_results']:
            lab_record = {
                'patient_id': patient_id,
                'patient_name': patient_name,
                'visit_id': visit_id,
                'visit_date': visit_date,
                'test_name': lab['test_name'],
                'value': lab['value'],
                'unit': lab['unit'],
                'reference_range': lab['reference_range'],
                'status': lab['status']
            }
            lab_results_data.append(lab_record)

labs_df = pd.DataFrame(lab_results_data)
labs_df['visit_date'] = pd.to_datetime(labs_df['visit_date'])
labs_df['value_numeric'] = pd.to_numeric(labs_df['value'], errors='coerce')

print("✓ Lab results dataframe created")
print(f"  Total lab tests: {len(labs_df)}")
print(f"  Unique test types: {labs_df['test_name'].nunique()}")
print(f"\nTest types:")
for test in sorted(labs_df['test_name'].unique()):
    count = len(labs_df[labs_df['test_name'] == test])
    print(f"  - {test}: {count} tests")

print(f"\nStatus distribution:")
print(labs_df['status'].value_counts())

display(labs_df.head(10))

# Save
labs_df.to_csv('./outputs/lab_results_exploded.csv', index=False)
print("\n✓ Saved to ./outputs/lab_results_exploded.csv")
```

### Step 5.8: Regex Pattern Extraction

**Cell 10: Extract patterns from clinical notes**

```python
# Cell 10: Regex pattern extraction
def extract_diet_recommendations(clinical_notes):
    """Extract dietary recommendations from clinical notes."""
    if not clinical_notes or pd.isna(clinical_notes):
        return None
    
    pattern = r'DIET:\s*([^.]+\.?)'
    match = re.search(pattern, clinical_notes)
    
    if match:
        return match.group(1).strip()
    return None

def extract_followup_timing(clinical_notes):
    """Extract follow-up timing from clinical notes."""
    if not clinical_notes or pd.isna(clinical_notes):
        return None
    
    pattern = r'F/U:\s*([^.]+\.?)'
    match = re.search(pattern, clinical_notes)
    
    if match:
        return match.group(1).strip()
    return None

def extract_assessment(clinical_notes):
    """Extract assessment from clinical notes."""
    if not clinical_notes or pd.isna(clinical_notes):
        return None
    
    pattern = r'ASSESSMENT:\s*([^.]+\.)'
    match = re.search(pattern, clinical_notes)
    
    if match:
        return match.group(1).strip()
    return None

# Apply extractions
visits_df['diet_recommendation'] = visits_df['clinical_notes'].apply(extract_diet_recommendations)
visits_df['followup_timing'] = visits_df['clinical_notes'].apply(extract_followup_timing)
visits_df['assessment'] = visits_df['clinical_notes'].apply(extract_assessment)

print("✓ Regex extractions complete")
print(f"\nDiet recommendations found: {visits_df['diet_recommendation'].notna().sum()} visits")
print(f"Follow-up schedules found: {visits_df['followup_timing'].notna().sum()} visits")
print(f"Assessments found: {visits_df['assessment'].notna().sum()} visits")

print("\nSample diet recommendations:")
diet_samples = visits_df[visits_df['diet_recommendation'].notna()][
    ['patient_name', 'date', 'diet_recommendation']
].head(3)
display(diet_samples)

print("\nSample follow-up schedules:")
followup_samples = visits_df[visits_df['followup_timing'].notna()][
    ['patient_name', 'date', 'followup_timing']
].head(3)
display(followup_samples)

# Save updated visits
visits_df.to_csv('./outputs/visits_with_extractions.csv', index=False)
```

### Step 5.9: Feature Engineering - has_diabetes

**Cell 11: Create has_diabetes feature**

```python
# Cell 11: Feature engineering - has_diabetes flag
def check_patient_has_diabetes(patient_data):
    """
    Check if patient has diabetes diagnosis.
    Diabetes ICD-10 codes: E10 (Type 1), E11 (Type 2), O24 (Gestational)
    """
    diabetes_codes = ['E10', 'E11', 'O24']
    
    for visit in patient_data['visits']:
        for diagnosis in visit['diagnoses']:
            icd10_code = diagnosis['icd10_code']
            if any(icd10_code.startswith(code) for code in diabetes_codes):
                return True
    return False

def calculate_avg_glucose(patient_data):
    """Calculate average glucose levels across all visits."""
    glucose_tests = []
    for visit in patient_data['visits']:
        for lab in visit['lab_results']:
            if 'Glucose' in lab['test_name']:
                glucose_tests.append(lab['value'])
    return np.mean(glucose_tests) if glucose_tests else None

def calculate_avg_hba1c(patient_data):
    """Calculate average HbA1c across all visits."""
    hba1c_tests = []
    for visit in patient_data['visits']:
        for lab in visit['lab_results']:
            if lab['test_name'] == 'HbA1c':
                hba1c_tests.append(lab['value'])
    return np.mean(hba1c_tests) if hba1c_tests else None

# Create enhanced patient summary
patient_summary = []

for patient in data['patients']:
    summary = {
        'patient_id': patient['patient_id'],
        'name': patient['demographics']['name'],
        'age': patient['demographics']['age'],
        'gender': patient['demographics']['gender'],
        'has_diabetes': check_patient_has_diabetes(patient),
        'num_visits': len(patient['visits']),
        'chronic_conditions_count': len(patient['medical_history']['chronic_conditions']),
        'chronic_conditions_list': ', '.join(patient['medical_history']['chronic_conditions']),
        'avg_glucose': calculate_avg_glucose(patient),
        'avg_hba1c': calculate_avg_hba1c(patient)
    }
    patient_summary.append(summary)

patients_enhanced_df = pd.DataFrame(patient_summary)

print("✓ Enhanced patient features created")
print(f"\nDiabetes Status:")
print(f"  Patients with diabetes: {patients_enhanced_df['has_diabetes'].sum()}")
print(f"  Patients without diabetes: {(~patients_enhanced_df['has_diabetes']).sum()}")
print(f"  Percentage with diabetes: {patients_enhanced_df['has_diabetes'].sum() / len(patients_enhanced_df) * 100:.1f}%")

print(f"\nAverage Glucose Levels:")
print(f"  Diabetic patients: {patients_enhanced_df[patients_enhanced_df['has_diabetes']]['avg_glucose'].mean():.1f} mg/dL")
print(f"  Non-diabetic patients: {patients_enhanced_df[~patients_enhanced_df['has_diabetes']]['avg_glucose'].mean():.1f} mg/dL")

display(patients_enhanced_df)

# Save
patients_enhanced_df.to_csv('./outputs/patients_enhanced_features.csv', index=False)
print("\n✓ Saved to ./outputs/patients_enhanced_features.csv")
```

---

## Phase 6: Visualization

### Step 6.1: Create Density Plots

**Cell 12: Distribution analysis**

```python
# Cell 12: Density plots for distribution analysis
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Merge visits with has_diabetes flag
visits_merged = visits_df.merge(
    patients_enhanced_df[['patient_id', 'has_diabetes']], 
    on='patient_id'
)

# BMI distribution
sns.kdeplot(data=visits_merged, x='bmi', hue='has_diabetes', 
            fill=True, alpha=0.5, ax=axes[0,0], palette=['blue', 'red'])
axes[0,0].set_title('BMI Distribution by Diabetes Status', fontsize=14, fontweight='bold')
axes[0,0].axvline(25, color='orange', linestyle='--', linewidth=2, label='Overweight (25)')
axes[0,0].axvline(30, color='red', linestyle='--', linewidth=2, label='Obese (30)')
axes[0,0].set_xlabel('BMI')
axes[0,0].legend()

# Systolic BP distribution
sns.kdeplot(data=visits_merged, x='systolic_bp', hue='has_diabetes',
            fill=True, alpha=0.5, ax=axes[0,1], palette=['blue', 'red'])
axes[0,1].set_title('Systolic Blood Pressure Distribution', fontsize=14, fontweight='bold')
axes[0,1].axvline(140, color='red', linestyle='--', linewidth=2, label='Stage 1 HTN (140)')
axes[0,1].set_xlabel('Systolic BP (mmHg)')
axes[0,1].legend()

# Heart rate distribution
sns.kdeplot(data=visits_merged, x='heart_rate', hue='has_diabetes',
            fill=True, alpha=0.5, ax=axes[1,0], palette=['blue', 'red'])
axes[1,0].set_title('Heart Rate Distribution', fontsize=14, fontweight='bold')
axes[1,0].axvline(100, color='red', linestyle='--', linewidth=2, label='Tachycardia (100)')
axes[1,0].set_xlabel('Heart Rate (bpm)')
axes[1,0].legend()

# Glucose distribution
glucose_df = labs_df[labs_df['test_name'].str.contains('Glucose', na=False)].copy()
glucose_merged = glucose_df.merge(
    patients_enhanced_df[['patient_id', 'has_diabetes']], 
    on='patient_id'
)
sns.kdeplot(data=glucose_merged, x='value_numeric', hue='has_diabetes',
            fill=True, alpha=0.5, ax=axes[1,1], palette=['blue', 'red'])
axes[1,1].set_title('Glucose Levels Distribution', fontsize=14, fontweight='bold')
axes[1,1].axvline(100, color='orange', linestyle='--', linewidth=2, label='Prediabetes (100)')
axes[1,1].axvline(126, color='red', linestyle='--', linewidth=2, label='Diabetes (126)')
axes[1,1].set_xlabel('Glucose (mg/dL)')
axes[1,1].legend()

plt.suptitle('Distribution Analysis -  Healthcare EDA', 
             fontsize=16, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig('./outputs/density_plots.png', dpi=300, bbox_inches='tight')
plt.show()

print("✓ Density plots created and saved")
```

### Step 6.2: Create Box Plots

**Cell 13: Box plots for outlier detection**

```python
# Cell 13: Box plots for outlier detection and group comparison
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# HbA1c by diabetes status
hba1c_df = labs_df[labs_df['test_name']=='HbA1c'].copy()
hba1c_merged = hba1c_df.merge(
    patients_enhanced_df[['patient_id', 'has_diabetes']], 
    on='patient_id'
)
sns.boxplot(data=hba1c_merged, x='has_diabetes', y='value_numeric', 
            palette=['lightblue', 'salmon'], ax=axes[0,0])
axes[0,0].set_title('HbA1c Levels by Diabetes Status', fontsize=12, fontweight='bold')
axes[0,0].axhline(6.5, color='red', linestyle='--', linewidth=1, label='Diabetes threshold')
axes[0,0].set_ylabel('HbA1c (%)')
axes[0,0].set_xlabel('Has Diabetes')
axes[0,0].legend()

# BMI by department
sns.boxplot(data=visits_merged, x='department', y='bmi', 
            palette='Set2', ax=axes[0,1])
axes[0,1].set_title('BMI Distribution by Department', fontsize=12, fontweight='bold')
axes[0,1].set_xticklabels(axes[0,1].get_xticklabels(), rotation=45, ha='right')
axes[0,1].axhline(25, color='orange', linestyle='--', alpha=0.5)
axes[0,1].axhline(30, color='red', linestyle='--', alpha=0.5)
axes[0,1].set_ylabel('BMI')

# Systolic BP by diabetes
sns.boxplot(data=visits_merged, x='has_diabetes', y='systolic_bp',
            palette=['lightblue', 'salmon'], ax=axes[0,2])
axes[0,2].set_title('Systolic BP by Diabetes Status', fontsize=12, fontweight='bold')
axes[0,2].axhline(140, color='red', linestyle='--', linewidth=1)
axes[0,2].set_ylabel('Systolic BP (mmHg)')
axes[0,2].set_xlabel('Has Diabetes')

# Glucose progression over visits
glucose_merged['visit_num'] = glucose_merged.groupby('patient_id').cumcount() + 1
diabetic_glucose = glucose_merged[glucose_merged['has_diabetes']==True]
if len(diabetic_glucose) > 0:
    sns.boxplot(data=diabetic_glucose, x='visit_num', y='value_numeric', 
                palette='coolwarm', ax=axes[1,0])
    axes[1,0].set_title('Glucose Over Sequential Visits\n(Diabetic Patients)', 
                       fontsize=12, fontweight='bold')
    axes[1,0].set_xlabel('Visit Number')
    axes[1,0].set_ylabel('Glucose (mg/dL)')

# Weight by age group and diabetes
visits_merged['age_group'] = pd.cut(visits_merged['patient_age'], 
                                     bins=[0, 40, 60, 100], 
                                     labels=['<40', '40-60', '>60'])
sns.boxplot(data=visits_merged, x='age_group', y='weight_lbs',
            hue='has_diabetes', palette=['lightblue', 'salmon'], ax=axes[1,1])
axes[1,1].set_title('Weight by Age Group and Diabetes', fontsize=12, fontweight='bold')
axes[1,1].set_ylabel('Weight (lbs)')
axes[1,1].set_xlabel('Age Group')

# Total charges by department
sns.boxplot(data=visits_merged, x='department', y='total_charge',
            palette='Set3', ax=axes[1,2])
axes[1,2].set_title('Healthcare Costs by Department', fontsize=12, fontweight='bold')
axes[1,2].set_xticklabels(axes[1,2].get_xticklabels(), rotation=45, ha='right')
axes[1,2].set_ylabel('Total Charge ($)')

plt.suptitle('Box Plot Analysis - Outlier Detection and Group Comparison', 
             fontsize=16, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig('./outputs/box_plots.png', dpi=300, bbox_inches='tight')
plt.show()

print("✓ Box plots created and saved")
```

### Step 6.3: Key Insights Visualization

**Cell 14: Summary visualizations**

```python
# Cell 14: Create summary dashboard
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# 1. Diabetes prevalence
ax1 = fig.add_subplot(gs[0, 0])
diabetes_counts = patients_enhanced_df['has_diabetes'].value_counts()
ax1.pie(diabetes_counts, labels=['Without Diabetes', 'With Diabetes'], 
        autopct='%1.1f%%', colors=['lightblue', 'salmon'], startangle=90)
ax1.set_title('Diabetes Prevalence', fontweight='bold')

# 2. Visit types distribution
ax2 = fig.add_subplot(gs[0, 1])
visit_type_counts = visits_df['type'].value_counts()
ax2.bar(range(len(visit_type_counts)), visit_type_counts.values, color='steelblue')
ax2.set_xticks(range(len(visit_type_counts)))
ax2.set_xticklabels(visit_type_counts.index, rotation=45, ha='right')
ax2.set_title('Visit Types Distribution', fontweight='bold')
ax2.set_ylabel('Count')

# 3. Department distribution
ax3 = fig.add_subplot(gs[0, 2])
dept_counts = visits_df['department'].value_counts()
ax3.barh(range(len(dept_counts)), dept_counts.values, color='coral')
ax3.set_yticks(range(len(dept_counts)))
ax3.set_yticklabels(dept_counts.index)
ax3.set_title('Visits by Department', fontweight='bold')
ax3.set_xlabel('Number of Visits')

# 4. BMI comparison
ax4 = fig.add_subplot(gs[1, 0])
diabetic_bmi = visits_merged[visits_merged['has_diabetes']==True]['bmi']
non_diabetic_bmi = visits_merged[visits_merged['has_diabetes']==False]['bmi']
ax4.hist([non_diabetic_bmi, diabetic_bmi], label=['No Diabetes', 'Diabetes'], 
         color=['lightblue', 'salmon'], alpha=0.7, bins=10)
ax4.set_xlabel('BMI')
ax4.set_ylabel('Frequency')
ax4.set_title('BMI Distribution by Diabetes Status', fontweight='bold')
ax4.legend()
ax4.axvline(25, color='orange', linestyle='--', label='Overweight')
ax4.axvline(30, color='red', linestyle='--', label='Obese')

# 5. Lab test status distribution
ax5 = fig.add_subplot(gs[1, 1])
status_counts = labs_df['status'].value_counts()
colors_map = {'HIGH': 'red', 'NORMAL': 'green', 'LOW': 'blue', 'BORDERLINE': 'orange'}
colors = [colors_map.get(status, 'gray') for status in status_counts.index]
ax5.bar(status_counts.index, status_counts.values, color=colors)
ax5.set_title('Lab Test Results Status', fontweight='bold')
ax5.set_ylabel('Count')
ax5.set_xlabel('Status')

# 6. Healthcare costs by diabetes status
ax6 = fig.add_subplot(gs[1, 2])
cost_by_diabetes = visits_merged.groupby('has_diabetes')['total_charge'].mean()
ax6.bar(['No Diabetes', 'Diabetes'], cost_by_diabetes.values, 
        color=['lightblue', 'salmon'])
ax6.set_title('Average Visit Cost by Diabetes Status', fontweight='bold')
ax6.set_ylabel('Average Total Charge ($)')
ax6.grid(axis='y', alpha=0.3)

# 7. Age distribution
ax7 = fig.add_subplot(gs[2, 0])
patients_enhanced_df['age'].hist(bins=15, color='steelblue', alpha=0.7, ax=ax7)
ax7.set_xlabel('Age')
ax7.set_ylabel('Frequency')
ax7.set_title('Patient Age Distribution', fontweight='bold')

# 8. HbA1c trends (for patients with multiple tests)
ax8 = fig.add_subplot(gs[2, 1:])
hba1c_timeline = hba1c_merged.sort_values('visit_date')
for patient_id in hba1c_timeline['patient_id'].unique():
    patient_data = hba1c_timeline[hba1c_timeline['patient_id'] == patient_id]
    if len(patient_data) >= 2:  # Only plot if multiple data points
        has_diabetes = patient_data['has_diabetes'].iloc[0]
        color = 'salmon' if has_diabetes else 'lightblue'
        ax8.plot(patient_data['visit_date'], patient_data['value_numeric'], 
                marker='o', linestyle='-', linewidth=2, markersize=8, 
                alpha=0.7, color=color)

ax8.axhline(6.5, color='red', linestyle='--', linewidth=2, label='Diabetes threshold (6.5%)')
ax8.set_xlabel('Date')
ax8.set_ylabel('HbA1c (%)')
ax8.set_title('HbA1c Trends Over Time (Patients with Multiple Tests)', fontweight='bold')
ax8.legend(['Diabetes threshold'], loc='upper right')
ax8.grid(True, alpha=0.3)

plt.suptitle(' Healthcare - EDA Summary Dashboard', 
             fontsize=18, fontweight='bold', y=0.995)
plt.savefig('./outputs/eda_summary_dashboard.png', dpi=300, bbox_inches='tight')
plt.show()

print("✓ Summary dashboard created and saved")
```

---

## Phase 7: Experiment Tracking

### Step 7.1: Log Metrics with MLflow

**Cell 15: Experiment tracking**

```python
# Cell 15: Log experiment with MLflow
import mlflow
from azureml.core import Experiment

# Create or get experiment
experiment = Experiment(workspace=ws, name='<your name>-healthcare-eda')

# Start MLflow run
with mlflow.start_run(experiment_id=experiment.id, run_name='complete_eda_analysis') as run:
    
    # Log parameters
    mlflow.log_param("dataset_version", "1.0")
    mlflow.log_param("total_patients", len(patients_enhanced_df))
    mlflow.log_param("total_visits", len(visits_df))
    mlflow.log_param("total_lab_tests", len(labs_df))
    mlflow.log_param("date_range_start", str(visits_df['date'].min().date()))
    mlflow.log_param("date_range_end", str(visits_df['date'].max().date()))
    
    # Log key metrics
    mlflow.log_metric("patients_with_diabetes", 
                     int(patients_enhanced_df['has_diabetes'].sum()))
    mlflow.log_metric("diabetes_percentage", 
                     float(patients_enhanced_df['has_diabetes'].sum() / len(patients_enhanced_df) * 100))
    mlflow.log_metric("avg_visits_per_patient", 
                     float(len(visits_df) / len(patients_enhanced_df)))
    mlflow.log_metric("avg_age", 
                     float(patients_enhanced_df['age'].mean()))
    
    # BMI metrics
    mlflow.log_metric("avg_bmi_diabetic", 
                     float(visits_merged[visits_merged['has_diabetes']==True]['bmi'].mean()))
    mlflow.log_metric("avg_bmi_non_diabetic", 
                     float(visits_merged[visits_merged['has_diabetes']==False]['bmi'].mean()))
    
    # Glucose metrics
    diabetic_glucose = patients_enhanced_df[patients_enhanced_df['has_diabetes']]['avg_glucose'].mean()
    non_diabetic_glucose = patients_enhanced_df[~patients_enhanced_df['has_diabetes']]['avg_glucose'].mean()
    mlflow.log_metric("avg_glucose_diabetic", float(diabetic_glucose))
    mlflow.log_metric("avg_glucose_non_diabetic", float(non_diabetic_glucose))
    
    # Cost metrics
    avg_cost_diabetic = visits_merged[visits_merged['has_diabetes']==True]['total_charge'].mean()
    avg_cost_non_diabetic = visits_merged[visits_merged['has_diabetes']==False]['total_charge'].mean()
    mlflow.log_metric("avg_visit_cost_diabetic", float(avg_cost_diabetic))
    mlflow.log_metric("avg_visit_cost_non_diabetic", float(avg_cost_non_diabetic))
    
    # Lab test metrics
    mlflow.log_metric("high_lab_results_count", 
                     int((labs_df['status'] == 'HIGH').sum()))
    mlflow.log_metric("normal_lab_results_count", 
                     int((labs_df['status'] == 'NORMAL').sum()))
    
    # Log all visualizations as artifacts
    artifact_files = [
        './outputs/density_plots.png',
        './outputs/box_plots.png',
        './outputs/eda_summary_dashboard.png'
    ]
    
    for artifact in artifact_files:
        if os.path.exists(artifact):
            mlflow.log_artifact(artifact)
    
    # Log processed datasets
    data_files = [
        './outputs/patients_summary.csv',
        './outputs/visits_flattened.csv',
        './outputs/lab_results_exploded.csv',
        './outputs/patients_enhanced_features.csv',
        './outputs/visits_with_extractions.csv'
    ]
    
    for data_file in data_files:
        if os.path.exists(data_file):
            mlflow.log_artifact(data_file)
    
    # Create and log summary report
    summary_report = {
        "experiment_name": " Healthcare EDA",
        "run_date": str(datetime.now()),
        "data_summary": {
            "total_patients": int(len(patients_enhanced_df)),
            "total_visits": int(len(visits_df)),
            "total_lab_tests": int(len(labs_df)),
            "date_range": f"{visits_df['date'].min().date()} to {visits_df['date'].max().date()}"
        },
        "key_findings": {
            "diabetes_prevalence": f"{patients_enhanced_df['has_diabetes'].sum() / len(patients_enhanced_df) * 100:.1f}%",
            "avg_bmi_difference": f"{visits_merged[visits_merged['has_diabetes']==True]['bmi'].mean() - visits_merged[visits_merged['has_diabetes']==False]['bmi'].mean():.1f}",
            "avg_glucose_difference": f"{diabetic_glucose - non_diabetic_glucose:.1f} mg/dL",
            "cost_impact": f"${avg_cost_diabetic - avg_cost_non_diabetic:.2f} per visit"
        }
    }
    
    with open('./outputs/summary_report.json', 'w') as f:
        json.dump(summary_report, f, indent=2)
    
    mlflow.log_artifact('./outputs/summary_report.json')
    
    print("✓ Complete experiment logged to MLflow")
    print(f"\nRun Details:")
    print(f"  Run ID: {run.info.run_id}")
    print(f"  Run Name: {run.info.run_name}")
    print(f"  Experiment ID: {run.info.experiment_id}")
    print(f"  Status: {run.info.status}")
    print(f"\nView in Azure ML Studio:")
    print(f"  Experiments → <your name>-healthcare-eda → Click on run")
```

### Step 7.2: View Results in Azure ML Studio

**Navigate to view your results:**

1. **Go to Experiments**
   ```
   Azure ML Studio → Left sidebar → Experiments
   ```

2. **Open Your Experiment**
   - Click on "<your name>-healthcare-eda"
   - You'll see all runs listed

3. **View Run Details**
   - Click on the most recent run
   - Explore tabs:
     - **Overview**: Run metadata and description
     - **Metrics**: All logged metrics with charts
     - **Images**: Visualizations (if any logged as images)
     - **Outputs + logs**: All artifacts including CSV files and plots
     - **Code**: The notebook code used

4. **Download Artifacts**
   - Navigate to **"Outputs + logs"** tab
   - Click **"outputs"** folder
   - See all your generated files
   - Download any file by clicking on it

5. **View Metrics Charts**
   - Navigate to **"Metrics"** tab
   - See all logged metrics
   - Azure ML automatically creates charts
   - Compare multiple runs side-by-side

---

## Phase 8: Cleanup

### Step 8.1: Save Your Work

**Cell 16: Final summary**

```python
# Cell 16: Final summary and verification
print("=" * 80)
print("CITIUS HEALTHCARE EDA - COMPLETION SUMMARY")
print("=" * 80)

print("\n✓ DATA PROCESSING COMPLETE")
print(f"  Patients analyzed: {len(patients_enhanced_df)}")
print(f"  Visits processed: {len(visits_df)}")
print(f"  Lab tests analyzed: {len(labs_df)}")

print("\n✓ FEATURES ENGINEERED")
print(f"  has_diabetes flag: Created")
print(f"  Regex extractions: {visits_df['diet_recommendation'].notna().sum()} diet recommendations")
print(f"  Regex extractions: {visits_df['followup_timing'].notna().sum()} follow-up schedules")

print("\n✓ VISUALIZATIONS CREATED")
print(f"  Density plots: ./outputs/density_plots.png")
print(f"  Box plots: ./outputs/box_plots.png")
print(f"  Summary dashboard: ./outputs/eda_summary_dashboard.png")

print("\n✓ DATASETS SAVED")
saved_files = [
    'patients_summary.csv',
    'visits_flattened.csv',
    'lab_results_exploded.csv',
    'patients_enhanced_features.csv',
    'visits_with_extractions.csv'
]
for filename in saved_files:
    path = f'./outputs/{filename}'
    if os.path.exists(path):
        size_kb = os.path.getsize(path) / 1024
        print(f"  {filename}: {size_kb:.1f} KB")

print("\n✓ EXPERIMENT LOGGED")
print(f"  Experiment: <your name>-healthcare-eda")
print(f"  All metrics and artifacts saved to Azure ML")

print("\n✓ KEY FINDINGS")
print(f"  Diabetes prevalence: {patients_enhanced_df['has_diabetes'].sum() / len(patients_enhanced_df) * 100:.1f}%")
print(f"  Avg BMI (diabetic): {visits_merged[visits_merged['has_diabetes']==True]['bmi'].mean():.1f}")
print(f"  Avg BMI (non-diabetic): {visits_merged[visits_merged['has_diabetes']==False]['bmi'].mean():.1f}")

diabetic_glucose = patients_enhanced_df[patients_enhanced_df['has_diabetes']]['avg_glucose'].mean()
non_diabetic_glucose = patients_enhanced_df[~patients_enhanced_df['has_diabetes']]['avg_glucose'].mean()
print(f"  Avg glucose (diabetic): {diabetic_glucose:.1f} mg/dL")
print(f"  Avg glucose (non-diabetic): {non_diabetic_glucose:.1f} mg/dL")

print("\n" + "=" * 80)
print("ASSIGNMENT COMPLETE! Remember to stop your compute instance.")
print("=" * 80)
```

### Step 8.2: Stop Compute Instance

**IMPORTANT: Stop compute to avoid charges!**

**Option A: Via Notebook (Recommended)**

```python
# Cell 17: Stop compute instance
from azureml.core.compute import ComputeInstance

compute_name = 'ci-<your name>-eda'  # Your compute instance name

try:
    compute = ComputeInstance(workspace=ws, name=compute_name)
    print(f"Stopping compute instance: {compute_name}")
    compute.stop(wait_for_completion=False)
    print("✓ Compute instance is stopping...")
    print("\n💡 COST SAVINGS:")
    print("  Compute stopped - you won't be charged!")
    print("  Your work is saved and can be accessed anytime")
    print("  Restart compute from Azure ML Studio when needed")
except Exception as e:
    print(f"Note: {e}")
    print("Please stop compute manually from Azure ML Studio")
```

**Option B: Via Azure ML Studio**

1. Navigate to **Compute** in left sidebar
2. Find your compute instance
3. Click the **Stop** button
4. Confirm stop
5. Wait for status to change to **Stopped**

**Option C: Set Up Schedule (Best for Regular Use)**

1. In Compute instances, click your compute name
2. Click **Edit**
3. Go to **Schedule** tab
4. Set:
   - Start time: 8:00 AM (your working hours)
   - Stop time: 6:00 PM
   - Days: Monday-Friday
5. Click **Update**

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Compute Instance Won't Start

**Symptoms:**
- Status stuck on "Creating"
- Error: "Quota exceeded"

**Solutions:**
1. Check quota in subscription:
   - Azure Portal → Subscriptions → Usage + quotas
   - Request quota increase if needed
2. Try different VM size:
   - Standard_DS2_v2 instead of DS3_v2
3. Try different region:
   - Some regions have more availability

#### Issue 2: Data Not Found

**Symptoms:**
- "File not found" error
- Empty datastore

**Solutions:**
1. Verify data upload:
   ```python
   datastore = ws.get_default_datastore()
   datastore.get_blob_client().list_blobs(
       name_starts_with='healthcare/'
   )
   ```
2. Re-upload data:
   - Go to Data → Data assets
   - Delete and re-create
3. Check path:
   - Ensure correct path: `healthcare/data/healthcare_data.json`

#### Issue 3: Kernel Dies or Crashes

**Symptoms:**
- Kernel restarts unexpectedly
- "Out of memory" error

**Solutions:**
1. Restart kernel:
   - Kernel → Restart
2. Clear outputs:
   - Cell → All Output → Clear
3. Upgrade compute:
   - Use Standard_DS4_v2 (28GB RAM)
4. Process data in chunks:
   ```python
   # Instead of loading all at once
   for patient in data['patients'][:3]:  # Process in batches
       # Your code here
   ```

#### Issue 4: MLflow Logging Fails

**Symptoms:**
- "Experiment not found"
- Logging errors

**Solutions:**
1. Verify workspace connection:
   ```python
   print(ws.name)  # Should print workspace name
   ```
2. Check experiment exists:
   ```python
   from azureml.core import Experiment
   experiments = Experiment.list(ws)
   print([e.name for e in experiments])
   ```
3. Use simpler run name:
   - Avoid special characters
   - Keep under 50 characters

#### Issue 5: Cannot Download Data from Datastore

**Symptoms:**
- Download fails
- Empty ./data folder

**Solutions:**
1. Check datastore connection:
   ```python
   datastore = ws.get_default_datastore()
   print(f"Datastore: {datastore.name}")
   print(f"Type: {datastore.datastore_type}")
   ```
2. Try alternative download method:
   ```python
   # Method 1: Direct download
   datastore.download(target_path='./data', prefix='healthcare/', overwrite=True)
   
   # Method 2: Using Dataset
   dataset = Dataset.File.from_files(path=[(datastore, 'healthcare/data/')])
   mount_context = dataset.mount()
   mount_context.start()
   ```
3. Check file exists in storage:
   - Azure Portal → Storage Account → Containers
   - Browse to azureml-blobstore-xxxxx
   - Verify healthcare/data/ exists

#### Issue 6: Visualizations Not Displaying

**Symptoms:**
- Plots don't show
- "Backend not available" error

**Solutions:**
1. Add matplotlib inline:
   ```python
   %matplotlib inline
   import matplotlib.pyplot as plt
   ```
2. Clear output and rerun:
   - Cell → All Output → Clear
   - Run cells again
3. Check for errors:
   ```python
   import matplotlib
   print(matplotlib.get_backend())
   ```

#### Issue 7: Permission Errors

**Symptoms:**
- "Access denied"
- "Insufficient permissions"

**Solutions:**
1. Check workspace role:
   - Should be Owner or Contributor
   - Azure Portal → ML Workspace → Access control (IAM)
2. Verify resource group permissions
3. Contact Azure administrator if using enterprise subscription

#### Issue 8: High Costs

**Symptoms:**
- Unexpected charges
- Compute running when not needed

**Solutions:**
1. **Immediately stop compute:**
   ```
   Compute → Select instance → Stop
   ```
2. Enable auto-shutdown:
   ```
   Compute → Edit → Enable idle shutdown
   ```
3. Set up budget alerts:
   ```
   Azure Portal → Cost Management → Budgets
   Create alert at $10, $25, $50
   ```
4. Use schedules:
   ```
   Only run during work hours
   Stop nights and weekends
   ```
5. Delete resources when done:
   ```
   Azure Portal → Resource Group → Delete resource group
   ```

---

## Best Practices

### Data Management

1. **Version your data:**
   - Use Dataset versioning in Azure ML
   - Include version in file names
   - Tag datasets with metadata

2. **Keep data organized:**
   ```
   healthcare/
   ├── data/
   │   ├── raw/
   │   ├── processed/
   │   └── features/
   ├── models/
   └── outputs/
   ```

3. **Document data changes:**
   - Keep changelog in README
   - Document transformations
   - Track data lineage

### Compute Management

1. **Right-size your compute:**
   - Start small (DS2_v2)
   - Scale up if needed
   - Don't over-provision

2. **Use auto-shutdown:**
   - Always enable
   - Set to 30-60 minutes idle

3. **Consider compute schedules:**
   - For regular work
   - Matches your work hours
   - Stops automatically

### Experiment Tracking

1. **Log consistently:**
   - All key metrics
   - Parameters used
   - Data versions

2. **Use meaningful names:**
   - Experiment: <your name>-healthcare-eda
   - Run: eda_v1_complete_analysis
   - Tags: {dataset: 'v1.0', analyst: 'name'}

3. **Save artifacts:**
   - All visualizations
   - Processed datasets
   - Summary reports

### Cost Optimization

1. **Stop when not using:**
   - Manual stop after each session
   - Or use auto-shutdown

2. **Use smallest viable compute:**
   - DS2_v2 for small datasets
   - DS3_v2 for medium
   - DS4_v2 only if needed

3. **Delete old resources:**
   - Old compute instances
   - Unused datastores
   - Test workspaces

4. **Monitor spending:**
   - Check daily in Cost Management
   - Set up budget alerts
   - Review monthly bills

---

## Next Steps

### Extend Your Analysis

1. **Add more patients:**
   - Process larger dataset
   - Use pipeline for automation

2. **Advanced visualizations:**
   - Interactive plots with Plotly
   - Dashboard with Power BI

3. **Machine learning:**
   - Predict diabetes risk
   - Forecast readmissions
   - Cost prediction models

### Deploy to Production

1. **Create pipeline:**
   - Automate data processing
   - Schedule regular runs
   - Email reports

2. **Build dashboard:**
   - Real-time metrics
   - Interactive exploration
   - Stakeholder access

3. **API endpoint:**
   - Query patient data
   - Get predictions
   - Integration with EHR

---

## Additional Resources

### Azure ML Documentation

- [Azure ML Overview](https://docs.microsoft.com/azure/machine-learning/)
- [Compute Instances](https://docs.microsoft.com/azure/machine-learning/concept-compute-instance)
- [MLflow Tracking](https://docs.microsoft.com/azure/machine-learning/how-to-use-mlflow)
- [Datasets](https://docs.microsoft.com/azure/machine-learning/how-to-create-register-datasets)

### Cost Management

- [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)
- [Cost Management Best Practices](https://docs.microsoft.com/azure/cost-management-billing/)

### Tutorials

- [Azure ML Quickstart](https://docs.microsoft.com/azure/machine-learning/quickstart-create-resources)
- [Train Models](https://docs.microsoft.com/azure/machine-learning/tutorial-1st-experiment-sdk-train)

---

## Support

### Getting Help

1. **Azure Support:**
   - Azure Portal → Help + Support
   - Create support ticket

2. **Community Forums:**
   - Microsoft Q&A
   - Stack Overflow (tag: azure-machine-learning)

3. **Documentation:**
   - docs.microsoft.com/azure
   - Search for specific errors

### Contact

For questions about this assignment:
- Review troubleshooting section first
- Check Azure ML documentation
- Contact course instructor

---

## Summary Checklist

Use this checklist to verify completion:

- [ ] Azure ML Workspace created
- [ ] Data uploaded to datastore
- [ ] Compute instance created and configured
- [ ] Auto-shutdown enabled
- [ ] All notebook cells executed successfully
- [ ] Patient summary dataframe created
- [ ] Visits data flattened
- [ ] Lab results exploded
- [ ] Regex extractions completed
- [ ] has_diabetes feature engineered
- [ ] Density plots created
- [ ] Box plots created
- [ ] Summary dashboard created
- [ ] MLflow experiment logged
- [ ] All metrics tracked
- [ ] Artifacts saved
- [ ] Results viewable in Azure ML Studio
- [ ] Compute instance stopped
- [ ] Work saved and backed up

**Congratulations on completing the Azure ML EDA assignment!** 