# Project 6 — Solution Architecture Guide
## MCP-Powered Cross-Function Research Orchestration with Agent-to-Agent Collaboration

**Two Reference Implementations: CrewAI and LangGraph**  
**Version:** 1.0 | **Project:** PROJ-2025-GL-042 (GreenLeaf Foods Brand Equity Study)

---

## 1. The Problem This Architecture Solves

A client-servicing user asks: *"Prepare a status update for GreenLeaf Foods — field progress, data quality issues, early insights, and timeline risks."*

This is deceptively simple. Answering it correctly requires:

- Fetching live data from three different functional systems (Field, Analytics, Client Servicing)
- Enforcing role-based access (the user cannot see non-cleared insights or raw respondent data)
- Masking PII before it reaches any agent context
- Detecting stale data from one source and caveating it
- Falling back gracefully when one MCP server is degraded
- Producing a fully audit-traced, client-safe output

A monolithic LLM with hardcoded functions fails all six. The architectures below succeed because they separate **tool ownership** (MCP), **specialised reasoning** (A2A agents/nodes), and **governance** (policy layer + audit) into distinct, composable layers.

---

## 2. Conceptual Architecture (Implementation-Agnostic)

```
┌──────────────────────────────────────────────────────────────────────┐
│  USER REQUEST                                                         │
│  "Prepare status update: field progress, DQ, insights, risks"        │
│  Role: ROLE-CS (Client Servicing)                                    │
└─────────────────────────┬────────────────────────────────────────────┘
                           │
┌─────────────────────────▼────────────────────────────────────────────┐
│  ORCHESTRATION LAYER                                                  │
│  • Receives user request + role context                               │
│  • Discovers available tools from MCP registries                     │
│  • Filters tool list by ROLE-CS permissions                          │
│  • Plans task decomposition across specialist agents                 │
│  • Enforces PII masking + access policy on all agent outputs         │
│  • Aggregates evidence, applies caveats, triggers HITL if needed     │
└──────┬──────────────────┬──────────────────────┬─────────────────────┘
       │                  │                      │
┌──────▼──────┐   ┌───────▼───────┐   ┌──────────▼──────────┐
│ FIELD AGENT │   │ANALYTICS AGENT│   │  CS AGENT           │
│             │   │               │   │                     │
│ Scope:      │   │ Scope:        │   │ Scope:              │
│ Collection  │   │ Analysis      │   │ Client comm,        │
│ progress,   │   │ tables,       │   │ deliverables,       │
│ DQ flags,   │   │ insights      │   │ timeline,           │
│ field ops   │   │ (cleared      │   │ risks, draft        │
│             │   │  only for CS) │   │ client update       │
└──────┬──────┘   └───────┬───────┘   └──────────┬──────────┘
       │                  │                      │
┌──────▼──────┐   ┌───────▼───────┐   ┌──────────▼──────────┐
│  FieldMCP   │   │ AnalyticsMCP  │   │ ClientServicingMCP  │
│  :8001      │   │ :8002         │   │ :8003               │
│  ONLINE     │   │ ONLINE        │   │ DEGRADED            │
│  Real-time  │   │ (stale Apr17) │   │ (email slow,        │
│             │   │               │   │  fallback active)   │
└──────┬──────┘   └───────┬───────┘   └──────────┬──────────┘
       │                  │                      │
┌──────▼──────────────────▼──────────────────────▼──────────┐
│  DATA SOURCES                                              │
│  survey_collection_status | analysis_tables | project_plans│
│  data_quality_reports | insight_summaries | client_emails  │
│  deliverable_tracker | role_permission_matrix              │
└────────────────────────────────────────────────────────────┘
       │                  │                      │
┌──────▼──────────────────▼──────────────────────▼──────────┐
│  GOVERNANCE LAYER (cross-cutting)                          │
│  • PII masking applied before any agent sees response      │
│  • Role-permission check on every tool call                │
│  • cleared_for_client filter on all insight retrieval      │
│  • internal_only filter on email retrieval                 │
│  • Stale data detection + caveat injection                 │
│  • Full audit log: tool call, agent handoff, block, cost   │
└────────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────┐
│  OUTPUT LAYER                                               │
│  • Client-ready status update email draft                  │
│  • Evidence table (claim → tool call → source)             │
│  • Blocked items log (what was withheld and why)           │
│  • System caveats (stale data, degraded server)            │
│  • Full audit trail                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation A — CrewAI

### 3.1 Why CrewAI for This Use Case

CrewAI's **role-based crew model** maps naturally onto the three functional departments in this architecture. Each department becomes a `Crew` with a `Manager Agent` and specialised `Agents`. The crew structure enforces a natural delegation pattern — the orchestrating crew decides which functional crew to call, and each crew operates within its own tool scope.

CrewAI's `Process.hierarchical` mode gives the orchestrator manager-level control over task delegation without each sub-agent needing to know about the others.

---

### 3.2 Agent Definitions

#### Orchestrator Crew

```python
# crew_orchestrator.py

