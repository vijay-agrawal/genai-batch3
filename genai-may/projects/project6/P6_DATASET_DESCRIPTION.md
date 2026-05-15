# MCP-Powered Cross-Function Research Orchestration
## Synthetic Dataset Description & Demo Guide

**Project:** Project 6 — MCP-Powered Cross-Function Research Orchestration with Agent-to-Agent Collaboration  
**Dataset Version:** 1.0  
**Simulated Date:** April 18, 2025 (mid-fieldwork)  
**Domain:** Enterprise AI; Research & Consulting Operations; Cross-functional Workflow Automation

---

## Overview

This dataset simulates the full data environment for a research and consulting operations platform where three functional departments — Field/Collection, Analytics, and Client Servicing — each expose tools through MCP servers. The trigger event is a real client email (EMAIL-005) from GreenLeaf Foods VP Marketing requesting a status update while preparing a Board presentation. The dataset is designed to demonstrate every stage of the progressive MCP orchestration demo — from a monolithic agent that violates five policies simultaneously, through tool discovery, permission-enforced tool calls, A2A collaboration, PII masking, and a graceful MCP server failure fallback.

**The study context:** GreenLeaf Foods Brand Equity & Category U&A Study (PROJ-2025-GL-042), currently at 69% fieldwork completion with three data quality exceptions, two open risks, and a hard May 12 presentation deadline tied to a Board meeting.

---

## Dataset Inventory

| File | Format | Records | Description |
|------|--------|---------|-------------|
| `project_plans/project_master.json` | JSON | 1 | Project overview: client, team, dates, status, health |
| `project_plans/project_timeline.json` | JSON | 12 | Milestone tracker with planned/actual dates, risk flags |
| `project_plans/project_timeline.csv` | CSV | 12 | Same, tabular |
| `survey_collection_status/collection_by_segment_market.json` | JSON | 23 | Completion % by segment × market with status and notes |
| `survey_collection_status/collection_by_segment_market.csv` | CSV | 23 | Same, tabular |
| `survey_collection_status/collection_summary.json` | JSON | 1 | Aggregated field summary — tool-friendly single record |
| `survey_collection_status/daily_field_tracker.json` | JSON | 12 | Day-by-day cumulative completion trend (Apr 7–18) |
| `survey_collection_status/daily_field_tracker.csv` | CSV | 12 | Same, tabular |
| `data_quality_reports/dq_exceptions.json` | JSON | 3 | DQ exceptions with severity, action, disclosure text |
| `data_quality_reports/dq_exceptions.csv` | CSV | 3 | Same, tabular |
| `data_quality_reports/dq_summary.json` | JSON | 1 | Aggregated DQ health: rejection rate, open exceptions |
| `data_quality_reports/dq_by_market.json` | JSON | 6 | Per-market DQ scorecard |
| `data_quality_reports/dq_by_market.csv` | CSV | 6 | Same, tabular |
| `analysis_tables/brand_funnel_interim.json` | JSON | 5 | Interim brand funnel: awareness→NPS per brand, INTERIM labelled |
| `analysis_tables/brand_funnel_interim.csv` | CSV | 5 | Same, tabular |
| `analysis_tables/category_usage_interim.json` | JSON | 6 | Category usage by segment, INTERIM labelled |
| `analysis_tables/category_usage_interim.csv` | CSV | 6 | Same, tabular |
| `analysis_tables/brand_attribute_ratings_interim.json` | JSON | 7 | GreenLeaf vs NutriCrunch attribute ratings with significance |
| `analysis_tables/brand_attribute_ratings_interim.csv` | CSV | 7 | Same, tabular |
| `insight_summaries/insight_summaries.json` | JSON | 5 | Analyst-authored insights with confidence, cleared_for_client flag |
| `insight_summaries/insight_summaries.csv` | CSV | 5 | Same, tabular |
| `client_emails/client_email_thread.json` | JSON | 5 | Email thread: inbound/outbound/internal with action items |
| `client_emails/client_email_thread.csv` | CSV | 5 | Same, tabular |
| `deliverable_tracker/deliverable_tracker.json` | JSON | 10 | All deliverables with status, owner, risk, client approval |
| `deliverable_tracker/deliverable_tracker.csv` | CSV | 10 | Same, tabular |
| `role_permission_matrix/role_permission_matrix.json` | JSON | 5 | Roles: accessible tools, restrictions, PII rules, audit level |
| `role_permission_matrix/role_permission_matrix.csv` | CSV | 5 | Same, tabular |
| `mcp_server_schemas/tool_registry.json` | JSON | 1 | Full MCP tool registry: 19 tools across 3 servers with access lists |
| `mcp_server_schemas/mcp_health_status.json` | JSON | 3 | MCP server health: online/degraded, latency, stale data flags |
| `mcp_server_schemas/mcp_health_status.csv` | CSV | 3 | Same, tabular |
| `agent_outputs/risk_register.json` | JSON | 5 | Project risks with severity, mitigation, disclose_to_client flag |
| `agent_outputs/risk_register.csv` | CSV | 5 | Same, tabular |
| `agent_outputs/monolithic_agent_output.json` | JSON | 1 | Baseline monolithic agent output with 5 policy violations (Demo Step 2) |
| `agent_outputs/orchestrated_output.json` | JSON | 1 | Gold-standard orchestrated output with evidence table and blocked items |
| `audit_logs/audit_log.json` | JSON | 17 | Every tool call, handoff, block — with timestamps and reason codes |
| `audit_logs/audit_log.csv` | CSV | 17 | Same, tabular |
| `evaluation_set/mcp_eval_benchmark.json` | JSON | 12 | Evaluation cases mapped to each demo step |
| `evaluation_set/mcp_eval_benchmark.csv` | CSV | 12 | Same, tabular |

