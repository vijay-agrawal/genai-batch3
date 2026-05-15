# LangGraph Demand Sensing & Supply Chain Command Center Copilot
## Synthetic Dataset Description & Demo Guide

**Project:** Project 5 — LangGraph Demand Sensing & Supply Chain Command Center Copilot  
**Dataset Version:** 1.0  
**Coverage:** 16 weeks (Jan 6 – Apr 20, 2025) | 10 SKUs | 10 Stores | 5 Regions  
**Domain:** Supply Chain Analytics; Demand Sensing; Inventory Management

---

## Overview

This dataset simulates the full data environment for a CPG/retail supply chain command centre copilot. It covers 10 SKUs across 10 stores in 5 regions over 16 weeks, with 5 deliberate anomaly scenarios each requiring a different LangGraph node path, routing decision, and recommendation type. The dataset is designed to demonstrate every stage of the progressive demo — from threshold rule limitations through LangGraph tool calls, routing, root-cause diagnosis, recommendation, critique, and HITL approval — including a data anomaly case that correctly produces **no action**.

---

## Dataset Inventory

| File | Format | Records | Description |
|------|--------|---------|-------------|
| `sku_demand_data/sku_store_week_demand.json` | JSON | 1,600 | SKU × store × week demand: actual vs forecast, anomaly flags, drivers |
| `sku_demand_data/sku_store_week_demand.csv` | CSV | 1,600 | Same, tabular |
| `sku_demand_data/sku_master.json` | JSON | 10 | SKU name, category, cost, price, lead time, supplier |
| `sku_demand_data/sku_master.csv` | CSV | 10 | Same, tabular |
| `inventory_snapshots/inventory_snapshots.json` | JSON | 1,600 | SOH, in-transit, on-order, weeks-of-cover, status, stockout date |
| `inventory_snapshots/inventory_snapshots.csv` | CSV | 1,600 | Same, tabular |
| `promotion_calendar/promotion_calendar.json` | JSON | 6 | Promos: SKUs, regions, uplift, mechanic, notes |
| `promotion_calendar/promotion_calendar.csv` | CSV | 6 | Same, tabular |
| `supplier_delay_logs/supplier_delay_logs.json` | JSON | 5 | Delays: reason, days, severity, mitigation, financial impact |
| `supplier_delay_logs/supplier_delay_logs.csv` | CSV | 5 | Same, tabular |
| `supplier_delay_logs/supplier_master.json` | JSON | 6 | Supplier reliability scores, OTD%, contact, tier |
| `supplier_delay_logs/supplier_master.csv` | CSV | 6 | Same, tabular |
| `weather_event_data/weather_event_signals.json` | JSON | 6 | Heatwave, festival, flash sale, IPL, monsoon, competitor signals |
| `weather_event_data/weather_event_signals.csv` | CSV | 6 | Same, tabular |
| `shipment_data/shipment_data.json` | JSON | 1,631 | Per-shipment: planned vs actual arrival, delay, carrier, status |
| `shipment_data/shipment_data.csv` | CSV | 1,631 | Same, tabular |
| `service_level_targets/service_level_targets.json` | JSON | 10 | Per-SKU: fill rate %, cover min/max, criticality, HITL thresholds |
| `service_level_targets/service_level_targets.csv` | CSV | 10 | Same, tabular |
| `langgraph_state_schema/state_schema.json` | JSON | 1 | Full state schema with field descriptions, routing logic, tool list |
| `agent_outputs/langgraph_scenario_traces.json` | JSON | 5 | Gold-standard node-by-node traces for all 5 anomaly scenarios |
| `agent_outputs/whatif_simulation_results.json` | JSON | 5 | What-if simulation outputs: cover before/after, cost, stockout avoided |
| `agent_outputs/whatif_simulation_results.csv` | CSV | 5 | Same, tabular |
| `agent_outputs/agent_trace_log.json` | JSON | 85 | Per-tool-call trace: node, tool, status, latency, tokens, cost |
| `agent_outputs/agent_trace_log.csv` | CSV | 85 | Same, tabular |
| `evaluation_set/sc_eval_benchmark.json` | JSON | 12 | Evaluation cases mapped to each demo step with expected outputs |
| `evaluation_set/sc_eval_benchmark.csv` | CSV | 12 | Same, tabular |
| `metadata/metadata_registry.json` | JSON | 11 | Registry of all files, row counts, key fields, consuming tools |

