# Hybrid RAG for BFSI — Synthetic Dataset Description & Demo Guide

**Project:** Project 3 — Hybrid RAG for BFSI Customer Risk, Retention & Next-Best-Action Intelligence  
**Dataset Version:** 1.0  
**Last Updated:** December 2024

---

## Overview

This synthetic dataset supports an end-to-end demo of a Hybrid RAG system for a retail bank. It simulates the data ecosystem of a mid-to-large Indian private bank with 50 customers spanning Premium, HNI, Retail, SME, and Youth segments. Data is intentionally seeded with realistic patterns to demonstrate every stage of the progressive demo script.

---

## Dataset Inventory

| File | Format | Records | Description |
|------|--------|---------|-------------|
| `customers/customer_profiles.json` | JSON | 50 | Master customer profiles with demographics, balances, churn scores |
| `customers/customer_profiles.csv` | CSV | 50 | Same, tabular format |
| `customers/product_holdings.csv` | CSV | ~200 | Product-level holdings per customer |
| `customers/customer_risk_scorecards.json` | JSON | 50 | Rules-based composite risk scores (Demo Step 2) |
| `customers/customer_risk_scorecards.csv` | CSV | 50 | Same, tabular |
| `customers/nba_recommendations.json` | JSON | 15 | AI-generated Next-Best-Action records with HITL status |
| `customers/nba_recommendations.csv` | CSV | 15 | Same, tabular |
| `transactions/transaction_event_summaries.csv` | CSV | 600 | Monthly deposit/withdrawal summaries per customer (12 months) |
| `complaints/complaint_logs.csv` | CSV | ~92 | Individual complaint records with severity, resolution, CSAT |
| `call_center_notes/call_center_notes.json` | JSON | ~83 | Unstructured agent/RM notes (rich text, for LLM summarization) |
| `call_center_notes/call_center_notes.csv` | CSV | ~83 | Same, tabular |
| `call_center_notes/service_interaction_log.json` | JSON | ~161 | Structured service touchpoint log |
| `call_center_notes/service_interaction_log.csv` | CSV | ~161 | Same, tabular |
| `products/product_catalog.json` | JSON | 10 | Bank product definitions, features, eligibility |
| `products/product_catalog.csv` | CSV | 10 | Same, tabular |
| `retention_offers/retention_offers.json` | JSON | 10 | Approved retention offers with compliance checks |
| `retention_offers/retention_offers.csv` | CSV | 10 | Same, tabular |
| `risk_rules/risk_rules.json` | JSON | 10 | Business rules for churn/credit risk scoring |
| `risk_rules/risk_rules.csv` | CSV | 10 | Same, tabular |
| `policy_documents/customer_retention_policy.md` | Markdown | — | Full retention policy with HITL and PII rules |
| `policy_documents/credit_risk_policy.md` | Markdown | — | Credit risk tiers, exposure limits, AI advisory rules |
| `policy_documents/complaint_escalation_sop.md` | Markdown | — | Complaint TAT, regulatory escalation, AI restrictions |
| `policy_documents/investment_suitability_policy.md` | Markdown | — | SEBI/IRDAI suitability matrix, AI mis-selling safeguards |
| `regulatory_guidance/rbi_guidelines_summary.md` | Markdown | — | RBI KYC, grievance, credit card, data privacy rules |
| `regulatory_guidance/sebi_amfi_investment_rules.md` | Markdown | — | SEBI MF, IRDAI insurance, robo-advisory regulations |
| `knowledge_graph/kg_nodes.json` | JSON | 45 | Graph nodes (Customers, Products, RiskSignals, Offers) |
| `knowledge_graph/kg_edges.json` | JSON | ~147 | Graph relationships |
| `knowledge_graph/kg_schema_cypher.txt` | Text | — | Cypher CREATE statements for Neo4j import |
| `knowledge_graph/kg_schema_description.md` | Markdown | — | Graph schema, node/edge types, key demo paths |

---

## Embedded Data Patterns

The dataset is intentionally seeded with the following patterns to make each demo step compelling:

### Pattern A — High-Risk Premium Churners (CUST0001–CUST0010)
- **Segment:** Premium
- **Balance:** Dropped 30–60% over 6 months (withdrawals consistently exceed deposits in transaction data)
- **Complaints:** 3–7 complaints in the last 12 months; mix of HIGH severity (unauthorized charges, card blocked); several unresolved
- **Call Notes:** Contain competitor bank mentions (HDFC, ICICI), RM change frustration, threat of account closure
- **Products Held:** Only 1–2 (low cross-sell penetration)
- **Last Login:** 45–120 days ago (disengaged)
- **Churn Score:** 0.72–0.95
- **NBA Trigger:** CRITICAL tier — mandatory RM call + retention offer within 24hrs + HITL approval required

