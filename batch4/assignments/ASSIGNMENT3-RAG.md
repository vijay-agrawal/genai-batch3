# RAG Assignments — Healthcare Domain

---

## Overview

You will build two RAG systems using synthetic healthcare data.  
Both assignments use **Azure OpenAI** (embeddings + chat) and **ChromaDB** as the vector store.

Synthetic source files are described in each assignment. Scripts to generate the PDFs and CSV are provided at the end of this document.

---

---

# Assignment 1 — Parent Document Retriever on Medical Research Articles

## Learning Objective

Understand **why naive chunk-based RAG fails** when an answer requires context that spans multiple paragraphs — and how the **Parent Document Retriever** pattern solves it.

### The Core Problem

When you split a research article into small chunks (e.g., 200 characters), each chunk contains only a fragment of the study:

> *Chunk A:* "Metformin was administered at 500 mg twice daily."  
> *Chunk B:* "HbA1c levels dropped by 1.4% after 12 weeks."  
> *Chunk C:* "Patients with renal impairment were excluded from the study."

A question like *"What was the study design and who was excluded from the metformin trial?"* will match chunk A or B but return an incomplete answer. The crucial exclusion context lives in chunk C, which may not be retrieved.

### The Solution — Parent Document Retriever

- **Child chunks** (small, ~200 chars) are stored in the vector store for precise retrieval.
- **Parent documents** (large, ~1500 chars sections) are stored separately in a docstore.
- At query time: retrieve the best matching child chunks → fetch their parent sections → send full parent text to the LLM.

The LLM now sees the entire study section, not isolated fragments.

---

## Synthetic Data — Research Articles (PDF Files)

Create the following **4 PDF files** in a `research_articles/` subfolder.  
Use the `generate_pdfs.py` script at the end of this document.

---

### `article_diabetes_metformin.pdf`

```
Title: Efficacy of Metformin Monotherapy in Newly Diagnosed Type 2 Diabetes Patients

Abstract:
This randomized controlled trial evaluated the long-term glycemic control efficacy of
metformin monotherapy in 320 adults newly diagnosed with Type 2 diabetes mellitus (T2DM).
The study was conducted across four tertiary care hospitals in India over a period of
18 months. Primary endpoint was reduction in HbA1c at 12 weeks and 24 weeks. Secondary
endpoints included fasting plasma glucose, body weight change, and incidence of adverse
events. The trial was registered under CTRI/2022/04/041892.

1. Introduction:
Type 2 diabetes mellitus is a metabolic disorder characterized by chronic hyperglycemia
resulting from defects in insulin secretion, insulin action, or both. The global prevalence
of T2DM has risen sharply over the past two decades, with India alone accounting for
approximately 77 million cases as of 2022. First-line pharmacological treatment per ADA
guidelines recommends metformin unless contraindicated. Despite widespread use, real-world
efficacy data from South Asian populations remain limited.

This study aimed to fill that gap by recruiting newly diagnosed T2DM patients who had
not previously received any antidiabetic medication.

2. Methodology:
Patients aged 30–65 years with HbA1c between 7.0% and 10.0% at diagnosis were enrolled.
Patients with eGFR < 45 mL/min/1.73m², hepatic impairment, pregnancy, or a history of
lactic acidosis were excluded. Participants were randomized 1:1 to receive either
metformin 500 mg twice daily (titrated to 1000 mg twice daily at week 4) or placebo.
All participants received standardized dietary counselling. Blinding was maintained
through identical tablet appearance and packaging.

A total of 162 patients were allocated to the metformin arm and 158 to placebo.
Baseline characteristics including age, BMI, HbA1c, and fasting glucose were comparable
across both groups (p > 0.05 for all).

3. Results:
At 12 weeks, the metformin group demonstrated a mean HbA1c reduction of 1.4% (±0.3%)
compared to 0.3% (±0.2%) in the placebo group (p < 0.001). At 24 weeks, the reduction
was sustained at 1.6% (±0.4%) in the metformin arm versus 0.4% (±0.3%) in placebo.

Fasting plasma glucose fell by an average of 38 mg/dL in the treatment group versus
11 mg/dL in placebo at 12 weeks. Body weight showed a modest reduction of 1.2 kg in
the metformin group, consistent with previously published data.

Gastrointestinal side effects (nausea, diarrhea) were reported in 22% of metformin
patients versus 6% in placebo. All GI events were mild to moderate and resolved within
3 weeks of dose escalation. No cases of lactic acidosis or serious adverse events
were reported in either group.

4. Discussion:
The results confirm that metformin monotherapy achieves clinically meaningful HbA1c
reductions in South Asian T2DM patients over a 24-week period. The exclusion of patients
with renal impairment (eGFR < 45) is critical as metformin is renally cleared and
accumulation can precipitate lactic acidosis.

The 22% rate of GI side effects is consistent with published literature but is
manageable through gradual dose titration. Clinicians should initiate at 500 mg twice
daily and titrate slowly based on tolerability.

5. Conclusion:
Metformin 500 mg–2000 mg/day is effective and well-tolerated as monotherapy in newly
diagnosed T2DM patients without renal or hepatic contraindications. Gradual dose
titration significantly reduces GI side effects. Long-term follow-up beyond 24 weeks
is recommended to assess durability of glycemic control and cardiovascular outcomes.
```