**Total: 28 files across 10 folders**

---

## The Five Anomaly Scenarios (Demo Drivers)

Each scenario exercises a different LangGraph node path and teaches a distinct lesson about the value of multi-node agentic AI over simple rules.

---

### SC-001 — Week 7 (Feb 03): Holi Promotion Spike → Inventory Underposition
**SKUs affected:** SKU-001 (PremiumOats), SKU-007 (GreenTea) | **Region:** North

**What happened:** PROMO-001 (Holi festive display) drove 145% demand uplift — 25pp above the 120% forecast. Inventory was pre-positioned for 120%, leaving North stores understocked.

**LangGraph node path:**
- `detect_node` → STOCKOUT_RISK (0.7 and 0.9 weeks cover)  
- `diagnose_node` → HOLI_PROMO_UPLIFT (confidence 0.89) + INVENTORY_POSITIONING_MISS  
- `recommend_node` → Inter-store transfer STR-008→STR-002 (400 units, INR 8,500 — auto-approved) + Expedite 600u (INR 42,000 — HITL)  
- `critique_node` → PASS  
- `hitl_outcome` → APPROVED WITH EDIT: 400u expedite (not 600u — transfer covers 200u)

**Key demo lesson:** Promotion calendar tool is essential. Threshold rule would flag low cover but cannot attribute to promo uplift or recommend inter-store transfer vs expedite.

---

### SC-002 — Week 9 (Feb 17): Supplier B Shutdown → Supply-Side Stockout (CRITICAL)
**SKUs affected:** SKU-002 (InstaNoodles), SKU-005 (ProteinBar) | **Region:** East, Central

**What happened:** SUP-B production line shutdown (conveyor failure) — 10-day delay on 4,200 + 1,800 units. Demand is completely normal; the inventory drop is 100% supply-driven.

**LangGraph node path:**
- `detect_node` → STOCKOUT_RISK (0.4 weeks cover) — looks like demand collapse  
- `diagnose_node` → SUPPLIER_SHUTDOWN (confidence 0.97); demand normal confirmed  
- `recommend_node` → Activate SUP-F backup (30% capacity, INR 62K) + Cross-region transfer West→East (1,800u, INR 38K) + flag SKU-005 as no-mitigation-available  
- `critique_node` → PASS_WITH_FLAGS: SUP-F max capacity 30% enforced  
- `hitl_outcome` → APPROVED by SCM Director + customer advisory issued for SKU-005

**Key demo lesson — the most important in the dataset:** A threshold rule or simple LLM reads this as a demand crash and may recommend promotions or demand-stimulation. The root-cause node correctly identifies it as supply failure, completely changing the recommendation type. This is the "supply vs demand disambiguation" demo moment.

---

### SC-003 — Week 11 (Mar 03): Heatwave Demand Spike → Compound Signal
**SKUs affected:** SKU-003 (ColdBrew), SKU-010 (Sunscreen) | **Region:** South, West

**What happened:** South India heatwave (43°C peak) drives +80% cold beverage and +60% sunscreen demand — overlapping with PROMO-003 Summer Ready Campaign. Cannot deconvolve without MMM.

**LangGraph node path:**
- `detect_node` → STOCKOUT_RISK SKU-003 (0.8 weeks); LOW SKU-010 (1.1 weeks)  
- `diagnose_node` → HEATWAVE (0.85) + PROMO_003 (0.74); **compound signal warning issued**; SUP-C 6-day delay complicates expedite  
- `recommend_node` → Bridge transfer North→South 300u (auto-approved INR 12K) + Expedite 1,000u from SUP-C subject to QA clearance (HITL)  
- `critique_node` → flags QA clearance as constraint; caps confidence at 0.79  
- `hitl_outcome` → APPROVED WITH EDIT: 700u not 1,000u (weather forecast shows cooling; QA approved)