from crewai import Agent, Task, Crew, Process
from crewai_tools import MCPServerTool

# Tool discovery: load tools from MCP registries filtered by user role
field_tools     = MCPServerTool(server_url="http://field-mcp.c5i.internal:8001",
                                 role="ROLE-CS")
analytics_tools = MCPServerTool(server_url="http://analytics-mcp.c5i.internal:8002",
                                 role="ROLE-CS")
cs_tools        = MCPServerTool(server_url="http://cs-mcp.c5i.internal:8003",
                                 role="ROLE-CS")

orchestrator = Agent(
    role="Research Orchestrator",
    goal="""Coordinate Field, Analytics, and Client Servicing agents to answer
            a client research status request. Enforce role-based access, apply
            PII masking, detect data quality issues, and produce a cited,
            client-safe output.""",
    backstory="""You are the lead research coordinator at c5i. You receive client
                 requests and direct specialised functional agents to gather
                 evidence. You never guess — you only include information
                 retrieved from tools, properly caveated.""",
    tools=[field_tools, analytics_tools, cs_tools],
    allow_delegation=True,
    verbose=True,
)
```

#### Field Agent

```python
field_agent = Agent(
    role="Field & Collection Specialist",
    goal="""Retrieve accurate fieldwork completion data, sample gap analysis,
            and data quality exception summaries for a given project.
            Return only structured, PII-free data.""",
    backstory="""You manage fieldwork operations at c5i. You have access to
                 real-time collection dashboards and the data quality exception
                 log. You never fabricate completion numbers.""",
    tools=[
        # Discovered from FieldMCP for ROLE-CS:
        MCPTool("get_collection_summary"),
        MCPTool("get_collection_by_segment"),
        MCPTool("get_dq_summary"),
        MCPTool("get_dq_exceptions_detail"),
        # Blocked by MCP: get_pii_fields (accessible_to=[])
    ],
    allow_delegation=False,
)
```

#### Analytics Agent

```python
analytics_agent = Agent(
    role="Analytics & Insights Specialist",
    goal="""Retrieve early analysis outputs and insight summaries that have been
            cleared for client sharing. Flag interim data status, confidence
            levels, and stale data from the analytics system.""",
    backstory="""You are a senior analyst at c5i. You work with partial and
                 final datasets. You always label interim findings clearly and
                 never share insights marked cleared_for_client=False with
                 client-facing agents.""",
    tools=[
        MCPTool("get_insight_summaries_cleared"),  # cleared only for ROLE-CS
        MCPTool("get_brand_funnel"),
        MCPTool("get_attribute_ratings"),
        MCPTool("get_category_usage"),
        # Blocked: get_insight_summaries_all (not in ROLE-CS list)
        # Blocked: get_analysis_tables_raw (Analytics/PM only)
    ],
    allow_delegation=False,
)
```

#### Client Servicing Agent

```python
cs_agent = Agent(
    role="Client Servicing Specialist",
    goal="""Retrieve project timeline, risk register, and client email context.
            Draft a client-ready status update using only approved inputs from
            the Field and Analytics agents. Apply final PII masking and
            internal-email exclusion before output.""",
    backstory="""You are the account manager at c5i responsible for client
                 communications on PROJ-2025-GL-042. You craft professional,
                 evidence-backed updates that are truthful about risks and
                 careful about what is shared before full analysis is complete.""",
    tools=[
        MCPTool("get_project_summary"),
        MCPTool("get_timeline_status"),
        MCPTool("get_deliverable_tracker"),
        MCPTool("get_client_emails"),       # with internal_only=False filter
        MCPTool("get_risk_register"),
        MCPTool("draft_client_update"),
    ],
    allow_delegation=False,
)
```

---

### 3.3 Task Definitions

```python
# Tasks wire agents to specific retrieval and synthesis responsibilities

task_field = Task(
    description="""
    For project PROJ-2025-GL-042 (as of April 18, 2025):
    1. Retrieve overall field completion summary.
    2. Break down completion by segment and market — flag any AT_RISK or BEHIND cells.
    3. Retrieve all DQ exceptions — return the pre-approved disclosure_language for each.
    4. Return a structured field evidence package: completion %, at-risk markets,
       DQ exception count, and approved disclosure text for each exception.
    DO NOT include respondent-level data or any PII fields.
    """,
    expected_output="Structured field evidence package: completion stats, segment gaps, DQ disclosure texts.",
    agent=field_agent,
    output_key="field_evidence",
)

task_analytics = Task(
    description="""
    For project PROJ-2025-GL-042:
    1. Retrieve ONLY insights with cleared_for_client=True.
    2. For each insight, include: title, finding, confidence label, data_status,
       caveat, and the specific data source it is based on.
    3. Check AnalyticsMCP for stale data flag — include in output if present.
    4. DO NOT retrieve or relay insights with cleared_for_client=False.
    5. DO NOT fabricate or extend findings beyond what the tool returns.
    """,
    expected_output="List of cleared insights with confidence labels and stale data caveat if applicable.",
    agent=analytics_agent,
    output_key="analytics_evidence",
    context=[task_field],  # has context of field situation
)