**Total: 38 files across 13 folders**

---

## The Five Embedded Demo Tensions

The dataset is built around five deliberate tensions that each demo step must resolve — these are what make the dataset rich for teaching:

### Tension 1 — Cleared vs Non-Cleared Insights (INS-004)
INS-004 is an analytically interesting finding (Youth segment sustainability driver as growth lever) but it is marked `cleared_for_client=False` because the Youth quota is only 71% filled. The **monolithic agent includes it** (policy violation). The **orchestrated system blocks it** at two levels: (1) `get_insight_summaries_all` is not in ROLE-CS tool list; (2) even `get_insight_summaries_cleared` filters it out. This is the most direct demonstration of access control with business consequence.

### Tension 2 — Stale Data from AnalyticsMCP
AnalyticsMCP is flagged as serving data last updated April 17 at 18:00 — approximately 50 new completes from April 18 morning are not yet reflected. The orchestrator must: (a) detect the stale data flag, (b) include the caveat in the output, and (c) not suppress the insights just because data is stale. The monolithic agent presents numbers without any freshness caveat.

### Tension 3 — ClientServicingMCP Degraded (Demo Step 9)
The email threading service within ClientServicingMCP is degraded (2,840ms latency — see `mcp_health_status.json`). The orchestrator must detect the degradation, use the cached email thread fallback, log the fallback in the audit trail, and note it as a caveat in the output. The deliverable tracker tool within the same MCP server is unaffected. This demonstrates graceful partial degradation.

### Tension 4 — PII in Multiple Potential Leak Points
Three PII exposure risks are embedded in the dataset:
- Analyst email addresses in client email bodies (should be masked in client-facing output)
- Internal email EMAIL-004 contains confidential escalation content (should be excluded for ROLE-CS)
- `get_pii_fields` tool exists in FieldMCP but has `accessible_to=[]` — blocked for every role

The monolithic agent leaks analyst emails. The orchestrated system catches all three.

### Tension 5 — Internal Email Exposure
EMAIL-004 is marked `internal_only=True` and contains a confidential escalation note about the Chennai CAPI situation. The `get_client_emails` tool in ClientServicingMCP has a `direction` and `internal_only` filter parameter. The orchestrator must pass `internal_only=False` for client-facing outputs. The monolithic agent, having hardcoded access to all emails, inadvertently includes internal content.

---

## MCP Server Architecture

### Three MCP Servers

**FieldMCP** (`http://field-mcp.c5i.internal:8001`) — ONLINE
- Exposes: collection summary, collection by segment, daily tracker, DQ exceptions, DQ summary, respondent status (anonymized), PII fields (blocked)
- Owns: all fieldwork and data quality data
- Health: ONLINE, real-time data (hourly updates)