**Key demo lesson:** Root-cause node correctly caveats compound signals rather than over-claiming one driver. Critique node catches the QA constraint. HITL uses external weather forecast (shorter cooling horizon) to reduce expedite volume — human judgment that AI cannot access.

---

### SC-004 — Week 14 (Mar 24): Cancelled Corporate Order → Overstock + Counter-Intuitive Recommendation
**SKUs affected:** SKU-004 (EcoDetergent) | **Region:** West

**What happened:** A 2,000-unit corporate bulk contract (PROMO-004) was cancelled. Pre-positioned inventory creates 4.8x weeks of cover. Simultaneously, SUP-D has a quality hold on an incoming batch.

**LangGraph node path:**
- `detect_node` → OVERSTOCK (4.8 weeks cover, demand=0)  
- `diagnose_node` → CORPORATE_ORDER_CANCELLATION (confidence 0.99); supplier delay is BENEFICIAL  
- `recommend_node` → Redistribute 800u West→All regions (INR 32K, branch manager approval) + Optional markdown + **DO NOT EXPEDITE SUP-D** (counter-intuitive non-action)  
- `critique_node` → PASS; validates the non-action recommendation  
- `hitl_outcome` → APPROVED by branch manager

**Key demo lesson:** The critical recommendation is the one that says *do nothing on supply* — do not expedite the SUP-D batch. A threshold rule would ignore overstock context and potentially trigger a routine replenishment. The diagnose node correctly identifies the corporate cancellation and validates the counter-intuitive "delay is beneficial" finding.

---

### SC-005 — Week 16 (Apr 07): POS Data Anomaly → False Positive Prevented
**SKUs affected:** SKU-008 (WholeMilk) | **Region:** All

**What happened:** POS system glitch during a brand app flash sale recorded 3x demand for SKU-008. True demand is normal. Inventory position unchanged (2.2 weeks cover). A threshold system would have triggered an urgent expedite order.

**LangGraph node path:**
- `detect_node` → apparent DEMAND_SPIKE (3x) — but cover is 2.2 weeks (anomaly: spike + normal cover is contradictory)  
- `diagnose_node` → POS_DATA_ANOMALY (confidence 0.91); demand and inventory signals contradict → DATA_ANOMALY route  
- `recommend_node` → FLAG ONLY — do not expedite; no supply action  
- `critique_node` → PASS; false positive prevention confirmed

**Key demo lesson (Demo Step 2 comparison):** A threshold rule would have triggered an expedite order of ~INR 85,000 that was completely unnecessary. The LangGraph cross-signal contradiction check (demand spike × inventory unchanged) correctly routes to the data anomaly path and prevents the false-positive action. The correct outcome is *inaction* — and the copilot must justify that clearly.

---

## Estimated Value Demonstrated Across 5 Scenarios

| Scenario | Threshold Rule Action | LangGraph Action | Cost Saving / Outcome |
|----------|----------------------|-----------------|----------------------|
| SC-001 Holi Promo | No action (no root cause) | Inter-store transfer + targeted expedite | Stockout averted; INR 14K less than full expedite |
| SC-002 Supplier Fail | Demand promotion (wrong response) | Backup supplier + cross-region transfer | Correct response type; INR 100K approved |
| SC-003 Heatwave | Full expedite (over-order) | Bridge transfer + 700u expedite with QA | INR 37K saved vs 1,000u order |
| SC-004 Overstock | Routine replenishment (wrong) | Redistribute + do not expedite | Prevents INR 45K unnecessary supply cost |
| SC-005 Data Anomaly | Expedite order (false positive) | FLAG only — no action | INR 85,000 false-positive cost avoided |
| **Total** | | | **~INR 181,000 net saving across 5 scenarios** |