task_cs = Task(
    description="""
    For project PROJ-2025-GL-042:
    1. Retrieve project timeline — identify any milestones marked AT_RISK.
    2. Retrieve risk register — include only risks with disclose_to_client=True.
    3. Retrieve client email thread — EXCLUDE internal_only=True emails.
    4. Using the field_evidence and analytics_evidence from prior agents, call
       draft_client_update with:
       - field_summary from field_evidence
       - dq_summary from field_evidence (using approved disclosure_language only)
       - insights from analytics_evidence (cleared only)
       - risks from risk register (disclose_to_client=True only)
    5. Apply PII masking: remove analyst email addresses from draft.
    6. Return: draft email, evidence table (claim → source), blocked items log.
    """,
    expected_output="Client-ready status update draft, evidence table, blocked items log, system caveats.",
    agent=cs_agent,
    output_key="client_update_draft",
    context=[task_field, task_analytics],
)
```

---

### 3.4 Crew Assembly and Execution

```python
research_status_crew = Crew(
    agents=[orchestrator, field_agent, analytics_agent, cs_agent],
    tasks=[task_field, task_analytics, task_cs],
    process=Process.hierarchical,
    manager_agent=orchestrator,
    memory=True,                    # cross-task context
    verbose=True,
    output_log_file="audit_logs/crewai_run_log.txt",
)

# Execution
result = research_status_crew.kickoff(inputs={
    "project_id": "PROJ-2025-GL-042",
    "requesting_user_role": "ROLE-CS",
    "requesting_user": "Ananya Sharma",
    "client": "GreenLeaf Foods",
    "request_date": "2025-04-18",
})
```

---

### 3.5 MCP Integration in CrewAI

```python
# FastMCP server definition (Field domain)
# field_mcp_server.py

from fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("FieldMCP")

class CollectionSummaryParams(BaseModel):
    project_id: str

@mcp.tool()
def get_collection_summary(params: CollectionSummaryParams) -> dict:
    """
    Returns overall fieldwork completion stats, health status, and biggest risk.
    PII: None. Accessible to: ROLE-CS, ROLE-AN, ROLE-FD, ROLE-PM, ROLE-ORCH.
    """
    # Fetches from survey_collection_status/collection_summary.json
    return load_collection_summary(params.project_id)

@mcp.tool()
def get_pii_fields(project_id: str, respondent_id: str) -> dict:
    """
    Returns respondent PII: name, email, phone. RESTRICTED — no role has access.
    """
    raise PermissionError("PII export blocked. Requires Data Protection Officer approval.")

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8001)
```

```python
# CrewAI agent connects to MCP server via tool wrapper
from crewai_tools import MCPServerTool

field_tools = MCPServerTool(
    server_url="http://field-mcp.c5i.internal:8001",
    headers={"X-User-Role": "ROLE-CS", "X-Request-ID": "REQ-2025-04-18-CS-042"},
    timeout=5.0,
    fallback_on_timeout=True,
)
# Agent receives dynamically discovered tool list filtered by server-side role check
```

---

### 3.6 CrewAI Data Flow Diagram

```
User Request (ROLE-CS)
        │
        ▼
  Orchestrator Agent
  (Process.hierarchical)
        │
        ├──── Delegates ──► Field Agent
        │                       │
        │                  [get_collection_summary → FieldMCP]
        │                  [get_collection_by_segment → FieldMCP]
        │                  [get_dq_exceptions_detail → FieldMCP]
        │                       │
        │                  field_evidence package
        │                       │
        ├──── Delegates ──► Analytics Agent
        │     (has field_evidence context)
        │                       │
        │                  [get_insight_summaries_cleared → AnalyticsMCP]
        │                  ← stale data caveat returned
        │                  INS-004 filtered out (cleared_for_client=False)
        │                       │
        │                  analytics_evidence package
        │                       │
        └──── Delegates ──► CS Agent
              (has field + analytics context)
                               │
                         [get_timeline_status → ClientServicingMCP]
                         [get_risk_register → ClientServicingMCP]
                         [get_client_emails(internal_only=False) → CS MCP]
                         [draft_client_update → ClientServicingMCP]
                               │
                         Draft + Evidence Table + Blocked Items
                               │
                        ◄──────┘
                   Orchestrator applies:
                   • Final PII scan (analyst emails removed)
                   • System caveats appended
                   • Audit log written
                               │
                        Client-Ready Output
```

---

## 4. Implementation B — LangGraph

### 4.1 Why LangGraph for This Use Case

LangGraph's **state graph model** is ideal for this architecture because the research status request has conditional paths: the orchestrator's plan changes based on which MCP servers are available, whether DQ exceptions are severe enough to require different framing, and whether any insights failed the cleared_for_client check. LangGraph's explicit routing, typed state, and conditional edges make these branching decisions traceable and testable.

Unlike CrewAI's delegation model, LangGraph treats each processing step as a node with well-defined state transitions — making it well-suited for audit-critical workflows where every decision point must be logged.

---

### 4.2 State Schema

```python
# state.py
from typing import TypedDict, Optional, List, Annotated
from operator import add