---

### `article_hypertension_ace.pdf`

```
Title: Comparative Efficacy of ACE Inhibitors vs. Calcium Channel Blockers in Stage 2
Hypertension — A 12-Month Prospective Study

Abstract:
This prospective observational study compared the antihypertensive efficacy, tolerability,
and end-organ protection of ACE inhibitors (enalapril) versus calcium channel blockers
(amlodipine) in 280 patients with Stage 2 hypertension (SBP 160–179 mmHg or DBP
100–109 mmHg). The study tracked office BP, 24-hour ambulatory BP, renal function
markers, and left ventricular mass index (LVMI) over 12 months.

1. Introduction:
Stage 2 hypertension significantly elevates the risk of myocardial infarction, stroke,
renal failure, and heart failure. Pharmacological management with monotherapy or
combination therapy is essential. ACE inhibitors and calcium channel blockers are both
first-line agents, but their relative advantages in specific patient subgroups remain
debated. ACE inhibitors are particularly beneficial in patients with diabetes or
proteinuria due to their nephroprotective effects. CCBs offer superior vasodilation
with fewer metabolic side effects.

This study was designed to compare the two drug classes in a real-world, non-selected
Stage 2 hypertension population over a 12-month period to assess both BP control and
end-organ outcomes.

2. Patient Selection and Exclusion Criteria:
Patients aged 40–70 years with newly diagnosed Stage 2 hypertension confirmed on at
least two clinic visits were enrolled. Patients with secondary hypertension (renal artery
stenosis, primary aldosteronism, pheochromocytoma), bilateral renal artery stenosis,
known hypersensitivity to ACE inhibitors or CCBs, pregnancy, or creatinine > 2.0 mg/dL
were excluded. Patients already on antihypertensive therapy were also excluded.

Patients were allocated to enalapril 5 mg daily (titrated to 20 mg) or amlodipine
5 mg daily (titrated to 10 mg) based on physician preference. This was an observational
study and not randomized.

3. Results:
At 6 months, mean SBP reduction was 28 mmHg in the enalapril group versus 25 mmHg in
the amlodipine group (p = 0.04). DBP reduction was comparable: 16 mmHg vs. 15 mmHg.
At 12 months, both groups achieved similar BP control (<140/90 mmHg) in approximately
72% of patients.

Microalbuminuria reduction was significantly better in the enalapril group (42% reduction
vs. 11%, p < 0.001), confirming nephroprotective benefit. LVMI regression was similar
in both groups at 12 months (8% reduction vs. 7%, p = 0.31).

Dry cough was reported in 18% of enalapril patients, leading to discontinuation in 6%.
Peripheral edema was noted in 14% of amlodipine patients. No cases of angioedema were
recorded in either group.

4. Discussion:
Both ACE inhibitors and CCBs provide effective BP control in Stage 2 hypertension.
ACE inhibitors should be preferred in hypertensive patients with diabetes or
microalbuminuria due to demonstrated nephroprotective effects. The high rate of cough
with enalapril (18%) is a known class effect and may warrant switching to an ARB
(angiotensin receptor blocker) in intolerant patients.

Patients with peripheral edema on amlodipine can often be managed by dose reduction
or adding a low-dose diuretic rather than discontinuing the drug.

5. Conclusion:
In Stage 2 hypertension, enalapril and amlodipine provide comparable long-term BP control.
Enalapril is preferred in patients with diabetic nephropathy or proteinuria. CCBs are
preferred when ACE inhibitor cough is problematic. Combination therapy should be
considered when monotherapy achieves less than 50% of target BP reduction at maximum dose.
```

