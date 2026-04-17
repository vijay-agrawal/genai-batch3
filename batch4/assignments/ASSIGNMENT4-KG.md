# Assignment: Neo4j Mini GraphRAG Retriever
### Python + Cypher + JSON + Insights

---

## Goal

Build a single Python script that:

1. Takes **Patient ID** and/or **Disease name** as user input
2. Runs **2 practical Neo4j Cypher queries**
3. Outputs results as **nested JSON evidence packs**
4. Additionally **flattens/explodes** the JSON into meaningful insight tables (pandas)

---

## What You Will Build

**Script:** `neo4j_patient_insights.py`

### Inputs (from user)

| Input | Required | Example |
|---|---|---|
| Patient ID | Optional | `P_001` |
| Disease | Optional | `Hypertension` or ICD-10 `I10` |
| Time window | Optional | default `90` days |

### Outputs

1. **Use-case A output:** nested JSON (patient summary + evidence)
2. **Use-case B output:** nested JSON (disease cohort / trends)
3. **Insights view:** pandas DataFrames created by flattening/exploding JSON (printed to console)

---

## Use-Cases

### Use-case A — Patient "Clinical Snapshot + Evidence"

**Real question:**
> "Show the last 5 encounters for this patient, with diagnoses, medications, and note snippets."

**Expected nested JSON structure:**

```json
{
  "patient": { ... },
  "encounters": [
    {
      "encounter_id": "...",
      "date": "...",
      "diagnoses": [ ... ],
      "medications": [ ... ],
      "notes": [ ... ]
    }
  ],
  "provenance": {
    "query": "...",
    "timestamp": "..."
  }
}
```

**Sections:**
- `patient`
- `encounters[]` with `diagnoses[]`, `medications[]`, `notes[]`
- `provenance` (query name, timestamp — optional)

---

### Use-case B — Disease "Newly Diagnosed Cohort"

**Real question:**
> "List patients newly diagnosed with this disease in the last 90 days (first-ever occurrence)."

**Expected nested JSON structure:**

```json
{
  "disease": {
    "name": "Hypertension",
    "icd10": "I10"
  },
  "cohort": [
    {
      "patient_id": "P_001",
      "name": "...",
      "first_dx_date": "2024-01-15"
    }
  ],
  "summary": {
    "count": 12
  }
}
```

**Sections:**
- `disease` (name / icd10)
- `cohort[]` with `patient_id`, `name`, `first_dx_date`
- `summary` stats (count)

---

## Requirements

### Functional

- Must use the **`neo4j` Python driver**
- Must load Neo4j credentials from **`.env`** file
- Must support all three input modes:

| Input provided | Behaviour |
|---|---|
| Patient ID only | Run Use-case A |
| Disease only | Run Use-case B |
| Both | Run both Use-cases |

### Output Format

- Print nested JSON to console (pretty-printed with `json.dumps(..., indent=2)`)
- Print **at least 2 insight tables** (DataFrames) derived from the JSON:

| Table | Description |
|---|---|
| Table 1 | Encounter-level rows — one row per encounter |
| Table 2 | Diagnosis/medication exploded — one row per dx/med, with encounter info carried across |

---

## JSON Flattening / Explosion

Use `pandas.json_normalize` or manual expansion to convert nested JSON into flat DataFrames.

**Example — Table 1 (encounter-level):**

| patient_id | encounter_id | date | department | num_diagnoses | num_medications |
|---|---|---|---|---|---|
| P_001 | E_010 | 2024-03-01 | Cardiology | 2 | 3 |
| P_001 | E_009 | 2024-01-15 | GP | 1 | 1 |

**Example — Table 2 (diagnosis/medication exploded):**

| patient_id | encounter_id | date | type | code | description |
|---|---|---|---|---|---|
| P_001 | E_010 | 2024-03-01 | diagnosis | I10 | Hypertension |
| P_001 | E_010 | 2024-03-01 | medication | RX_042 | Lisinopril 10mg |

---

## Suggested Script Structure

```
neo4j_patient_insights.py
├── load_credentials()         # load from .env
├── get_user_inputs()          # prompt for patient_id, disease, time_window
├── run_usecase_a(patient_id)  # Cypher query + build JSON
├── run_usecase_b(disease, days) # Cypher query + build JSON
├── flatten_encounters(json)   # → Table 1 DataFrame
├── flatten_dx_meds(json)      # → Table 2 DataFrame
└── main()                     # orchestrate based on inputs
```

---

## Setup

1. Copy `03neo4j_test_connection.py` pattern for driver initialisation
2. Ensure your `.env` contains:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

3. Test connection before running the full script:

```bash
python 03neo4j_test_connection.py
```

4. Run the assignment script:

```bash
python neo4j_patient_insights.py
```

---

## Evaluation Checklist

- [ ] Script accepts patient ID and/or disease as input
- [ ] Use-case A Cypher query runs and returns last 5 encounters
- [ ] Use-case B Cypher query returns newly diagnosed cohort (90-day window)
- [ ] Both results printed as pretty-printed nested JSON
- [ ] Table 1: encounter-level DataFrame printed to console
- [ ] Table 2: diagnosis/medication exploded DataFrame printed to console
- [ ] Credentials loaded from `.env` (not hard-coded)
- [ ] Script handles missing inputs gracefully (runs only the relevant use-case)