class ResearchStatusState(TypedDict):
    # Request context
    project_id: str
    requesting_user_role: str
    requesting_user: str
    request_timestamp: str

    # Tool discovery
    available_tools: List[dict]           # filtered by role from registry
    mcp_server_health: dict               # ONLINE / DEGRADED / OFFLINE per server

    # Field agent outputs
    field_completion_summary: Optional[dict]
    collection_by_segment: Optional[List[dict]]
    dq_exceptions: Optional[List[dict]]
    dq_summary: Optional[dict]
    field_evidence_package: Optional[dict]

    # Analytics agent outputs
    cleared_insights: Optional[List[dict]]
    analytics_stale_data_flag: bool
    analytics_stale_data_note: Optional[str]
    analytics_offline: bool               # True if AnalyticsMCP unavailable

    # CS agent outputs
    timeline_milestones: Optional[List[dict]]
    risk_register: Optional[List[dict]]
    client_email_context: Optional[dict]
    client_update_draft: Optional[str]

    # Governance
    pii_masked_fields: Annotated[List[str], add]     # accumulates across nodes
    blocked_tool_calls: Annotated[List[dict], add]   # accumulates across nodes
    access_violations_attempted: Annotated[List[dict], add]

    # Output
    evidence_table: Optional[List[dict]]
    system_caveats: Annotated[List[str], add]
    audit_log: Annotated[List[dict], add]
    final_output: Optional[dict]
```

---

### 4.3 Node Definitions

```
┌─────────────────────────────────────────────────────┐
│               LANGGRAPH NODE MAP                    │
│                                                     │
│  [START]                                            │
│     │                                               │
│     ▼                                               │
│  [tool_discovery_node]                              │
│  Query MCP registries → filter by ROLE-CS           │
│     │                                               │
│     ▼                                               │
│  [health_check_node]                                │
│  Ping all 3 MCP servers → record status             │
│     │                                               │
│     ├─ All healthy ──────────────────┐              │
│     └─ Degraded/Offline ─► [fallback_router_node]  │
│                                      │              │
│                              ┌───────▼──────┐       │
│                              │[field_node]  │       │
│                              │              │       │
│                   ┌──────────┴──────────────┘       │
│                   │                                 │
│                   ▼                                 │
│         [dq_check_node]                             │
│         Parse DQ exceptions                         │
│         Extract approved disclosure text            │
│                   │                                 │
│                   ▼                                 │
│         [analytics_node]                            │
│         Call AnalyticsMCP (cleared only)            │
│         Detect stale flag                           │
│                   │                                 │
│      ┌────────────┴────────────────┐                │
│      │                            │                 │
│      ▼                            ▼                 │
│  [insights_ok]           [analytics_offline]        │
│      │                            │                 │
│      │                   [insights_deferred_node]   │
│      │                   Add system caveat          │
│      └──────────┬─────────────────┘                 │
│                 │                                   │
│                 ▼                                   │
│       [timeline_risk_node]                          │
│       Timeline + risk register                      │
│                 │                                   │
│                 ▼                                   │
│       [email_context_node]                          │
│       Client emails (internal_only=False)           │
│       Fallback if CS MCP degraded                   │
│                 │                                   │
│                 ▼                                   │
│       [draft_node]                                  │
│       Assemble approved inputs                      │
│       Call draft_client_update                      │
│                 │                                   │
│                 ▼                                   │
│       [pii_masking_node]                            │
│       Scan draft for PII patterns                   │
│       Mask: analyst emails, respondent refs         │
│                 │                                   │
│                 ▼                                   │
│       [evidence_assembly_node]                      │
│       Build evidence table                          │
│       Log blocked items                             │
│                 │                                   │
│                 ▼                                   │
│       [audit_finalise_node]                         │
│       Write complete audit trail                    │
│                 │                                   │
│               [END]                                 │
└─────────────────────────────────────────────────────┘
```

---

### 4.4 Node Implementations

```python
# nodes.py
from langgraph.graph import StateGraph, END
from typing import Literal

# ── Tool Discovery Node ────────────────────────────────────────────────────
def tool_discovery_node(state: ResearchStatusState) -> ResearchStatusState:
    """
    Queries all three MCP tool registries and filters available tools
    by the requesting user's role. Writes filtered tool list to state.
    """
    role = state["requesting_user_role"]
    registry = load_tool_registry()   # mcp_server_schemas/tool_registry.json

    available = [
        tool for server in registry["mcp_servers"].values()
        for tool in server["tools"]
        if role in tool["accessible_to"]
    ]
    blocked = [
        {"tool": tool["tool_name"], "server": server_name,
         "reason": tool.get("blocked_reason","Insufficient permissions")}
        for server_name, server in registry["mcp_servers"].items()
        for tool in server["tools"]
        if role not in tool["accessible_to"]
    ]
    return {
        **state,
        "available_tools": available,
        "blocked_tool_calls": blocked,
        "audit_log": [audit_entry("tool_discovery_node", "tool_registry_lookup", "SUCCESS")],
    }