---

### `article_alzheimers_biomarkers.pdf`

```
Title: Cerebrospinal Fluid Biomarkers for Early Detection of Alzheimer's Disease:
A Cross-Sectional Study of Amyloid-β and Tau Protein Ratios

Abstract:
This cross-sectional study investigated the diagnostic utility of cerebrospinal fluid
(CSF) biomarkers — amyloid-β 42 (Aβ42), total tau (t-tau), and phosphorylated tau
(p-tau181) — in distinguishing early-stage Alzheimer's disease (AD) from mild cognitive
impairment (MCI) and cognitively normal controls. A total of 210 participants were enrolled
across three memory clinics. The study evaluated the Aβ42/Aβ40 ratio and p-tau/Aβ42 ratio
as composite diagnostic markers.

1. Introduction:
Alzheimer's disease is the most common cause of dementia, accounting for 60–70% of cases
globally. Diagnosis has historically been confirmed post-mortem through neuropathological
examination. The emergence of CSF and PET-based biomarkers has enabled in-vivo detection
of amyloid and tau pathology years before clinical symptom onset.

The National Institute on Aging–Alzheimer's Association (NIA-AA) 2018 research framework
classifies AD biologically using the ATN (Amyloid/Tau/Neurodegeneration) scheme.
Early identification is critical because potential disease-modifying therapies (e.g.,
lecanemab, donanemab) are most effective in the early amyloid accumulation phase,
before significant neuronal loss occurs.

2. Methodology:
Participants were grouped into three categories: (a) AD (n=72), (b) amnestic MCI (n=85),
and (c) cognitively normal controls (n=53). All underwent lumbar puncture for CSF analysis.
CSF Aβ42, Aβ40, t-tau, and p-tau181 were measured using validated ELISA kits.
MRI volumetry and neuropsychological batteries (MMSE, MoCA, ADAS-Cog) were also performed.

Participants with active CNS infection, prior neurosurgery, anticoagulation therapy
contraindicated for lumbar puncture, or severe psychiatric comorbidity were excluded.

3. Results:
Mean CSF Aβ42 was significantly lower in AD patients (412 pg/mL ± 95) compared to
MCI (698 pg/mL ± 142) and controls (1021 pg/mL ± 188) (p < 0.001 across all comparisons).
The p-tau181/Aβ42 ratio demonstrated the highest diagnostic accuracy with AUC = 0.94
for distinguishing AD from controls and AUC = 0.81 for AD vs. MCI.

Hippocampal volume loss correlated inversely with p-tau/Aβ42 ratio (r = -0.67, p < 0.001).
Patients with a p-tau/Aβ42 ratio > 0.12 had 8.3x higher odds of converting from MCI
to AD within 24 months (OR 8.3, 95% CI 3.1–22.4).

4. Discussion:
The Aβ42/Aβ40 ratio and p-tau/Aβ42 ratio are robust, reproducible biomarkers for early
AD detection. The p-tau/Aβ42 ratio outperforms individual biomarkers alone and should
be the primary CSF test in memory clinics.

Clinicians should note that CSF biomarker cutoffs vary by assay manufacturer and laboratory.
Local validation of cutoffs is essential before clinical deployment. PET amyloid imaging
remains the gold standard where available, but CSF testing is more accessible and
cost-effective.

5. Conclusion:
CSF p-tau181/Aβ42 ratio provides high diagnostic accuracy for early AD identification.
Integration of this ratio with neuropsychological assessment and MRI volumetry should
be standard practice in memory disorder clinics. Longitudinal studies are needed to
validate conversion prediction cutoffs across diverse ethnic populations.
```

---

### `article_sepsis_icu.pdf`