### Pattern B — Medium-Risk Fence-Sitters (CUST0011–CUST0025)
- **Balance:** Stable or slight decline
- **Complaints:** 1–3; mostly MEDIUM severity (interest rate complaints, loan rejection)
- **Call Notes:** Competitor enquiries; EMI restructuring requests; neutral-to-negative sentiment
- **Products Held:** 2–4 (moderate penetration)
- **Last Login:** 15–45 days
- **Churn Score:** 0.35–0.72
- **NBA Trigger:** HIGH tier — RM outreach within 48 hours; cross-sell or rate offer

### Pattern C — Loyal Retained Customers (CUST0026–CUST0050)
- **Balance:** High and growing; deposits dominate
- **Complaints:** 0–1; LOW severity; quickly resolved
- **Products Held:** 4–8 (deep cross-sell; demat, insurance, MF, home loan)
- **Last Login:** 1–14 days
- **Churn Score:** 0.05–0.35
- **NBA Trigger:** LOW tier; maintenance engagement; potential upsell to wealth management

### Pattern D — Compliance Edge Cases (across segments)
- Several customers have `kyc_status = PENDING` — triggers KYC restriction rule
- NBA records for HIGH-risk investment offers (`OFF008 NRI Remittance Cashback`, `OFF009 MF SIP Exit Load Waiver`) are flagged with `blocked_reason` showing compliance holds
- Complaint records include cases where `repeat_complaint = True` and `escalated = True` — triggers HITL mandatory escalation
- Call notes contain explicit competitor comparisons — these seed the "competitor mention" risk signal in the knowledge graph

### Pattern E — Knowledge Graph Evidence Chains
- CUST0001–CUST0005 have multi-hop evidence paths: Customer → EXHIBITS_RISK (3 signals) → ELIGIBLE_FOR_OFFER → GOVERNED_BY Policy
- Risk signals weighted to produce composite scores > 0.7 when all three (balance drop + complaints + low engagement) co-occur
- Cypher queries in `kg_schema_cypher.txt` reproduce these paths for Neo4j demo

---

## Demo Step ↔ Dataset Mapping

| Demo Step | What to Show | Key Files |
|-----------|-------------|-----------|
| 1 | Pose the customer question | `customer_profiles.json` — CUST0001 |
| 2 | Rules-based scorecard | `customer_risk_scorecards.csv`, `risk_rules.json` |
| 3 | LLM summarization of notes | `call_center_notes.json` — filter by CUST0001 |
| 4 | RAG over policy/product docs | `retention_offers.json` + `customer_retention_policy.md` |
| 5 | Structured context retrieval | `complaints/`, `transactions/`, `service_interaction_log.json` |
| 6 | Knowledge graph traversal | `kg_nodes.json`, `kg_edges.json`, `kg_schema_cypher.txt` |
| 7 | Hybrid retrieval + NBA | `nba_recommendations.json` — CUST0001 record |
| 8 | Compliance guardrails | `nba_recommendations.json` — `blocked_reason` field; `regulatory_guidance/` |
| 9 | HITL approval workflow | `nba_recommendations.json` — `hitl_status`, `hitl_required` fields |
| 10 | Limitations discussion | All sources — synthetic data caveats |
| 11 | Future scope | All sources — streaming, uplift model hooks |

---

## Demo Questions — By Stage

Use these questions verbatim in the demo to drive each retrieval stage.

### Stage 1 — Framing the Problem
> **Q1.** "Why is CUST0001 at risk of churn, and what should the Relationship Manager do next?"

> **Q2.** "Which of our Premium segment customers are at the highest risk of leaving in the next 30 days?"

> **Q3.** "Give me a churn risk summary for CUST0003 — including balance trends, complaints, and engagement signals."

---

### Stage 2 — Rules-Based Scorecard (Demo Step 2)
> **Q4.** "Run the rules-based risk scorecard for CUST0001 and explain which rules fired and why."

> **Q5.** "How many customers have triggered the 'Balance Drop Alert' rule (RULE001) in the current scoring period?"

> **Q6.** "What is the composite risk score for CUST0005, and which individual risk signals contributed most to it?"

---

### Stage 3 — LLM Summarization of Interaction Notes (Demo Step 3)
> **Q7.** "Summarize all call center notes and service interactions for CUST0001 in the last 6 months. What are the key themes?"

> **Q8.** "Which competitor banks has CUST0002 mentioned across their interaction history? What was the context?"

> **Q9.** "From the interaction notes, what is CUST0004's stated reason for dissatisfaction? Is there a pattern across their complaints?"

*(Highlight here: LLM summarizes well but may suggest actions not grounded in policy — set up for Step 4)*

---

### Stage 4 — Policy-Grounded RAG (Demo Step 4)
> **Q10.** "Which retention offers are permitted for CUST0001 given their segment and current balance? Cross-check against the retention policy."