# ── MCP Health Check Node ─────────────────────────────────────────────────
def health_check_node(state: ResearchStatusState) -> ResearchStatusState:
    """
    Pings all three MCP servers. Records health status.
    DEGRADED servers trigger fallback routing.
    """
    health = {}
    caveats = []
    for server_name, server in load_tool_registry()["mcp_servers"].items():
        status = ping_mcp_server(server["base_url"])   # returns ONLINE/DEGRADED/OFFLINE
        health[server_name] = status
        if status == "DEGRADED":
            caveats.append(f"{server_name} is degraded — fallback mode active")
        elif status == "OFFLINE":
            caveats.append(f"{server_name} is offline — outputs from this server unavailable")
    return {**state, "mcp_server_health": health, "system_caveats": caveats}

# ── Fallback Router (conditional edge) ────────────────────────────────────
def route_after_health_check(state: ResearchStatusState) -> Literal["field_node","fallback_router_node"]:
    health = state["mcp_server_health"]
    if health.get("AnalyticsMCP") == "OFFLINE":
        return "fallback_router_node"
    return "field_node"

# ── Field Node ────────────────────────────────────────────────────────────
def field_node(state: ResearchStatusState) -> ResearchStatusState:
    """
    Calls FieldMCP tools: get_collection_summary, get_collection_by_segment,
    get_dq_summary, get_dq_exceptions_detail.
    Role check: ROLE-CS has access to all four. get_pii_fields blocked at MCP level.
    """
    project_id = state["project_id"]

    collection_summary = call_mcp_tool(
        "FieldMCP", "get_collection_summary",
        params={"project_id": project_id},
        role=state["requesting_user_role"],
    )
    collection_by_segment = call_mcp_tool(
        "FieldMCP", "get_collection_by_segment",
        params={"project_id": project_id},
        role=state["requesting_user_role"],
    )
    dq_summary = call_mcp_tool("FieldMCP","get_dq_summary",{"project_id":project_id},state["requesting_user_role"])
    dq_exceptions = call_mcp_tool("FieldMCP","get_dq_exceptions_detail",{"project_id":project_id},state["requesting_user_role"])

    return {
        **state,
        "field_completion_summary": collection_summary,
        "collection_by_segment": collection_by_segment,
        "dq_summary": dq_summary,
        "dq_exceptions": dq_exceptions,
        "audit_log": [
            audit_entry("field_node","get_collection_summary","SUCCESS"),
            audit_entry("field_node","get_collection_by_segment","SUCCESS"),
            audit_entry("field_node","get_dq_summary","SUCCESS"),
            audit_entry("field_node","get_dq_exceptions_detail","SUCCESS"),
        ],
    }

# ── Analytics Node ────────────────────────────────────────────────────────
def analytics_node(state: ResearchStatusState) -> ResearchStatusState:
    """
    Calls AnalyticsMCP:get_insight_summaries_cleared.
    ROLE-CS cannot call get_insight_summaries_all — blocked at MCP level.
    INS-004 (cleared_for_client=False) is filtered at data level inside the tool.
    Detects stale data flag and injects caveat.
    """
    insights_response = call_mcp_tool(
        "AnalyticsMCP", "get_insight_summaries_cleared",
        params={"project_id": state["project_id"]},
        role=state["requesting_user_role"],
    )
    stale_flag   = insights_response.get("stale_data_flag", False)
    stale_note   = insights_response.get("stale_data_note", "")
    cleared_insights = insights_response.get("insights", [])

    caveats = []
    if stale_flag:
        caveats.append(f"AnalyticsMCP data caveat: {stale_note}")

    return {
        **state,
        "cleared_insights": cleared_insights,
        "analytics_stale_data_flag": stale_flag,
        "analytics_stale_data_note": stale_note,
        "analytics_offline": False,
        "system_caveats": caveats,
        "audit_log": [audit_entry("analytics_node","get_insight_summaries_cleared",
                                   "SUCCESS_WITH_CAVEAT" if stale_flag else "SUCCESS")],
    }

# ── Analytics Offline Fallback Node ───────────────────────────────────────
def insights_deferred_node(state: ResearchStatusState) -> ResearchStatusState:
    """
    Called when AnalyticsMCP is offline. Sets analytics_offline=True.
    Injects explicit caveat. Does NOT hallucinate insight data.
    """
    return {
        **state,
        "cleared_insights": [],
        "analytics_offline": True,
        "system_caveats": [
            "AnalyticsMCP offline — early insights unavailable. "
            "Field progress and timeline sections confirmed. "
            "Insights section will be provided once analytics service is restored."
        ],
        "audit_log": [audit_entry("insights_deferred_node","get_insight_summaries_cleared","OFFLINE_SKIP")],
    }