```
Title: Early Goal-Directed Therapy vs. Usual Care in Sepsis-Induced Hypotension:
Outcomes from a Multi-Centre ICU Study

Abstract:
This retrospective multi-centre cohort study examined 28-day mortality, ICU length of
stay, and organ failure rates in 415 adult sepsis patients managed with either
Early Goal-Directed Therapy (EGDT) or usual care (UC) in five tertiary ICUs.
Sepsis was defined per Sepsis-3 criteria (SOFA score ≥ 2 with suspected infection).
Septic shock was defined as vasopressor requirement with serum lactate > 2 mmol/L
despite adequate fluid resuscitation.

1. Introduction:
Sepsis remains one of the leading causes of ICU mortality globally, with a 28-day
mortality of 20–30% for sepsis and 40–60% for septic shock. Early Goal-Directed Therapy,
introduced by Rivers et al. (2001), standardized resuscitation targets including:
central venous pressure (CVP) 8–12 mmHg, MAP ≥ 65 mmHg, urine output ≥ 0.5 mL/kg/hr,
and central venous oxygen saturation (ScvO2) ≥ 70%.

Subsequent large RCTs (ProCESS, ARISE, ProMISe) challenged EGDT's superiority over
usual care, creating ongoing clinical debate about protocolized vs. individualized
resuscitation.

2. Patient Population and Exclusions:
Adult patients (≥18 years) admitted to ICU with sepsis-induced hypotension (MAP < 65 mmHg
not responsive to 30 mL/kg crystalloid bolus) were included. Patients with do-not-resuscitate
orders at ICU admission, those transferred from another ICU after > 6 hours of sepsis
management, patients with end-stage renal disease on dialysis, or those with massive
hemorrhage as the primary cause of hypotension were excluded.

Of 415 included patients, 207 received EGDT and 208 received usual care.
Baseline SOFA scores (mean 8.2 vs. 8.0) and lactate levels (mean 4.1 vs. 3.9 mmol/L)
were comparable between groups.

3. Results:
28-day mortality was 31.4% in the EGDT group versus 33.2% in usual care (p = 0.67),
consistent with findings from large RCTs. ICU length of stay was marginally shorter
in EGDT (8.1 vs. 9.4 days, p = 0.03). Acute Kidney Injury (AKI) requiring renal
replacement therapy occurred in 28% of EGDT vs. 34% of UC patients (p = 0.04).

Among patients with lactate > 4 mmol/L at presentation, 28-day mortality was 48% in
usual care versus 39% in EGDT (p = 0.02), suggesting a possible benefit in the
highest-acuity subgroup.

4. Discussion:
The absence of an overall mortality benefit from EGDT aligns with contemporary evidence.
However, the subgroup analysis of patients with lactate > 4 mmol/L warrants further
prospective investigation, as this represents the most haemodynamically unstable cohort.

Key elements of sepsis care — early antibiotics (within 1 hour of recognition), source
control, lactate-guided resuscitation, and vasopressor initiation when MAP < 65 mmHg
despite adequate fluids — remain universally recommended regardless of protocol.
The choice between EGDT and protocolized usual care should be based on local expertise
and resource availability.

5. Conclusion:
EGDT does not reduce overall 28-day mortality versus usual care in unselected sepsis
patients. However, patients with severe hyperlactataemia (lactate > 4 mmol/L) may
benefit from structured resuscitation targets. Universal principles of early antibiotic
therapy and haemodynamic stabilization remain the cornerstone of sepsis management.
```

---

## Questions for Assignment 1

These questions are designed so that **small-chunk RAG fails** but **Parent Document Retriever succeeds**.  
The answer to each question requires context from 2–4 consecutive paragraphs.

| # | Question | Why small chunks fail | Source article |
|---|----------|-----------------------|----------------|
| 1 | What were the inclusion and exclusion criteria in the metformin trial, and how did these affect the patient population enrolled? | Exclusion criteria and enrollment numbers are in separate paragraphs | `article_diabetes_metformin.pdf` |
| 2 | Describe the complete methodology of the metformin study — how were patients randomized, what dosing was used, and how was blinding maintained? | Methodology details span the entire Section 2 | `article_diabetes_metformin.pdf` |
| 3 | What side effects were observed in the metformin arm, were they serious, and how were they managed? | Side effects (Section 3) and management guidance (Section 4) are in different paragraphs | `article_diabetes_metformin.pdf` |
| 4 | Why was enalapril preferred over amlodipine in certain patient subgroups, and what evidence supports this? | Preference rationale (Introduction), results (Section 3), and recommendation (Section 4) are spread across sections | `article_hypertension_ace.pdf` |
| 5 | Who was excluded from the hypertension study and what were the dosing protocols for each drug? | Exclusion criteria and dosing are in the same section but separate paragraphs | `article_hypertension_ace.pdf` |
| 6 | What is the p-tau/Aβ42 ratio and why is it more useful than measuring Aβ42 alone for Alzheimer's diagnosis? | Biomarker rationale (Introduction), the composite ratio (Methods), and its superiority (Results + Discussion) are spread across 4 sections | `article_alzheimers_biomarkers.pdf` |
| 7 | Which patients were most likely to convert from MCI to Alzheimer's disease, and what biomarker threshold predicted this? | Conversion odds ratio (Results) depends on understanding the patient grouping (Methods) | `article_alzheimers_biomarkers.pdf` |
| 8 | In the sepsis study, for which subgroup did EGDT show a statistically significant mortality benefit, and what was the threshold? | Subgroup result (Section 3) needs to be read alongside the Sepsis-3 definition and overall mortality context (Introduction + Results) | `article_sepsis_icu.pdf` |
| 9 | What are the universal sepsis management principles that apply regardless of whether EGDT or usual care is used? | Universal principles appear in the Discussion — but their context requires knowing the EGDT vs. UC debate (Introduction) | `article_sepsis_icu.pdf` |
| 10 | Which patients were excluded from the sepsis ICU study, and could any of those exclusions bias the mortality results? | Exclusion criteria (Section 2) + mortality results (Section 3) need to be read together | `article_sepsis_icu.pdf` |