---

## LangGraph Node Reference

| Node | Input State Fields | Output State Fields | Routing Trigger |
|------|--------------------|---------------------|-----------------|
| `detect_node` | demand_signals, inventory_positions | exceptions | Always first |
| `router_node` | exceptions.severity | → diagnose / summary / flag | CRITICAL/HIGH/MEDIUM → diagnose; LOW → summary; DATA_ANOMALY → flag |
| `diagnose_node` | exceptions, active_promotions, supplier_status, weather_events | root_cause_hypotheses | After detect for severity ≥ MEDIUM |
| `recommend_node` | root_cause_hypotheses, inventory_positions, what_if_results | recommendations | After diagnose |
| `critique_node` | recommendations, inventory_positions, sl_targets | critique_results | Always after recommend |
| `escalate_node` | recommendations, critique_results | approval_status | HITL required if cost > INR 100K or CRITICAL severity |
| `execute_node` | approval_status | execution_log | After HITL approval |
| `flag_node` | exceptions (data anomaly) | anomaly_flag | DATA_ANOMALY route only |
| `summary_node` | exceptions (low severity) | brief_summary | LOW severity route |

---

## HITL Threshold Rules (from service_level_targets.json)

| Cost Range | Action |
|-----------|--------|
| < INR 25,000 | Auto-approve (no human review) |
| INR 25,000–100,000 | Branch Manager approval |
| > INR 100,000 | SCM Director approval |
| New supplier activation | SCM Director regardless of cost |
| QA constraint | QA Director co-approval |
| Markdown decision | Finance + Category Manager |

---

## Demo Step ↔ Dataset Mapping

| Step | What to Show | Key Files |
|------|-------------|-----------|
| 1 | Executive question | `weekly_kpi_dashboard` equivalent — `inventory_snapshots` W07 filter |
| 2 | Threshold rule | Filter `inventory_snapshots` for `weeks_of_cover < 1.5` — show it fires but gives no root cause |
| 3 | LLM table summary | Raw `sku_store_week_demand.csv` + `inventory_snapshots.csv` pasted into prompt — show fragility |
| 4 | Tool calls | SC-002 trace: `demand_data_tool` → `inventory_lookup_tool` → `supplier_status_tool` → disambiguation |
| 5 | LangGraph routing | `state_schema.json` routing_logic + SC-005 data anomaly → flag_node path |
| 6 | Root-cause node | SC-003 `diagnose_node` compound signal warning; SC-002 supply vs demand disambiguation |
| 7 | Recommend node | SC-001 multi-action (auto-approve + HITL); SC-004 counter-intuitive non-action |
| 8 | Critique node | SC-003 QA constraint flag; SC-005 data quality FAIL route |
| 9 | HITL approval | SC-002 SCM Director approval; SC-003 HITL edit (1000→700 units) |
| 10 | Limitations | `supplier_delay_logs` — external signal noisy; `weather_event_signals` — compound signal caveats |
| 11 | Future scope | `state_schema.json` future_tools; monsoon onset event WE-005 for streaming alert |

---

## Demo Questions — By Stage

### Stage 1 — Command Centre Executive Question
> **Q1.** "Which SKUs are at risk of stockout next week and why?"

> **Q2.** "Give me a full exception summary for this week: stockouts, overstock, supplier delays, and demand anomalies."

> **Q3.** "What is the current weeks-of-cover for SKU-002 in East and Central regions, and is it normal?"

---

### Stage 2 — Threshold Rule Baseline (Show Limitation)
> **Q4.** "Apply a simple rule: flag any SKU-store with weeks-of-cover below 1.5. What does it return?"  
*(Expected: flags SKU-001 North, SKU-002 East, SKU-003 South — but gives no root cause. Cannot distinguish SC-002 supply failure from SC-001 promo spike.)*

> **Q5.** "Does the threshold rule flag SKU-008 in Week 16?"  
*(Expected: YES — 3x demand spike looks like stockout risk. This is a false positive the LangGraph system prevents.)*