# ── Draft Node ────────────────────────────────────────────────────────────
def draft_node(state: ResearchStatusState) -> ResearchStatusState:
    """
    Assembles approved inputs and calls ClientServicingMCP:draft_client_update.
    Enforces: cleared insights only, approved DQ disclosure text only,
    disclose_to_client=True risks only.
    """
    approved_insights = [i for i in (state["cleared_insights"] or [])
                         if i.get("cleared_for_client")]
    approved_dq       = [e["disclosure_language"] for e in (state["dq_exceptions"] or [])
                         if e.get("disclose_to_client")]
    approved_risks    = [r for r in (state["risk_register"] or [])
                         if r.get("disclose_to_client")]

    draft_response = call_mcp_tool(
        "ClientServicingMCP", "draft_client_update",
        params={
            "project_id":     state["project_id"],
            "field_summary":  state["field_completion_summary"],
            "dq_summary":     approved_dq,
            "insights":       approved_insights,
            "risks":          approved_risks,
            "analytics_offline": state.get("analytics_offline", False),
        },
        role=state["requesting_user_role"],
    )
    return {**state, "client_update_draft": draft_response["draft_text"],
            "audit_log": [audit_entry("draft_node","draft_client_update","SUCCESS")]}

# ── PII Masking Node ──────────────────────────────────────────────────────
def pii_masking_node(state: ResearchStatusState) -> ResearchStatusState:
    """
    Scans client_update_draft for PII patterns:
    - Email addresses matching @c5i.ai domain → mask as [INTERNAL-CONTACT]
    - Respondent IDs → remove
    - Internal project codes that should not appear in client comms → mask
    """
    draft = state.get("client_update_draft","")
    masked_draft, masked_fields = apply_pii_mask(draft)
    return {
        **state,
        "client_update_draft": masked_draft,
        "pii_masked_fields":  masked_fields,
        "audit_log": [audit_entry("pii_masking_node","pii_scanner",
                                   "MASKED" if masked_fields else "CLEAN",
                                   detail={"fields_masked": masked_fields})],
    }

# ── Evidence Assembly Node ────────────────────────────────────────────────
def evidence_assembly_node(state: ResearchStatusState) -> ResearchStatusState:
    """
    Builds the evidence table: maps every claim in the draft to a tool call ID.
    Logs all blocked items: why they were withheld and which policy applied.
    """
    evidence_table  = build_evidence_table(state)
    blocked_items   = build_blocked_items_log(state)
    return {**state, "evidence_table": evidence_table,
            "audit_log": [audit_entry("evidence_assembly_node","build_evidence_table","SUCCESS",
                                       detail={"evidence_rows": len(evidence_table),
                                               "blocked_items": len(blocked_items)})]}

# ── Audit Finalise Node ───────────────────────────────────────────────────
def audit_finalise_node(state: ResearchStatusState) -> ResearchStatusState:
    """
    Writes the complete audit trail to audit_logs/audit_log.json.
    Computes: total tool calls, blocked calls, PII events, total cost/latency.
    """
    write_audit_log(state["audit_log"], state["project_id"], state["requesting_user"])
    final_output = {
        "client_update_draft": state["client_update_draft"],
        "evidence_table":      state["evidence_table"],
        "blocked_items":       state["blocked_tool_calls"],
        "pii_masked":          state["pii_masked_fields"],
        "system_caveats":      state["system_caveats"],
        "access_violations_attempted": state.get("access_violations_attempted", []),
        "audit_entry_count":   len(state["audit_log"]),
    }
    return {**state, "final_output": final_output}
```

---

### 4.5 Graph Assembly and Execution

```python
# graph.py
from langgraph.graph import StateGraph, END

def build_research_status_graph():
    graph = StateGraph(ResearchStatusState)

    # Register nodes
    graph.add_node("tool_discovery_node",    tool_discovery_node)
    graph.add_node("health_check_node",      health_check_node)
    graph.add_node("fallback_router_node",   fallback_router_node)
    graph.add_node("field_node",             field_node)
    graph.add_node("dq_check_node",          dq_check_node)
    graph.add_node("analytics_node",         analytics_node)
    graph.add_node("insights_deferred_node", insights_deferred_node)
    graph.add_node("timeline_risk_node",     timeline_risk_node)
    graph.add_node("email_context_node",     email_context_node)
    graph.add_node("draft_node",             draft_node)
    graph.add_node("pii_masking_node",       pii_masking_node)
    graph.add_node("evidence_assembly_node", evidence_assembly_node)
    graph.add_node("audit_finalise_node",    audit_finalise_node)

    # Linear edges
    graph.set_entry_point("tool_discovery_node")
    graph.add_edge("tool_discovery_node", "health_check_node")

    # Conditional edge: route based on MCP health
    graph.add_conditional_edges(
        "health_check_node",
        route_after_health_check,
        {"field_node": "field_node", "fallback_router_node": "fallback_router_node"}
    )
    graph.add_edge("fallback_router_node", "field_node")
    graph.add_edge("field_node",           "dq_check_node")
    graph.add_edge("dq_check_node",        "analytics_node")

    # Conditional edge: analytics online vs offline
    graph.add_conditional_edges(
        "analytics_node",
        lambda s: "insights_deferred_node" if s.get("analytics_offline") else "timeline_risk_node",
        {"insights_deferred_node": "insights_deferred_node",
         "timeline_risk_node":     "timeline_risk_node"}
    )
    graph.add_edge("insights_deferred_node", "timeline_risk_node")
    graph.add_edge("timeline_risk_node",     "email_context_node")
    graph.add_edge("email_context_node",     "draft_node")
    graph.add_edge("draft_node",             "pii_masking_node")
    graph.add_edge("pii_masking_node",       "evidence_assembly_node")
    graph.add_edge("evidence_assembly_node", "audit_finalise_node")
    graph.add_edge("audit_finalise_node",    END)

    return graph.compile()