> **Q11.** "Can the RM offer CUST0001 a 0.5% FD rate upgrade without Credit Committee approval? What does the policy say?"

> **Q12.** "What are the HITL approval requirements before making a retention offer to a customer with churn score above 0.85?"

> **Q13.** "The agent suggested waiving CUST0002's annual card fee AND reducing their loan ROI in the same interaction. Is this permitted by policy?"

---

### Stage 5 — Structured Context Retrieval (Demo Step 5)
> **Q14.** "Summarize the risk drivers for CUST0003 across three dimensions: complaint history, transaction trends, and channel engagement."

> **Q15.** "Show the monthly net cash flow trend for CUST0001 over the last 12 months. Is there a deterioration pattern?"

> **Q16.** "How many complaint records for CUST0001 remain unresolved? What is the total elapsed time past resolution SLA?"

---

### Stage 6 — Knowledge Graph Evidence Path (Demo Step 6)
> **Q17.** "Trace the complete evidence path behind CUST0001's churn risk — from account signals through to which retention offers are eligible and what policy governs each."

> **Q18.** "Which risk signals does CUST0001 exhibit, what is the weight of each, and how do they combine into the final churn score?"

> **Q19.** "Show all customers who share the same risk signal combination as CUST0001 (balance drop + complaints + low engagement). How many are there?"

---

### Stage 7 — Hybrid Retrieval + Next-Best-Action (Demo Step 7)
> **Q20.** "Generate a final next-best-action recommendation for CUST0001 with: (a) recommended offer, (b) rationale with evidence from all three retrieval layers, (c) risk warnings, and (d) compliance constraints."

> **Q21.** "Across the three retrieval layers — structured data, interaction notes, and policy documents — what is the single strongest signal driving the churn recommendation for CUST0001?"

> **Q22.** "For CUST0008 (SME segment), what is the recommended next-best-action? Which documents were retrieved to ground the recommendation?"

---

### Stage 8 — Compliance Guardrails (Demo Step 8)
> **Q23.** "CUST0001 has asked the RM to recommend specific mutual fund schemes with guaranteed returns. Why should this recommendation be blocked, and what regulatory rule applies?"

> **Q24.** "The NBA system recommended OFF009 (MF SIP Exit Load Waiver) for CUST0005. Why is this flagged as a compliance hold? What approval is needed?"

> **Q25.** "Show me an example of a recommendation that was auto-blocked due to a PII or unauthorized-advice guardrail. Explain the trigger."

> **Q26.** "A customer with churn score 0.91 has an active RBI Ombudsman complaint. Can the RM make a retention offer? What does the complaint escalation SOP say about this?"

---

### Stage 9 — HITL Approval Workflow (Demo Step 9)
> **Q27.** "Show all pending HITL approvals in the NBA queue. Which ones require Regional Head sign-off versus Branch Manager?"

> **Q28.** "RM003 rejected the NBA recommendation for CUST0007. What edited recommendation did they substitute, and how will this be used to improve the model?"

> **Q29.** "For CUST0001's recommendation, walk through the full HITL gate: who must approve, what information is shown to the approver, and what audit log is created?"

---

### Stage 10 & 11 — Limitations and Future Scope
> **Q30.** "What are the key limitations of this synthetic dataset that would need to be addressed before deploying this system in production?"

> **Q31.** "If we integrated a calibrated real-time churn model output, how would the risk scorecard change? Which signals would be replaced versus supplemented?"

> **Q32.** "How would you extend this system to support real-time event streaming — for example, flagging a customer immediately when a large withdrawal exceeds INR 5 lakh?"

---

## Suggested High-Impact Demo Sequence

For a 30-minute stakeholder demo, use this sequence to show maximum value progression:

1. **Q1** → Show the business question  
2. **Q4** → Rules scorecard fires (RULE001, RULE002, RULE003 all fire for CUST0001)  
3. **Q7** → LLM notes summary (competitor mention surfaced)  
4. **Q10 + Q11** → Policy grounding catches what raw LLM missed  
5. **Q17** → Knowledge graph evidence chain (the "wow" moment)  
6. **Q20** → Full hybrid NBA recommendation with all evidence layers  
7. **Q24** → Compliance guardrail fires and blocks offer  
8. **Q29** → HITL workflow completes the loop  

---

## Data Generation Notes

- Random seed: `42` for structured data, `99` for interactions — results are fully reproducible
- PII: All customer names are anonymized (`Customer_XXXX` placeholders) — no real names or identifiers
- Patterns are inserted deterministically: CUST0001–CUST0010 are always HIGH risk with strong evidence chains
- Financial amounts are in INR and reflect realistic ranges for an Indian private bank (2024 context)
- Regulatory references cite real RBI, SEBI, and IRDAI documents but are paraphrased, not verbatim