**AnalyticsMCP** (`http://analytics-mcp.c5i.internal:8002`) — ONLINE (stale data)
- Exposes: brand funnel, attribute ratings, category usage, all insight summaries, cleared insight summaries only
- Owns: all analysis tables and insight outputs
- Health: ONLINE, batch updates at 18:00 IST daily — **data as of Apr 17**

**ClientServicingMCP** (`http://cs-mcp.c5i.internal:8003`) — DEGRADED (email service slow)
- Exposes: project summary, timeline, deliverable tracker, client emails, draft client update, risk register
- Owns: client communication and project governance data
- Health: DEGRADED — email threading service 2,840ms latency; deliverable tracker unaffected; fallback to cached email thread

### 19 Tools Total (across 3 servers)
See `mcp_server_schemas/tool_registry.json` for full schema including params, return types, access lists, PII flags.

---

## Role-Permission Matrix Summary

| Role | MCP Servers | Can See Non-Cleared Insights | Can See PII | Can Export Raw Data | Can Approve Client Comms |
|------|------------|------------------------------|-------------|---------------------|--------------------------|
| Client Servicing (ROLE-CS) | Field + CS | ❌ | ❌ | ❌ | ✅ |
| Analytics (ROLE-AN) | Field + Analytics | ✅ | ❌ | ✅ (anonymized) | ❌ |
| Field/Collection (ROLE-FD) | Field only | ❌ | ❌ | ❌ | ❌ |
| Project Manager (ROLE-PM) | All three | ✅ | ❌ | ❌ | ✅ |
| Orchestrator (ROLE-ORCH) | All three | Inherits from user | ❌ always | ❌ always | ❌ (drafts only) |

---

## Demo Step ↔ Dataset Mapping

| Step | What to Show | Key Files |
|------|-------------|-----------|
| 1 | Client request trigger | `client_emails/client_email_thread.json` EMAIL-005 |
| 2 | Monolithic agent failures | `agent_outputs/monolithic_agent_output.json` — 5 violations |
| 3 | MCP server discovery | `mcp_server_schemas/tool_registry.json` — server list and tool schemas |
| 4 | Tool registry + permission filter | `role_permission_matrix/role_permission_matrix.json` ROLE-CS row + tool_registry |
| 5 | Progressive tool calls | `audit_logs/audit_log.json` TC-001 through TC-008 |
| 6 | A2A collaboration | `agent_outputs/orchestrated_output.json` orchestrator_plan |
| 7 | Policy layer — PII + access | audit entries TC-009 (BLOCKED_PERMISSION) + TC-011 (BLOCKED_PII) |
| 8 | Audit trail | `audit_logs/audit_log.json` — all 17 entries |
| 9 | Failure scenario | `mcp_server_schemas/mcp_health_status.json` ClientServicingMCP DEGRADED + TC-008 FALLBACK |
| 10 | Limitations | Tool registry governance; security testing; schema evolution |
| 11 | Future scope | RBAC integration; production tool registry; workflow memory |

---

## Demo Questions — By Stage

### Stage 1 — The Business Trigger
> **Q1.** "Show me the email that triggered this request."  
*(Expected: EMAIL-005 — Priya Mehta requesting field progress, DQ issues, early insights, and timeline risks by end of week)*

> **Q2.** "What is the current project health and why is it AMBER?"  
*(Expected: project_master.json — 3 DQ exceptions, Chennai CAPI behind, SEC B quota gap)*

---

### Stage 2 — Monolithic Agent (Show the Failures)
> **Q3.** "Use a monolithic single agent to draft the client update."  
*(Expected: monolithic_agent_output.json — 5 violations: INS-004, analyst PII, internal email, no interim caveat, no source trace)*

> **Q4.** "How many policy violations did the monolithic agent commit? What are they?"  
*(Expected: 5 — see problems_count and output_problems in monolithic_agent_output.json)*

> **Q5.** "If I want to add a 'get_risk_register' tool to the monolithic agent, what does that require?"  
*(Expected: Code change + redeployment + manual access control update — no tool discovery, no registry)*