# Execution
app = build_research_status_graph()

result = app.invoke({
    "project_id":            "PROJ-2025-GL-042",
    "requesting_user_role":  "ROLE-CS",
    "requesting_user":       "Ananya Sharma",
    "request_timestamp":     "2025-04-18T14:20:00",
    "analytics_offline":     False,
    "pii_masked_fields":     [],
    "blocked_tool_calls":    [],
    "access_violations_attempted": [],
    "system_caveats":        [],
    "audit_log":             [],
})
```

---

## 5. MCP and A2A: Interplay and Value Proposition

### 5.1 What MCP Provides (The Tool Layer)

MCP (Model Context Protocol) standardises how agents discover and call tools — regardless of which agent framework is orchestrating them.

**In this project, MCP delivers four things:**

| Capability | How It Works Here | Without MCP |
|-----------|------------------|-------------|
| **Tool discovery** | Agents query the registry at runtime to find what's available | Each agent has a hardcoded function list; adding a tool requires code deployment |
| **Permission enforcement at source** | `accessible_to` and PII flags live in the tool schema, enforced by the MCP server | Access control lives in application code — brittle, easily bypassed |
| **Domain ownership** | Field owns FieldMCP; Analytics owns AnalyticsMCP; CS owns ClientServicingMCP | All functions in one codebase — domain boundaries are naming conventions only |
| **Graceful degradation** | Clients detect ONLINE/DEGRADED/OFFLINE and route accordingly | A broken function throws an exception; no structured fallback path |

```
MCP VALUE: The PII block on get_pii_fields is not enforced by the agent.
           It is enforced by the server — accessible_to=[].
           No agent configuration change can bypass it.
           This is the security property MCP enables.
```

### 5.2 What A2A Provides (The Collaboration Layer)

Agent-to-Agent (A2A) is the protocol through which specialised agents exchange evidence, caveats, and outputs — without any single agent needing full data access.

**In this project, A2A delivers four things:**

| Capability | How It Works Here | Without A2A |
|-----------|------------------|-------------|
| **Domain expertise isolation** | Analytics Agent handles insight confidence; Field Agent handles DQ framing | One agent must handle all domains — loses specialisation |
| **Least-privilege reasoning** | Each agent only has access to its domain's MCP tools | A single agent would need access to all data — larger blast radius |
| **Evidence passing with provenance** | Field Agent returns a structured package; Analytics Agent receives it as context | Insights are generated without field context — potential inconsistencies |
| **Role inheritance** | Orchestrator's role (ROLE-CS) flows through all agent calls — Analytics Agent cannot access ROLE-AN-only tools even when called by the orchestrator | Permissions not context-sensitive — all agents operate at max privilege |

```
A2A VALUE: The Analytics Agent cannot call get_insight_summaries_all
           even though the orchestrator theoretically could route to it.
           The agent's context (ROLE-CS request) flows through to the
           MCP server call — role is not re-elevated at agent boundary.
           This is the isolation property A2A enables.
```

### 5.3 MCP × A2A Interplay: The Compound Value

Neither MCP nor A2A alone produces the security and auditability properties this solution requires. Their value is multiplicative:

```
MCP alone:     Tools are modular and discoverable.
               But: a single agent with full role could access everything.

A2A alone:     Specialised agents reason about their domain.
               But: without MCP, each agent hardcodes its tools and access rules.

MCP + A2A:     • Tool ownership is explicit and server-enforced (MCP)
               • Agent reasoning is domain-specific and role-bounded (A2A)
               • Permission enforcement is at source, not in orchestrator (MCP)
               • Evidence provenance flows through agent handoffs (A2A)
               • Any new tool added to a domain MCP server is automatically
                 available to the right agents without code changes (MCP)
               • Any new agent can join the workflow by registering with the
                 orchestrator and declaring its tool dependencies (A2A)
```

**The INS-004 example illustrates this perfectly:**

```
Without MCP+A2A:
  Monolithic agent → calls all insight functions → returns INS-004 → client sees
  preliminary Youth finding → GreenLeaf acts on an unconfirmed hypothesis
  → credibility risk