---

### Stage 3 — LLM Table Reasoning (Show Fragility)
> **Q6.** [Feed `sku_store_week_demand.csv` + `inventory_snapshots.csv` raw] "What is the weeks-of-cover for SKU-002 at STR-004 and when will it stock out?"  
*(Expected: LLM may compute incorrectly from SOH ÷ demand; may not account for in-transit stock; no promo or supplier context)*

---

### Stage 4 — Tool Calls (Demo Step 4)
> **Q7.** "Why did SKU-002 demand appear to collapse in East and Central in Week 9?"  
*(Tool chain: `demand_data_tool` → normal demand confirmed → `inventory_lookup_tool` → critical low → `supplier_status_tool` → SUP-B shutdown. Root cause: SUPPLY FAILURE not demand crash)*

> **Q8.** "Why did SKU-001 demand spike 145% in North in Week 7?"  
*(Tool chain: `demand_data_tool` → spike confirmed → `promotion_calendar_tool` → PROMO-001 Holi active → uplift 25pp above forecast. Root cause: PROMOTION + INVENTORY MISS)*

> **Q9.** "What external signal is driving SKU-003 and SKU-010 demand in South in Week 11?"  
*(Tool chain: `weather_event_tool` → WE-001 heatwave; `promotion_calendar_tool` → PROMO-003 active. Compound signal — cannot deconvolve)*

---

### Stage 5 — LangGraph Routing (Demo Step 5)
> **Q10.** "Route the SKU-002 East exception: weeks-of-cover 0.4, CRITICAL severity. What path does the graph take?"  
*(Expected: detect_node → router_node → CRITICAL → diagnose_node → recommend_node → critique_node → escalate_node (HITL mandatory))*

> **Q11.** "Route the SKU-008 exception: 3x demand spike but inventory unchanged. What path does the graph take?"  
*(Expected: detect_node → router_node → diagnose_node → DATA_ANOMALY detected → flag_node → no action)*

> **Q12.** "What is the difference in routing between SC-001 (promo spike) and SC-002 (supplier failure)?"  
*(Expected: Both route CRITICAL; but diagnose_node produces different root cause → different recommendation type: transfer/expedite vs backup supplier/cross-region)*

---

### Stage 6 — Root-Cause Node (Demo Step 6)
> **Q13.** "Is the SKU-002 East inventory drop caused by a demand problem or a supply problem? Show your evidence."  
*(Expected: Supply — demand_data_tool confirms normal demand; supplier_status_tool confirms SUP-B 10-day shutdown. Confidence 0.97.)*

> **Q14.** "What are the ranked hypotheses for the SKU-003 South demand spike in Week 11? What is the confidence on each?"  
*(Expected: HEATWAVE 0.85, PROMO_003 0.74, COMPETITOR_PRICE_CUT 0.42. Compound signal caveat — MMM needed to deconvolve.)*

> **Q15.** "Is the SKU-004 West overstock a demand decline or a one-off event? How confident are you?"  
*(Expected: CORPORATE_ORDER_CANCELLATION confidence 0.99 — PROMO-004 cancelled. Demand is flat WoW.)*

---

### Stage 7 — Recommendation Node (Demo Step 7)
> **Q16.** "Generate recommendations for the SKU-001 North stockout risk. Include urgency, cost, and HITL flag for each."  
*(Expected: REC-001A: inter-store transfer INR 8,500 auto-approved; REC-001B: expedite 600u INR 42,000 HITL required)*

> **Q17.** "What should we do about the SKU-002 East stockout when no alternative supplier is available for SKU-005?"  
*(Expected: REC-002C: no full mitigation possible — honest escalation; estimate lost sales INR 216,000; customer advisory recommended)*

> **Q18.** "Should we expedite the incoming SUP-D batch for SKU-004 given the supplier delay?"  
*(Expected: NO — DO NOT EXPEDITE. The delay is beneficial given 4.8x overstock. This counter-intuitive recommendation is the key demo point for SC-004.)*