---

### Stage 3 — MCP Server Discovery
> **Q6.** "Which MCP servers are available for this project?"  
*(Expected: FieldMCP (ONLINE), AnalyticsMCP (ONLINE, stale), ClientServicingMCP (DEGRADED) — from mcp_health_status.json)*

> **Q7.** "What tools does FieldMCP expose and who can access each one?"  
*(Expected: 7 tools — get_collection_summary, get_collection_by_segment, get_daily_tracker, get_dq_exceptions_detail, get_dq_summary, get_respondent_status_anonymized, get_pii_fields (blocked for all))*

> **Q8.** "If I register a new tool in the tool registry without changing application code, will the orchestrator discover and use it?"  
*(Expected: YES — demonstrate by adding a mock tool to tool_registry.json; orchestrator polls registry at runtime)*

---

### Stage 4 — Tool Registry + Permission Filtering
> **Q9.** "Which tools are available for this user (ROLE-CS Client Servicing)? Which are restricted?"  
*(Expected: 8 accessible tools. Restricted: get_pii_fields, get_analysis_tables_raw, get_insight_summaries_all, get_raw_respondent_data)*

> **Q10.** "What happens if a ROLE-CS orchestrator tries to call get_insight_summaries_all?"  
*(Expected: BLOCKED_PERMISSION — not in ROLE-CS tool access list. Logged in audit trail as AUD00009)*

> **Q11.** "Which tools require HITL or co-approval before the output can be sent to the client?"  
*(Expected: draft_client_update output must be approved by ROLE-CS or ROLE-PM with can_approve_client_communication=True)*

---

### Stage 5 — Progressive Tool Execution (Demo Step 5)
> **Q12.** "What is the latest field completion by segment and geography?"  
*(Tool: FieldMCP:get_collection_by_segment → 23 records. Chennai CAPI 56% AT_RISK; SEC B Bengaluru 78% BEHIND)*

> **Q13.** "Are there any data-quality issues to disclose? Show me the client-safe disclosure text for each."  
*(Tool: FieldMCP:get_dq_exceptions_detail → 3 exceptions. Each has pre-approved disclosure_language field — orchestrator retrieves it, does not generate it)*

> **Q14.** "What early insights can be shared? And is the analytics data fresh?"  
*(Tool: AnalyticsMCP:get_insight_summaries_cleared → 3 insights. Server returns stale_data_note: 'Data as of Apr 17 18:00'. INS-004 absent from response.)*

> **Q15.** "What timeline risks should the client be warned about?"  
*(Tools: ClientServicingMCP:get_timeline_status → MS-07 AT_RISK; get_risk_register → RISK-01, RISK-02, RISK-05)*

---

### Stage 6 — A2A Collaboration (Demo Step 6)
> **Q16.** "Walk me through the agent handoff sequence for this request."  
*(Expected: audit_log.json agent handoff entries — Orchestrator→FieldAgent→Orchestrator→AnalyticsAgent→Orchestrator→CSAgent→Orchestrator. Each handoff logged with message summary.)*

> **Q17.** "What did the Analytics Agent contribute that the Field Agent could not?"  
*(Expected: Cleared insights with confidence labels. Field Agent has no access to AnalyticsMCP — tool not in ROLE-FD access list.)*

> **Q18.** "What did the Client Servicing Agent do that the Analytics Agent could not?"  
*(Expected: Drafted client communication. AnalyticsAgent has can_approve_client_communication=False and no access to draft_client_update tool.)*

---

### Stage 7 — Policy Layer (Demo Step 7)
> **Q19.** "[PII TEST] Try to retrieve respondent contact details for quality audit purposes."  
*(Expected: BLOCKED_PII — get_pii_fields accessible_to=[] — blocked regardless of role. Audit entry logged.)*

> **Q20.** "[ACCESS TEST] Try to retrieve the non-cleared Youth segment insight (INS-004) as a Client Servicing user."  
*(Expected: Two-layer block: (1) get_insight_summaries_all not in ROLE-CS list; (2) even via cleared tool, INS-004 filtered at data level.)*