With MCP+A2A:
  Orchestrator (ROLE-CS) → Analytics Agent → calls get_insight_summaries_cleared
  → AnalyticsMCP filters INS-004 (cleared_for_client=False) at data level
  → Analytics Agent only receives INS-001, INS-002, INS-003
  → CS Agent drafts update with cleared insights only
  → Blocked item logged: INS-004 withheld (cleared_for_client=False)
  → Client update is safe AND the audit trail shows exactly what was withheld
```

---

## 6. CrewAI vs LangGraph — Decision Guide

| Dimension | CrewAI | LangGraph |
|-----------|--------|-----------|
| **Mental model** | Teams with roles and tasks | State machines with typed transitions |
| **Best for** | Role-driven workflows with natural delegation | Complex conditional routing and audit-critical pipelines |
| **Routing** | Process.hierarchical (manager delegates) | Explicit conditional edges — routing is code |
| **State management** | Memory across tasks within a crew | Typed state object passed through every node |
| **Auditability** | Task output logs; delegation trace | Full state captured at every node; every transition is explicit |
| **Failure handling** | Task retry; crew-level exception handling | Conditional edges to fallback nodes; failure is a first-class routing case |
| **MCP integration** | MCPServerTool wrapper per crew | call_mcp_tool() in each node; health check is a dedicated node |
| **When to choose** | Research operations, consulting workflows, multi-team coordination | Supply chain command centres, regulated pipelines, audit-mandatory systems |
| **This project fit** | **Strong** — department-crew mapping is intuitive | **Strong** — degraded server routing and PII masking as explicit nodes |

**Recommendation for this project:** Both implementations are viable. Use **CrewAI** if the team prioritises rapid development and the crew/role metaphor aligns with how the organisation is structured. Use **LangGraph** if audit completeness, conditional routing (degraded servers, offline fallbacks), and state immutability are primary requirements. A production deployment might use **LangGraph for the orchestration layer** (deterministic routing, full state trace) with **CrewAI-style agent definitions** within each node (role backstory, tool list, delegation rules).

---

## 7. Governance Layer — What Both Implementations Share

Regardless of framework, the following governance components are framework-agnostic and apply to both:

```
┌────────────────────────────────────────────────────────────┐
│  GOVERNANCE LAYER (implemented identically in both)        │
│                                                            │
│  1. PII Masking                                            │
│     apply_pii_mask(text) → removes @c5i.ai emails,        │
│     respondent IDs, internal reference codes              │
│     Applied: after draft_node before final output          │
│                                                            │
│  2. Cleared Insight Filter                                 │
│     Enforced at: AnalyticsMCP data level (tool returns     │
│     only cleared_for_client=True records)                  │
│     Second check: analytics_node validates the filter      │
│                                                            │
│  3. Internal Email Filter                                  │
│     get_client_emails(internal_only=False) parameter       │
│     Email-004 never enters agent context                   │
│                                                            │
│  4. Stale Data Detection                                   │
│     AnalyticsMCP returns stale_data_flag in every response │
│     Detected in analytics_node → injected into caveats     │
│                                                            │
│  5. Audit Log (append-only)                                │
│     Every tool call, agent handoff, block, and fallback    │
│     logged with: timestamp, agent, tool, status, latency,  │
│     tokens, cost, block_reason, fallback_source            │
│                                                            │
│  6. Evidence Table                                         │
│     Every claim in the client draft traced to a tool call  │
│     ID → supports post-hoc audit of any assertion          │
└────────────────────────────────────────────────────────────┘
```

---

## 8. Key Files Reference

| File | Used By | Purpose |
|------|---------|---------|
| `mcp_server_schemas/tool_registry.json` | tool_discovery_node / Crew kickoff | Single source of truth for all 19 tools, access lists, PII flags |
| `mcp_server_schemas/mcp_health_status.json` | health_check_node | Server health for routing decisions |
| `role_permission_matrix/role_permission_matrix.json` | Permission enforcement | Role → tool access mapping |
| `insight_summaries/insight_summaries.json` | AnalyticsMCP data layer | INS-004 cleared_for_client=False — the key policy test |
| `client_emails/client_email_thread.json` | CSAgent | EMAIL-004 internal_only=True — the internal leak prevention test |
| `agent_outputs/monolithic_agent_output.json` | Demo Step 2 | Baseline failure — 5 policy violations annotated |
| `agent_outputs/orchestrated_output.json` | Demo Steps 6-8 | Gold-standard output with evidence table and blocked items |
| `audit_logs/audit_log.json` | Demo Step 8 | 17-entry audit trail including TC-009 (BLOCKED) and TC-011 (BLOCKED_PII) |

---

*This document is the architecture reference for Project 6 demo implementation.*  
*Pair with: `DATASET_DESCRIPTION.md` for data asset details and `mcp_eval_benchmark.json` for evaluation cases.*