---

### Stage 8 — Critique Node (Demo Step 8)
> **Q19.** "Validate the SKU-003 expedite recommendation — are constraints met?"  
*(Expected: QA clearance for alternative bean grade required (constraint flagged). Weather forecast shows cooling — recommend 700u not 1,000u. PASS_WITH_FLAGS.)*

> **Q20.** "Validate the SKU-008 Week 16 action plan — should we proceed with expedite?"  
*(Expected: DATA_ANOMALY path — critique confirms no action is correct. Estimated false positive cost avoided: INR 85,000.)*

> **Q21.** "Validate the SKU-004 'do not expedite' recommendation. Is it well-evidenced?"  
*(Expected: PASS — overstock 4.8x cover confirmed; supplier delay is net positive; no SL risk from delay. Counter-intuitive finding validated.)*

---

### Stage 9 — HITL Approval Flow (Demo Step 9)
> **Q22.** "[SCM Director] Review the SKU-002 East recommendations: activate SUP-F (INR 62K) + West-East transfer (INR 38K). Approve, reject, or edit?"  
*(Expected: APPROVED — both within authorized actions. Additional: issue customer advisory on SKU-005 unavailability.)*

> **Q23.** "[SCM Director] The system recommends expediting 1,000 units SKU-003 at INR 124,000. Weather forecast shows cooling from Mar 17. What is your decision?"  
*(Expected: APPROVED WITH EDIT — reduce to 700 units. Cost revised to INR 87,000. QA clearance separately approved.)*

> **Q24.** "Show the audit trail for all HITL decisions made in the 16-week period. Who approved what and when?"  
*(Expected: SC-001 branch manager W07; SC-002 SCM Director W09; SC-003 SCM Director W11; SC-004 branch manager W14. All logged with cost, edits, timestamp.)*

---

### Stage 10 — Observability (Demo Step 9)
> **Q25.** "Show the agent trace for Scenario SC-002. How many tool calls, any failures, total cost and latency?"  
*(Expected: 12 tool calls, 1 failure (retry succeeded), $0.89 total cost, 16.8 seconds end-to-end)*

> **Q26.** "Compare cost and latency across all 5 scenarios. Which was most expensive and why?"  
*(Expected: SC-002 highest ($0.89) — most tool calls (12), supplier lookup + what-if simulations. SC-005 cheapest ($0.38) — data anomaly path exits early)*

> **Q27.** "If the `supplier_status_tool` had failed in SC-002, what would the system have diagnosed instead?"  
*(Expected: Without supplier data, diagnose_node would have returned DEMAND_COLLAPSE hypothesis — wrong root cause → wrong recommendation type. Tool reliability is critical.)*

---

### Stage 11 — Limitations & Future Scope
> **Q28.** "The system diagnosed a heatwave demand spike but couldn't deconvolve it from the promotion effect. What would fix this?"  
*(Expected: MMM integration — separate the promo coefficient from weather coefficient. Currently capped at compound signal confidence 0.85.)*

> **Q29.** "How would you set up a real-time alert for when 'NovaBrew complaint search index' or equivalent supply chain KPI breaches a threshold?"  
*(Expected: Real-time streaming from POS/WMS; alert threshold on weeks-of-cover < 1.5 for CRITICAL SKUs; Monsoon onset WE-005 in W22 would trigger pre-build alert for SKU-007)*

---

## Generation Notes

- Random seeds: 42 (Part 1), 99 (Part 2), 7 (Part 3), 13 (Part 4) — fully reproducible
- All 5 anomaly scenarios are deterministic — always appear in the seeded weeks
- `langgraph_scenario_traces.json` is hand-crafted gold-standard output — use for evaluation comparison
- Financial values (INR) are illustrative; HITL thresholds in `service_level_targets.json` are configurable
- SKU criticality (Dairy/Baby Care = CRITICAL) drives routing — Baby Care has 4hr stockout tolerance vs 72hr for Home Care