> **Q21.** "How does the system ensure that internal emails (EMAIL-004) are not included in client-facing outputs?"  
*(Expected: get_client_emails tool has internal_only filter parameter. CSAgent passes internal_only=False. EMAIL-004 excluded from response.)*

> **Q22.** "Where would analyst email addresses appear in the raw data, and how are they masked?"  
*(Expected: client_email_thread.json 'from' and 'to' fields contain email addresses. PII masking layer in orchestrated_output.json removes them before inclusion in draft.)*

---

### Stage 8 — Audit Trail (Demo Step 8)
> **Q23.** "Show the audit trail for every tool call made in this request."  
*(Expected: audit_log.json — 11 tool call entries: 9 SUCCESS, 1 FALLBACK, 1 BLOCKED_PERMISSION, 1 BLOCKED_PII)*

> **Q24.** "Trace the claim 'Chennai CAPI at 56% completion' back to its source."  
*(Expected: evidence_table in orchestrated_output.json — claim 'Chennai CAPI at 56%' → source: FieldMCP:get_collection_by_segment → tool_call_id: TC-002 → audit entry AUD00002)*

> **Q25.** "Which claims in the client update draft are sourced from interim data? How are they caveated?"  
*(Expected: All three insight claims sourced from AnalyticsMCP with data_caveat: 'Based on Apr 17 data'. Interim label explicit in insight summaries.)*

---

### Stage 9 — Failure Scenario (Demo Step 9)
> **Q26.** "AnalyticsMCP is now offline. What does the orchestrator do?"  
*(Expected: EV-011 — timeout detected, failure logged to audit, proceeds with Field and CS data only, explicit caveat: 'Insights section deferred — AnalyticsMCP offline', no hallucination)*

> **Q27.** "ClientServicingMCP is degraded — the email service is slow. How is this handled?"  
*(Expected: mcp_health_status.json — DEGRADED with fallback note. TC-008 in audit log: status=FALLBACK, fallback_source='Cached email thread Apr 17'. Caveat included in final output.)*

> **Q28.** "Is it better to return a partial answer with caveats or wait for full data when a server is unavailable?"  
*(Expected: Policy decision — orchestrated_output.json system_caveats field. Partial answer with explicit caveats is preferred over either waiting or hallucinating.)*

---

### Stage 10 — Limitations
> **Q29.** "What happens if an MCP tool schema changes without the orchestrator being notified?"  
*(Expected: Tool registry governance gap — schema versioning, breaking change notifications, and contract testing are essential. tool_registry.json has registry_version field — highlight need for versioning.)*

> **Q30.** "Could a malicious tool in the registry return false data that the orchestrator would include in a client brief?"  
*(Expected: Yes — tool authentication and output validation are required. Current demo shows permission enforcement but not output integrity checking. Security testing essential before production.)*

---

### Stage 11 — Future Scope
> **Q31.** "How would enterprise SSO and RBAC integrate with this MCP permission model?"  
*(Expected: User role would be injected from SSO token rather than hardcoded — orchestrator passes JWT role claim in every tool call header; MCP servers validate against RBAC policy.)*

> **Q32.** "How would you add workflow memory so the orchestrator remembers last week's status update when drafting this week's?"  
*(Expected: Persistent conversation memory keyed by project_id + user_role. Last draft stored and injected as context for weekly recurrence. email_thread.json already provides precedent.)*

---

## Generation Notes

- Random seeds: 42 (Part 1), 99 (Part 2), 7 (Part 3), 13 (Part 4), 17 (Part 5) — fully reproducible
- Simulated date is April 18, 2025 — all "as_of_date" fields consistent with mid-fieldwork state
- `orchestrated_output.json` is hand-crafted gold standard — use for evaluation comparison and as the demo "reveal"
- `monolithic_agent_output.json` is deliberately bad — the 5 violations are intentional and annotated
- All `contains_respondent_pii=False` in DQ and collection data — PII exposure is structural (email addresses in thread, get_pii_fields tool) not in records
- INS-004 is the most important data asset — it is analytically valid but operationally blocked. Its absence from client output is the cleanest access control demonstration in the dataset.
- ClientServicingMCP degraded state (`mcp_health_status.json`) is pre-set — use for Demo Step 9 without needing to simulate a live failure

