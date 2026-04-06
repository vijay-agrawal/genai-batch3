# Machine Learning Use-Cases in Healthcare — Company Tech Context

Mapping supervised and unsupervised ML techniques to three core Company Tech business domains:
**Claims Management**, **Prior Authorization**, and **Med-Tech ISO Workflows**.

---

## Overview: Supervised vs Unsupervised in Healthcare

| Dimension | Supervised ML | Unsupervised ML |
|-----------|--------------|-----------------|
| **Requires labels?** | Yes — historical outcomes (approved/denied, fraud/not-fraud) | No — discovers patterns without pre-defined categories |
| **Output** | Prediction or classification on new records | Clusters, anomalies, latent groupings |
| **When to use** | You know what "right" looks like from past data | You're exploring unknown structure or have no labeled data |
| **Healthcare examples** | Claim denial prediction, auth approval likelihood | Billing pattern anomalies, patient risk cohorts |

---

## 1. Claims Management

### Business Context
Claims adjudication involves thousands of daily transactions. Errors, fraud, and inefficiencies drive up administrative cost and delay reimbursement. ML accelerates adjudication, flags risk, and surfaces patterns invisible to rule engines.

---

### Supervised Use-Cases

#### 1.1 Claim Denial Prediction
**Goal:** Before submitting a claim, predict whether it will be denied.

| Item | Detail |
|------|--------|
| **Label** | `denied` / `approved` (from historical adjudication) |
| **Key Features** | Diagnosis code (ICD-10), procedure code (CPT), payer ID, place of service, provider NPI, patient demographics, prior denial history |
| **Algorithms** | Gradient Boosting (XGBoost), Logistic Regression for explainability |
| **Business Value** | Fix claims before submission → reduce rework, accelerate cash flow |
| **Company Angle** | Train on Company-processed claims corpus; model learns payer-specific denial patterns |

**Conceptual feature → outcome mapping:**
```
ICD-10 mismatch + missing modifier  →  High denial probability
CPT within payer coverage + clean modifier  →  Low denial probability
```

---

#### 1.2 Fraud, Waste & Abuse (FWA) Detection
**Goal:** Classify claims as legitimate or potentially fraudulent.