---

## Implementation Guide

### Step 1 — Naive RAG (baseline)
- Split PDFs into small chunks: `chunk_size=200, chunk_overlap=20`
- Store in ChromaDB, retrieve top-5 chunks, generate answer
- Run all 10 questions and observe incomplete answers

### Step 2 — Parent Document Retriever
```python
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Small chunks for retrieval precision
child_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)

# Large sections for LLM context
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100)

docstore = InMemoryStore()

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=docstore,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)
retriever.add_documents(documents)
```

### Step 3 — Compare answers
Run the same 10 questions through both approaches and compare the quality and completeness of answers.

---

---

# Assignment 2 — Fixing RAG's Weakness with Negation and Numeric Queries

## Learning Objective

Understand why **vector similarity search fails for numeric comparisons and negation**, and implement a **hybrid structured-filtering + RAG** approach using patient clinical notes.

### The Core Problem

RAG uses cosine/dot-product similarity. When you ask:

> *"Which patients with systolic BP > 200 responded to treatment?"*

The retriever finds chunks that are *semantically similar* to BP and treatment — but it has **no concept of > 200 as a threshold**. It may return notes from patients with BP = 150 that mention "blood pressure treatment" simply because the text is similar.

Similarly, for negation:

> *"Which patients did NOT respond to amlodipine?"*

The word "NOT" is nearly invisible in embedding space. A note saying *"Patient did not respond to amlodipine"* has very similar embedding to *"Patient responded well to amlodipine"* because the surrounding clinical vocabulary is identical.

### The Solution — Pre-filter on structured fields, then RAG on filtered results

1. Parse the CSV into structured fields (patient_id, systolic_bp, treatment, outcome).
2. Apply **numeric and boolean filters** directly on the DataFrame (pandas) before retrieval.
3. Load only the filtered patient notes into ChromaDB (or use ChromaDB metadata filters).
4. Run RAG only on the filtered subset.

---

## Synthetic Data — Patient Clinical Notes CSV

Save the following as `clinical_notes/patient_clinical_notes.csv`.  
Use the `generate_csv.py` script at the end of this document, or copy the data directly.

**CSV columns:**
`patient_id, age, gender, diagnosis, systolic_bp, diastolic_bp, treatment, response_to_treatment, hba1c_before, hba1c_after, creatinine, notes`