| Item | Detail |
|------|--------|
| **Label** | `fraud` / `legitimate` (from audit outcomes or SIU decisions) |
| **Key Features** | Billing frequency per provider, procedure-to-diagnosis ratio, upcoding signals, geographic anomaly, duplicate claim indicators |
| **Algorithms** | Random Forest, Gradient Boosting; SMOTE for extreme class imbalance |
| **Business Value** | Intercept fraudulent claims before payment; protect payers and self-insured employers |
| **Metric Focus** | High recall (don't miss fraud) with acceptable precision (avoid flagging legitimate providers) |

---

#### 1.3 Claim Routing & Auto-Adjudication
**Goal:** Predict whether a claim can be auto-adjudicated (no human review needed) vs. requires manual work.

| Item | Detail |
|------|--------|
| **Label** | `auto-adjudicated` / `manual-review` (from ops logs) |
| **Key Features** | Claim complexity score, code pair edits, payer-specific rules hit, member eligibility flags |
| **Algorithms** | Decision Tree (interpretable for ops), Random Forest |
| **Business Value** | Increase straight-through processing (STP) rate; reduce ops headcount on simple claims |

---

### Unsupervised Use-Cases

#### 1.4 Billing Pattern Anomaly Detection
**Goal:** Without labeled fraud data, surface providers whose billing behavior is statistically unusual.

| Item | Detail |
|------|--------|
| **Technique** | Isolation Forest, Local Outlier Factor (LOF), Autoencoders |
| **Signals** | Procedure mix deviation from specialty peers, unusual service duration, weekend/holiday billing spikes |
| **Business Value** | Prioritize audits on high-risk providers without needing historical fraud labels |
| **Company Angle** | Especially valuable when onboarding a new payer client with no prior fraud audit history |

---

#### 1.5 Provider & Claim Clustering
**Goal:** Discover natural segments in provider behavior or claim types.

| Item | Detail |
|------|--------|
| **Technique** | K-Means, DBSCAN |
| **Features** | Average claim value, specialty, denial rate, CPT mix, patient volume |
| **Discovered Segments (example)** | "High-volume clean billers", "Complex case specialists", "Outlier pattern billers" |
| **Business Value** | Targeted intervention per cluster — streamlined processing for clean billers, enhanced review for outlier cluster |

---

## 2. Prior Authorization

### Business Context
Prior auth (PA) is a bottleneck: payers require pre-approval for certain procedures, creating administrative burden for providers and delays for patients. ML can predict outcomes, prioritize queues, and automate routine decisions.

---

### Supervised Use-Cases

#### 2.1 Prior Auth Approval Likelihood Prediction
**Goal:** Predict whether a PA request will be approved, denied, or require peer review.

| Item | Detail |
|------|--------|
| **Label** | `approved` / `denied` / `peer-review` (from historical PA decisions) |
| **Key Features** | CPT code, ICD-10, payer ID, plan type, member's clinical history, provider specialty, prior PA outcomes for same code/payer pair |
| **Algorithms** | Multi-class Gradient Boosting, Logistic Regression (per payer) |
| **Business Value** | Alert providers before submission when denial is likely; suggest alternative codes or documentation; reduce unnecessary submissions |

**Example prediction output:**
```
PA Request: CPT 27447 (Total Knee Replacement), Payer: BCBS-TX
→ Approval probability: 82%
→ Top denial risk factor: Missing conservative treatment documentation (PT records)
→ Recommendation: Attach 6-week PT notes before submitting
```

---

#### 2.2 PA Urgency Classification
**Goal:** Triage incoming PA requests by clinical urgency to route stat cases to the front of the queue.

| Item | Detail |
|------|--------|
| **Label** | `urgent` / `routine` / `expedited` |
| **Key Features** | Diagnosis severity score, hospitalization flag, procedure type, submitting provider's urgency designation, patient age |
| **Algorithms** | Logistic Regression, SVM |
| **Business Value** | Patients with time-sensitive needs get faster decisions; reduces liability risk for payers |

---

#### 2.3 Clinical Documentation Completeness Scoring
**Goal:** Predict whether submitted clinical notes contain sufficient evidence to support the PA, before a reviewer reads them.

| Item | Detail |
|------|--------|
| **Label** | `complete` / `incomplete` (based on reviewer outcomes) |
| **Key Features** | NLP features extracted from clinical notes — presence of diagnosis mention, treatment history, physician attestation, specific lab values |
| **Algorithms** | Text classification (TF-IDF + Logistic Regression); BERT-based classifier for higher accuracy |
| **Business Value** | Auto-request missing documentation immediately; reduce back-and-forth cycles from weeks to hours |

---

### Unsupervised Use-Cases

#### 2.4 PA Request Pattern Clustering
**Goal:** Group PA requests to identify high-volume, low-variation procedures suitable for auto-approval policies.

| Item | Detail |
|------|--------|
| **Technique** | K-Means on procedure/diagnosis/payer feature vectors |
| **Discovered Insight** | Cluster of "routine orthopedic PAs from in-network providers with consistent documentation" → candidate for auto-approval |
| **Business Value** | Policy recommendation: remove unnecessary friction for predictable approvals; focus clinical review capacity on complex cases |

---

#### 2.5 Denial Reason Clustering (Topic Modeling)
**Goal:** Discover the dominant reasons for PA denials without pre-defining categories.

| Item | Detail |
|------|--------|
| **Technique** | Latent Dirichlet Allocation (LDA) or BERTopic on free-text denial reason fields |
| **Discovered Topics (example)** | "Missing conservative therapy documentation", "Not medically necessary — lacks clinical criteria", "Out-of-network provider" |
| **Business Value** | Operations insight dashboard — track which denial reason cluster is growing; feed back into provider education |

---

## 3. Med-Tech ISO Workflows

### Business Context
Medical device and health IT companies operating under ISO 13485 (quality management) and ISO/IEC 62304 (software lifecycle) generate rich audit trails, non-conformance reports (NCRs), CAPA records, and change control logs. ML helps move from reactive compliance to predictive quality management.

---

### Supervised Use-Cases

#### 3.1 Non-Conformance Risk Classification
**Goal:** When a new NCR is created, predict its severity level and escalation likelihood.

| Item | Detail |
|------|--------|
| **Label** | `major` / `minor` / `observation` severity (from historical NCR dispositions) |
| **Key Features** | Product category, NCR description text (NLP), device class (Class I/II/III), source (audit/complaint/internal), prior NCR history on same product line |
| **Algorithms** | Text classification (TF-IDF + Random Forest), BERT fine-tuned on quality records |
| **Business Value** | Prioritize major NCRs for immediate CAPA initiation; prevent minor issues from ballooning due to delayed response |

---

#### 3.2 CAPA Effectiveness Prediction
**Goal:** Predict whether a Corrective and Preventive Action (CAPA) will be closed successfully on first review or require re-work.

| Item | Detail |
|------|--------|
| **Label** | `effective` / `requires-rework` (from CAPA closure audit outcomes) |
| **Key Features** | Root cause category, corrective action description completeness, responsible owner's historical effectiveness rate, days-to-action |
| **Algorithms** | Logistic Regression, Gradient Boosting |
| **Business Value** | Flag likely-ineffective CAPAs early; prompt quality engineers to strengthen root cause analysis before submission to auditors |

---

#### 3.3 Audit Finding Prediction (Pre-Audit Risk Scoring)
**Goal:** Before a regulatory or notified body audit, score each process area by likelihood of generating a finding.

| Item | Detail |
|------|--------|
| **Label** | `finding raised` / `no finding` (from prior audit outcomes mapped to process areas) |
| **Key Features** | Days since last process review, open NCR count, CAPA overdue rate, change control volume, training completion rate |
| **Algorithms** | Logistic Regression (interpretable for compliance teams), Random Forest |
| **Business Value** | Focus pre-audit remediation effort on highest-risk process areas; demonstrate proactive quality culture to auditors |

---

#### 3.4 Change Control Impact Classification
**Goal:** Classify incoming engineering change orders (ECOs) by regulatory impact — does this change require a new 510(k) or PMA supplement?

| Item | Detail |
|------|--------|
| **Label** | `significant change` (regulatory submission needed) / `non-significant` |
| **Key Features** | Change type (hardware/software/labeling), device class, affected component criticality, prior similar change outcomes |
| **Algorithms** | Decision Tree (explainable, auditable), Random Forest |
| **Business Value** | Reduce regulatory affairs bottleneck; prevent under-filing (compliance risk) and over-filing (cost/time risk) |

---

### Unsupervised Use-Cases

#### 3.5 Complaint & NCR Clustering for Trend Detection
**Goal:** Automatically group incoming customer complaints and NCRs to surface emerging product quality signals before they become reportable events.

| Item | Detail |
|------|--------|
| **Technique** | K-Means or DBSCAN on NLP-vectorized complaint text + product metadata |
| **Discovered Value** | A cluster of similar complaints about "device connectivity failure in cold environments" emerges months before individual complaints would trip a threshold |
| **Business Value** | Early warning system — initiate field investigation before MDR/MDV reporting obligation triggers; protect patient safety |
| **ISO 13485 Relevance** | Supports clause 8.2.2 (post-market surveillance) and complaint handling procedures |

---

#### 3.6 Process Anomaly Detection in Quality Records
**Goal:** Detect unusual patterns in quality system activity without labeled examples of "bad" quality behavior.

| Item | Detail |
|------|--------|
| **Technique** | Isolation Forest on quality metrics time-series (NCR open rate, CAPA overdue ratio, training gap %) |
| **Signals** | Sudden spike in NCR volume from a single product line, unusual CAPA cycle time elongation |
| **Business Value** | Proactive quality management — catch process degradation between audit cycles |

---

#### 3.7 Supplier Risk Profiling via Clustering
**Goal:** Segment the supplier base by quality and delivery performance patterns to stratify audit frequency.

| Item | Detail |
|------|--------|
| **Technique** | K-Means on supplier scorecards |
| **Features** | NCR rate per delivery, on-time delivery %, corrective action response time, part criticality |
| **Discovered Segments** | "Tier-1 reliable", "Improving suppliers", "At-risk suppliers", "Critical watch list" |
| **Business Value** | Risk-based supplier audit schedule (ISO 13485 clause 7.4); concentrate auditor time on at-risk cluster |

---

## Cross-Domain Summary

| Domain | Supervised Techniques | Unsupervised Techniques |
|--------|----------------------|------------------------|
| **Claims Mgmt** | Denial prediction, FWA classification, auto-adjudication routing | Billing anomaly detection, provider clustering |
| **Prior Auth** | Approval likelihood, urgency triage, documentation scoring | Request pattern clustering, denial reason topic modeling |
| **Med-Tech ISO** | NCR severity classification, CAPA effectiveness, audit risk scoring, change control impact | Complaint trend clustering, process anomaly detection, supplier risk profiling |

---

## Shared ML Pipeline Considerations

### Data Quality (The Universal Constraint)
- Claims and PA data often have **inconsistent coding** — same procedure coded differently across payers or time. Normalization before feature engineering is mandatory.
- Quality records are **text-heavy** — invest in NLP preprocessing (tokenization, domain-specific stopwords like ICD codes in free text).
- All three domains have **class imbalance** (fraud is rare, major NCRs are rare, PA denials vary by payer). Use SMOTE, class weighting, or threshold tuning — never trust raw accuracy.

### Explainability is Non-Negotiable
Healthcare ML outputs must be explainable to clinicians, compliance officers, and regulators.
- Use **SHAP values** to attribute predictions to individual features.
- Prefer **Logistic Regression or shallow Decision Trees** for high-stakes decisions even if ensemble models score slightly higher.
- Log every model version, training dataset, and prediction — required for ISO 13485 change control and payer audit trails.

### Model Governance
| Requirement | Why It Matters in Healthcare |
|-------------|------------------------------|
| Version-controlled models | Regulatory traceability (ISO 62304, OIG audit) |
| Documented training data | Demonstrate absence of bias in claims/PA decisions |
| Periodic retraining triggers | Payer policy changes invalidate older denial models within months |
| Human-in-the-loop for high-stakes decisions | No fully automated denial of a PA request without clinical review |