| patient_id | age | gender | diagnosis | systolic_bp | diastolic_bp | treatment | response_to_treatment | hba1c_before | hba1c_after | creatinine | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P001 | 58 | M | Hypertension | 210 | 118 | Amlodipine | No | - | - | 1.1 | Patient presented with severe hypertension. Amlodipine 10mg initiated. After 8 weeks SBP remained at 198 mmHg. Treatment considered a failure. Switched to combination therapy. |
| P002 | 63 | F | Hypertension | 205 | 112 | Enalapril | Yes | - | - | 0.9 | Enalapril 20mg daily initiated for Stage 2 hypertension. BP reduced to 148/88 mmHg within 6 weeks. Patient tolerating well with no adverse effects. |
| P003 | 47 | M | Hypertension | 195 | 105 | Amlodipine | Yes | - | - | 1.0 | Amlodipine 5mg titrated to 10mg over 4 weeks. SBP reduced from 195 to 138 mmHg. Good response. Mild ankle edema noted, managed conservatively. |
| P004 | 72 | F | Hypertension | 218 | 120 | Enalapril | No | - | - | 1.8 | Elderly female with Stage 3 hypertension and early CKD. Enalapril initiated but creatinine rose from 1.8 to 2.4 mg/dL at 4 weeks. Drug discontinued due to renal deterioration. BP uncontrolled. |
| P005 | 55 | M | Hypertension | 208 | 115 | Amlodipine + Enalapril | Yes | - | - | 1.0 | Combination therapy initiated. SBP reduced from 208 to 132 mmHg at 12 weeks. Patient compliant with medication. No significant adverse effects. Excellent responder. |
| P006 | 61 | F | Hypertension | 202 | 110 | Amlodipine | No | - | - | 1.2 | Monotherapy with amlodipine failed to achieve target BP. After 12 weeks SBP was 192 mmHg. Dose titration to 10mg had limited effect. Combination therapy recommended. |
| P007 | 49 | M | Hypertension | 212 | 116 | Losartan | Yes | - | - | 1.1 | Losartan 50mg initiated, titrated to 100mg. BP reduced to 136/84 mmHg at 8 weeks. Patient had documented ACE inhibitor cough previously. ARB chosen as alternative. Good response. |
| P008 | 67 | F | Hypertension | 225 | 122 | Amlodipine | No | - | - | 2.1 | Severe hypertension with CKD stage 3. Amlodipine showed no significant BP reduction. SBP remained above 210 mmHg throughout 8-week trial. Referred to nephrology for specialist management. |
| P009 | 53 | M | Type 2 Diabetes + Hypertension | 198 | 108 | Enalapril + Metformin | Yes | 9.2 | 7.4 | 1.0 | Dual diagnosis patient. Enalapril chosen for nephroprotective benefit. BP reduced to 142/86 mmHg. HbA1c improved from 9.2 to 7.4% over 24 weeks. Both conditions well controlled. |
| P010 | 44 | M | Type 2 Diabetes | 138 | 86 | Metformin | Yes | 8.8 | 6.9 | 0.8 | Metformin 500mg titrated to 2000mg. HbA1c improved from 8.8 to 6.9% at 24 weeks. Mild GI discomfort in first 2 weeks, resolved with gradual titration. No hypertension. |
| P011 | 70 | F | Type 2 Diabetes | 145 | 90 | Metformin | No | 10.1 | 9.8 | 2.2 | Metformin contraindicated due to CKD (eGFR 38). Initial dosing error — metformin prescribed despite creatinine 2.2. Discontinued. Switched to insulin therapy. Poor glycemic control persisted. |
| P012 | 59 | M | Type 2 Diabetes | 152 | 94 | Glipizide | Yes | 9.5 | 7.1 | 1.0 | Patient intolerant of metformin due to GI side effects. Glipizide 5mg started. HbA1c reduced from 9.5 to 7.1% at 16 weeks. Weight gain of 2.1 kg noted. |
| P013 | 66 | F | Hypertension | 203 | 111 | Enalapril | Yes | - | - | 1.0 | Stage 2 hypertension. Enalapril 10mg daily. BP reduced to 146/88 mmHg within 8 weeks. Dry cough developed at week 6, patient managed with antitussive. Continued therapy as BP well controlled. |
| P014 | 51 | M | Hypertension | 215 | 118 | Amlodipine | No | - | - | 1.1 | Patient non-adherent to amlodipine. Reported tablet side effects as reason. After counselling, BP still 208/114 mmHg at 10 weeks. Root cause suspected as non-compliance rather than drug failure. |
| P015 | 48 | F | Hypertension | 207 | 114 | Losartan + Hydrochlorothiazide | Yes | - | - | 0.9 | Combination ARB + diuretic initiated. Excellent BP response: SBP from 207 to 128 mmHg at 12 weeks. No electrolyte disturbances. Patient very satisfied. |
| P016 | 74 | M | Hypertension + Heart Failure | 155 | 95 | Carvedilol + Enalapril | Yes | - | - | 1.3 | Beta-blocker and ACE inhibitor combination for HF with reduced EF (EF 38%). BP and HR well controlled. SBP 132 mmHg at 3 months. No signs of decompensation. |
| P017 | 57 | F | Hypertension | 199 | 109 | Amlodipine | No | - | - | 1.0 | Borderline BP > 200 patient. Amlodipine 10mg showed insufficient response at 8 weeks (SBP 191 mmHg). Physician added indapamide. Patient follow-up pending. |
| P018 | 62 | M | Type 2 Diabetes + Hypertension | 201 | 112 | Enalapril + Metformin | Yes | 8.6 | 7.2 | 1.1 | BP > 200 with T2DM. Enalapril nephroprotective choice. At 16 weeks SBP 144 mmHg and HbA1c 7.2%. Both targets met. Patient maintained on current regimen. |
| P019 | 45 | F | Type 2 Diabetes | 130 | 82 | Metformin | No | 9.0 | 8.7 | 0.9 | Patient started metformin 1000mg. Severe GI intolerance (nausea, vomiting, diarrhea) persisted despite dose adjustment. HbA1c minimally improved. Switched to DPP-4 inhibitor. |
| P020 | 68 | M | Hypertension | 222 | 120 | Amlodipine + Losartan + HCTZ | Yes | - | - | 1.4 | Triple therapy initiated for resistant hypertension. SBP reduced from 222 to 138 mmHg at 16 weeks. Previously failed amlodipine monotherapy (SBP 210 at 8 weeks on mono). Good final response. |

---

## Questions for Assignment 2

### Section A — Questions that naive RAG gets wrong (run these first to observe failure)

| # | Question | Why RAG fails |
|---|----------|---------------|
| 1 | Which patients had systolic BP greater than 200 AND did NOT respond to their treatment? | RAG cannot evaluate > 200 as a threshold; "not respond" is invisible in embeddings |
| 2 | List all patients where amlodipine monotherapy failed to control blood pressure. | "Failed" and "did not respond" have similar embeddings to "succeeded" and "responded" |
| 3 | Which patients had systolic BP above 200 and were successfully treated? What treatments worked? | Numeric threshold not handled; multiple matching candidates confuse the retriever |
| 4 | Are there any patients where metformin was prescribed despite being contraindicated by kidney function? | Negation + clinical inference — RAG cannot reason about contraindication violation |
| 5 | Which patients had creatinine > 2.0 and how did their treatment outcomes differ from those with normal creatinine? | Numeric comparison on a different field than the question's topic |
| 6 | How many patients with BP > 200 were on combination therapy versus monotherapy? | Counting + numeric filter — RAG cannot count or threshold |

### Section B — Questions that work after implementing the fix

After pre-filtering the DataFrame on structured fields before passing notes to the RAG:

| # | Question | Pre-filter to apply |
|---|----------|---------------------|
| 1 | Among patients with systolic BP > 200, which treatments were effective? | `df[df['systolic_bp'] > 200 & df['response_to_treatment'] == 'Yes']` |
| 2 | Which patients with BP > 200 did not respond to amlodipine? | `df[df['systolic_bp'] > 200 & df['treatment'].str.contains('Amlodipine') & df['response'] == 'No']` |
| 3 | For patients with creatinine > 2.0, what complications arose from their treatment? | `df[df['creatinine'] > 2.0]` |
| 4 | Which diabetic patients achieved HbA1c below 7.5 after treatment? What was their medication? | `df[df['hba1c_after'] < 7.5 & df['diagnosis'].str.contains('Diabetes')]` |
| 5 | Which patients were switched off their first treatment? Why? | `df[df['response_to_treatment'] == 'No']` |

---

## Implementation Guide

### Step 1 — Naive RAG (observe failure)
- Load all clinical notes as plain text chunks.
- Store in ChromaDB without any structured metadata.
- Run Section A questions and observe hallucinations / wrong answers.

### Step 2 — Structured Pre-filtering + RAG

```python
import pandas as pd
from langchain_chroma import Chroma
from langchain_core.documents import Document

df = pd.read_csv("clinical_notes/patient_clinical_notes.csv")

def query_with_filter(question: str, filter_fn, df: pd.DataFrame, vectorstore):
    # Step 1: filter rows using structured data
    filtered_df = df[filter_fn(df)]

    if filtered_df.empty:
        return "No patients match the specified criteria."

    # Step 2: build a targeted context from filtered notes only
    context = "\n\n".join(
        f"[{row['patient_id']} | {row['treatment']} | BP {row['systolic_bp']}/{row['diastolic_bp']}]\n{row['notes']}"
        for _, row in filtered_df.iterrows()
    )

    # Step 3: pass filtered context to LLM
    prompt = f"""You are a clinical data analyst. Use only the patient notes below to answer.

Context:
{context}

Question: {question}

Answer:"""
    return llm.invoke(prompt).content

# Example usage:
answer = query_with_filter(
    question="Which patients with BP > 200 did not respond to amlodipine?",
    filter_fn=lambda df: (df['systolic_bp'] > 200) & (df['treatment'].str.contains('Amlodipine')) & (df['response_to_treatment'] == 'No'),
    df=df,
    vectorstore=vectorstore
)
```

### Step 3 — ChromaDB Metadata Filter approach (alternative)

Instead of pandas pre-filtering, store structured fields as ChromaDB metadata and use the built-in filter:

```python
# When indexing
doc = Document(
    page_content=row['notes'],
    metadata={
        "patient_id": row['patient_id'],
        "systolic_bp": int(row['systolic_bp']),
        "treatment": row['treatment'],
        "response": row['response_to_treatment'],
        "creatinine": float(row['creatinine']),
    }
)

# At query time
results = vectorstore.similarity_search(
    query="treatment outcome for hypertensive patient",
    filter={"systolic_bp": {"$gt": 200}, "response_to_treatment": "No"}
)
```

---

---

# Data Generation Scripts

## `generate_pdfs.py` — Create the 4 research article PDFs

```python
"""
Run: pip install fpdf2
     python generate_pdfs.py
Creates research_articles/*.pdf from the text content in ASSIGNMENTS.md.
"""
from fpdf import FPDF
import os, textwrap

OUTPUT_DIR = "research_articles"
os.makedirs(OUTPUT_DIR, exist_ok=True)

ARTICLES = {
    "article_diabetes_metformin.pdf": {
        "title": "Efficacy of Metformin Monotherapy in Newly Diagnosed Type 2 Diabetes Patients",
        # Paste the full text from the article section above
    },
    # Add remaining articles similarly
}

class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 8, self.title, ln=True, align="C")
        self.ln(4)

    def add_article_text(self, text: str):
        self.set_font("Helvetica", size=10)
        for line in text.strip().splitlines():
            wrapped = textwrap.wrap(line, width=100) or [""]
            for wline in wrapped:
                self.multi_cell(0, 6, wline)
        self.ln(4)

for filename, content in ARTICLES.items():
    pdf = PDF()
    pdf.title = content["title"]
    pdf.add_page()
    pdf.add_article_text(content.get("body", content["title"]))
    pdf.output(os.path.join(OUTPUT_DIR, filename))
    print(f"Created {filename}")
```

## `generate_csv.py` — Create the clinical notes CSV

```python
"""
Run: python generate_csv.py
Creates clinical_notes/patient_clinical_notes.csv
"""
import csv, os

os.makedirs("clinical_notes", exist_ok=True)

ROWS = [
    ["P001","58","M","Hypertension","210","118","Amlodipine","No","-","-","1.1",
     "Patient presented with severe hypertension. Amlodipine 10mg initiated. After 8 weeks SBP remained at 198 mmHg. Treatment considered a failure. Switched to combination therapy."],
    ["P002","63","F","Hypertension","205","112","Enalapril","Yes","-","-","0.9",
     "Enalapril 20mg daily initiated for Stage 2 hypertension. BP reduced to 148/88 mmHg within 6 weeks. Patient tolerating well with no adverse effects."],
    # ... add all 20 rows from the table above
]

with open("clinical_notes/patient_clinical_notes.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["patient_id","age","gender","diagnosis","systolic_bp","diastolic_bp",
                     "treatment","response_to_treatment","hba1c_before","hba1c_after",
                     "creatinine","notes"])
    writer.writerows(ROWS)

print("Created patient_clinical_notes.csv")
```

---

## Evaluation Checklist

### Assignment 1 — Parent Document Retriever
- [ ] Naive RAG with chunk_size=200 gives incomplete answers to at least 5 of the 10 questions
- [ ] Parent Document Retriever gives complete, contextually rich answers to all 10 questions
- [ ] Participant can explain *why* the child chunk retrieved was insufficient and what additional context the parent provided

### Assignment 2 — Negation and Numeric Queries
- [ ] Naive RAG gives incorrect or misleading answers to all 6 Section A questions
- [ ] Pre-filtered approach correctly identifies patients with BP > 200 who failed treatment
- [ ] Negation queries ("did NOT respond", "contraindicated") are handled correctly by the structured filter
- [ ] Participant can articulate why embedding similarity is fundamentally unsuited for threshold and negation queries
