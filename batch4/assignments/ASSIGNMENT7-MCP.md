# Assignment: Web-Based MCP Server for ICD Lookup

## Objective

Convert the existing **stdio-based** ICD Lookup MCP server into a **web-based HTTP server** so it can be called over a network (e.g., from a browser, curl, or a remote client). You will use **FastMCP's SSE transport** (Server-Sent Events over HTTP) and write a test client that connects over `localhost`.

---

## Background: MCP Transports

The Model Context Protocol supports multiple transports:

| Transport | How it works | Use case |
|-----------|-------------|----------|
| `stdio` | Server runs as subprocess, communicates via stdin/stdout | Local tools, VS Code extensions |
| `sse` (HTTP + SSE) | Server runs as HTTP server, streams responses via SSE | Web deployable, remote access, multi-client |
| `streamable-http` | Newer HTTP transport (FastMCP v2+) | Same as SSE but with better streaming |

In this assignment you will use the **`sse`** transport, which runs a real HTTP server that any MCP-compatible client can connect to via `http://localhost:8000/sse`.

---

## Prerequisites

- Python 3.10+
- The ICD Lookup server code from `mcp_icdlookup/` (for reference)

---

## Setup Instructions

### 1. Create and activate a virtual environment

```bash
# From the simple_mcp/ directory
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install fastmcp uvicorn httpx
```

> `uvicorn` is the ASGI server FastMCP uses under the hood.  
> `httpx` is used in the test client for optional direct HTTP calls.

### 3. Create your server file

Create `icd_server.py` using the starter code below.

### 4. Run the server

```bash
python icd_server.py
```

You should see output like:

```
[2026-04-24 10:00:00] MCP Web Server starting on http://0.0.0.0:8000
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 5. Run the test client (in a separate terminal)

```bash
# Activate the same venv first
python test_client.py
```

---

## Starter Code

### `icd_server.py` — Web MCP Server

```python
"""
ICD Lookup MCP Server — HTTP/SSE Transport
Accessible over the network at http://localhost:8000/sse
"""

from fastmcp import FastMCP
import re
from datetime import datetime

# TODO: Change the host/port if needed
HOST = "0.0.0.0"
PORT = 8000

mcp = FastMCP("ICD Code Lookup Web Server")


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")


# ── ICD-10 mock database ────────────────────────────────────────────────────
ICD_DATABASE = {
    "diabetes":          "E11.9 - Type 2 diabetes mellitus without complications",
    "type 1 diabetes":   "E10.9 - Type 1 diabetes mellitus without complications",
    "type 2 diabetes":   "E11.9 - Type 2 diabetes mellitus without complications",
    "hypertension":      "I10 - Essential (primary) hypertension",
    "high blood pressure":"I10 - Essential (primary) hypertension",
    "pneumonia":         "J18.9 - Pneumonia, unspecified organism",
    "asthma":            "J45.909 - Unspecified asthma, uncomplicated",
    "copd":              "J44.9 - Chronic obstructive pulmonary disease, unspecified",
    "bronchitis":        "J40 - Bronchitis, not specified as acute or chronic",
    "migraine":          "G43.909 - Migraine, unspecified, not intractable",
    "headache":          "R51.9 - Headache, unspecified",
    "depression":        "F32.9 - Major depressive disorder, single episode, unspecified",
    "anxiety":           "F41.9 - Anxiety disorder, unspecified",
    "covid":             "U07.1 - COVID-19",
    "coronavirus":       "U07.1 - COVID-19",
    "influenza":         "J11.1 - Influenza with other respiratory manifestations",
    "flu":               "J11.1 - Influenza with other respiratory manifestations",
    "chest pain":        "R07.9 - Chest pain, unspecified",
    "abdominal pain":    "R10.9 - Unspecified abdominal pain",
    "back pain":         "M54.9 - Dorsalgia, unspecified",
    "fracture":          "S42.90 - Fracture of unspecified shoulder girdle",
    "sprain":            "S93.40 - Sprain of unspecified ligament of ankle",
}


# ── Tools ───────────────────────────────────────────────────────────────────

@mcp.tool()
def lookup_icd_code(description: str) -> str:
    """
    Look up ICD-10 code based on a medical condition description.

    Args:
        description: Medical condition (e.g. "diabetes", "high blood pressure")

    Returns:
        ICD-10 code and description, or a not-found message
    """
    log(f"lookup_icd_code('{description}')")
    key = description.lower().strip()

    if key in ICD_DATABASE:
        return ICD_DATABASE[key]

    for db_key, value in ICD_DATABASE.items():
        if re.search(r'\b' + re.escape(db_key) + r'\b', key):
            return value

    available = ", ".join(sorted(ICD_DATABASE.keys()))
    return f"No ICD code found for '{description}'. Available: {available}"


@mcp.tool()
def list_available_conditions() -> str:
    """
    List all available medical conditions in the database.

    Returns:
        Comma-separated list of condition names
    """
    log("list_available_conditions()")
    conditions = sorted(ICD_DATABASE.keys())
    return f"Available conditions ({len(conditions)}): " + ", ".join(conditions)


# TODO (Task 3): Add a third tool here — see Tasks section below


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log(f"MCP Web Server starting on http://{HOST}:{PORT}")
    log("Clients connect to: http://localhost:8000/sse")
    mcp.run(transport="sse", host=HOST, port=PORT)
```

---

### `test_client.py` — MCP Test Client

```python
"""
Test client for the ICD Lookup web MCP server.
Connects via HTTP/SSE to http://localhost:8000/sse
Run the server first: python icd_server.py
"""

import asyncio
from fastmcp import Client

SERVER_URL = "http://localhost:8000/sse"


async def main():
    print(f"Connecting to MCP server at {SERVER_URL}\n")

    async with Client(SERVER_URL) as client:

        # ── Discover tools ──────────────────────────────────────────────
        tools = await client.list_tools()
        print("Available tools:", [t.name for t in tools])
        print()

        # ── list_available_conditions ───────────────────────────────────
        result = await client.call_tool("list_available_conditions", {})
        print("list_available_conditions:")
        print(result.content[0].text)
        print()

        # ── lookup_icd_code ─────────────────────────────────────────────
        test_cases = [
            "diabetes",
            "high blood pressure",
            "COVID",
            "migraine",
            "unknown condition xyz",
        ]

        print("lookup_icd_code results:")
        for condition in test_cases:
            result = await client.call_tool(
                "lookup_icd_code", {"description": condition}
            )
            print(f"  '{condition}' → {result.content[0].text}")

        # TODO (Task 3): Call your new tool here and print the result


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Tasks

Work through these tasks in order. Each builds on the previous one.

### Task 1 — Get the starter running

1. Set up the venv and install dependencies (see Setup Instructions).
2. Copy the starter code into `icd_server.py` and `test_client.py`.
3. Start the server and run the test client.
4. Confirm all test cases print correct ICD codes.

**Expected output (partial):**
```
Available tools: ['lookup_icd_code', 'list_available_conditions']

list_available_conditions:
Available conditions (21): abdominal pain, anxiety, asthma, ...

lookup_icd_code results:
  'diabetes' → E11.9 - Type 2 diabetes mellitus without complications
  'high blood pressure' → I10 - Essential (primary) hypertension
  'COVID' → U07.1 - COVID-19
  ...
```

---

### Task 2 — Verify it is actually HTTP

While the server is running, open a browser and navigate to:

```
http://localhost:8000/sse
```

You should see the SSE stream. Also try:

```bash
curl http://localhost:8000/sse
```

This confirms you have a real web server, not a stdio subprocess.

---

### Task 3 — Add a new tool: `search_by_code`

Add a tool that lets a user look up a condition by its ICD code (e.g., `"E11.9"` → `"Type 2 diabetes mellitus"`).

Requirements:
- Decorated with `@mcp.tool()`
- Accepts a `code: str` parameter
- Returns the matching condition name, or a not-found message if the code doesn't exist
- Call it from `test_client.py` and print the result

Hint: You will need to build a reverse lookup dictionary from `ICD_DATABASE`.

---

### Task 4 — Explore: What happens with multiple clients?

Open **two** terminals, both running `test_client.py` simultaneously while the server is running.

- Do both clients get responses?
- Check the server logs — can you see both connections?

Write 2–3 sentences in a comment at the top of `test_client.py` describing what you observed. This is the key advantage of an HTTP transport over stdio.

---

### Task 5 (Stretch) — Swap to Flask

Create an alternative server `icd_server_flask.py` that implements the same two tools using **Flask** instead of FastMCP.

This will require you to implement the MCP JSON-RPC protocol manually:
- `POST /` accepts `{"jsonrpc":"2.0","method":"tools/call","params":{...}}`
- Returns a JSON response with the tool result

Update `test_client.py` (or create `test_client_http.py`) to call this Flask server using the `requests` or `httpx` library directly (no FastMCP client needed — just plain HTTP POST).

Starter skeleton:

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["POST"])
def handle():
    body = request.get_json()
    method = body.get("method")
    params = body.get("params", {})

    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        # TODO: dispatch to lookup_icd_code or list_available_conditions
        result = "not implemented"
        return jsonify({"jsonrpc": "2.0", "id": body.get("id"), "result": result})

    return jsonify({"error": "unknown method"}), 400

if __name__ == "__main__":
    app.run(port=8001, debug=True)
```

---

---

## Part B (Stretch Goal): Streamable HTTP — True Progressive Results

### What is `streamable-http`?

Both `sse` and `streamable-http` run over HTTP, but they differ in how the server sends results back:

| | `sse` transport | `streamable-http` transport |
|---|---|---|
| Response style | Full result sent when tool finishes | Chunks sent **as they are produced** |
| Tool returns | Single value | Can `yield` multiple chunks |
| Client receives | All-at-once after completion | Each chunk the moment the server yields it |
| Best for | Short, fast tools | Long-running tools, progress feedback, large outputs |

The key capability unlocked by `streamable-http` is that a tool can be an **async generator** — it `yield`s partial results one at a time, and the client receives each chunk immediately rather than waiting for the whole operation to finish.

### The Demo Use Case: Batch ICD Report

Imagine a clinical system querying ICD codes for a list of patient conditions. Each condition requires a database call that takes ~1 second. For 6 conditions:

- **Without streaming** → user stares at a spinner for 6 seconds, then sees everything at once
- **With streaming** → first result appears in 1 second, then one more every second — the user sees progress and can start reading immediately

This is the same value proposition as ChatGPT printing tokens as they are generated rather than waiting until the full answer is ready.

---

### Starter Code

#### `icd_server_stream.py` — Streamable HTTP Server

```python
"""
ICD Lookup MCP Server — streamable-http transport (port 8001)
Tools can yield partial results; the client receives each chunk immediately.

Run:  python icd_server_stream.py
"""

import asyncio
from datetime import datetime
from fastmcp import FastMCP

HOST = "0.0.0.0"
PORT = 8001  # different port so it can run alongside icd_server.py

mcp = FastMCP("ICD Code Lookup — Streaming")


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


ICD_DATABASE = {
    "diabetes":           "E11.9 - Type 2 diabetes mellitus without complications",
    "type 1 diabetes":    "E10.9 - Type 1 diabetes mellitus without complications",
    "type 2 diabetes":    "E11.9 - Type 2 diabetes mellitus without complications",
    "hypertension":       "I10 - Essential (primary) hypertension",
    "high blood pressure":"I10 - Essential (primary) hypertension",
    "pneumonia":          "J18.9 - Pneumonia, unspecified organism",
    "asthma":             "J45.909 - Unspecified asthma, uncomplicated",
    "copd":               "J44.9 - Chronic obstructive pulmonary disease, unspecified",
    "migraine":           "G43.909 - Migraine, unspecified, not intractable",
    "depression":         "F32.9 - Major depressive disorder, single episode, unspecified",
    "anxiety":            "F41.9 - Anxiety disorder, unspecified",
    "covid":              "U07.1 - COVID-19",
    "influenza":          "J11.1 - Influenza with other respiratory manifestations",
    "chest pain":         "R07.9 - Chest pain, unspecified",
    "back pain":          "M54.9 - Dorsalgia, unspecified",
}


def _lookup(description: str) -> str:
    """Shared lookup logic (not a tool)."""
    import re
    key = description.lower().strip()
    if key in ICD_DATABASE:
        return ICD_DATABASE[key]
    for db_key, value in ICD_DATABASE.items():
        if re.search(r'\b' + re.escape(db_key) + r'\b', key):
            return value
    return f"NOT FOUND: '{description}'"


# ── Non-streaming tool (for comparison) ─────────────────────────────────────

@mcp.tool()
async def batch_lookup_blocking(conditions: list[str]) -> str:
    """
    Looks up ICD codes for multiple conditions — BLOCKING version.
    Simulates slow processing: waits for ALL conditions before returning anything.
    Compare the wall-clock time to batch_lookup_streaming.

    Args:
        conditions: List of medical condition descriptions
    """
    log(f"batch_lookup_BLOCKING started for {len(conditions)} conditions")
    results = []
    for condition in conditions:
        await asyncio.sleep(1.0)          # simulate a slow DB / API call
        result = _lookup(condition)
        results.append(f"{condition}: {result}")
        log(f"  processed '{condition}' (buffered, not sent yet)")
    log("batch_lookup_BLOCKING returning all at once")
    return "\n".join(results)


# ── Streaming tool ───────────────────────────────────────────────────────────

@mcp.tool()
async def batch_lookup_streaming(conditions: list[str]):
    """
    Looks up ICD codes for multiple conditions — STREAMING version.
    Each result is yielded immediately after processing, so the client
    sees it ~1 second after it was found rather than waiting for all results.

    Args:
        conditions: List of medical condition descriptions
    """
    log(f"batch_lookup_STREAMING started for {len(conditions)} conditions")
    yield f"Starting batch lookup for {len(conditions)} conditions...\n"

    for i, condition in enumerate(conditions, 1):
        await asyncio.sleep(1.0)          # simulate a slow DB / API call
        result = _lookup(condition)
        chunk = f"[{i}/{len(conditions)}] {condition}: {result}"
        log(f"  yielding chunk: {chunk}")
        yield chunk                        # client receives this RIGHT NOW

    yield f"\nDone. Processed {len(conditions)} conditions."


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log(f"Streaming MCP server starting → http://localhost:{PORT}/mcp")
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
```

---

#### `test_client_stream.py` — Streaming Test Client

```python
"""
Streaming test client for icd_server_stream.py
Demonstrates the difference between blocking and streaming tool calls.

Run the server first:  python icd_server_stream.py
Then run this client:  python test_client_stream.py
"""

import asyncio
import time
from datetime import datetime
from fastmcp import Client

SERVER_URL = "http://localhost:8001/mcp"

CONDITIONS = [
    "diabetes",
    "hypertension",
    "covid",
    "migraine",
    "anxiety",
    "back pain",
]


def ts() -> str:
    """Current time as HH:MM:SS for log lines."""
    return datetime.now().strftime("%H:%M:%S")


async def demo_blocking(client: Client):
    """Call the blocking tool — all results arrive at once after ~6 seconds."""
    print("=" * 60)
    print("BLOCKING (non-streaming) — batch_lookup_blocking")
    print("=" * 60)
    print(f"[{ts()}] Calling tool... (expect ~{len(CONDITIONS)}s delay)\n")

    start = time.perf_counter()
    result = await client.call_tool(
        "batch_lookup_blocking", {"conditions": CONDITIONS}
    )
    elapsed = time.perf_counter() - start

    print(f"[{ts()}] All results arrived at once after {elapsed:.1f}s:\n")
    for chunk in result.content:
        print(f"  {chunk.text}")
    print()


async def demo_streaming(client: Client):
    """Call the streaming tool — each result chunk arrives as soon as it's ready."""
    print("=" * 60)
    print("STREAMING — batch_lookup_streaming")
    print("=" * 60)
    print(f"[{ts()}] Calling tool... (watch results appear one by one)\n")

    start = time.perf_counter()
    result = await client.call_tool(
        "batch_lookup_streaming", {"conditions": CONDITIONS}
    )
    # result.content holds all chunks — print them with their relative timestamps
    # In a true streaming client (e.g. a UI), each chunk would render as it arrived.
    for chunk in result.content:
        print(f"[{ts()}] {chunk.text}")

    elapsed = time.perf_counter() - start
    print(f"\n[{ts()}] Total wall time: {elapsed:.1f}s")
    print()

    # ── Side-by-side observation guide ──────────────────────────────────────
    print("Observation:")
    print("  Blocking  → one long wait, then all lines printed simultaneously")
    print("  Streaming → each line printed as the server yielded it (~1s apart)")
    print("  In a real UI the streaming version would feel far more responsive.")


async def main():
    print(f"\nConnecting to {SERVER_URL}\n")
    async with Client(SERVER_URL) as client:
        tools = await client.list_tools()
        print("Available tools:", [t.name for t in tools], "\n")

        await demo_blocking(client)
        await demo_streaming(client)

        # TODO (Part B Task 2): add your own tool call here


if __name__ == "__main__":
    asyncio.run(main())
```

---

### Part B Tasks

#### B1 — Run and observe

1. Start the streaming server: `python icd_server_stream.py`
2. In a second terminal, run the client: `python test_client_stream.py`
3. Watch the terminal output carefully. For the blocking call you should see one long pause followed by all results. For the streaming call you should see each line print approximately 1 second apart.
4. Look at the **server-side logs** at the same time — you will see each `yielding chunk` log appear at 1-second intervals, confirming the server is computing and sending progressively.

**Expected client output (abridged):**
```
BLOCKING — batch_lookup_blocking
[10:01:00] Calling tool... (expect ~6s delay)
[10:01:06] All results arrived at once after 6.0s:
  diabetes: E11.9 - Type 2 diabetes mellitus ...
  hypertension: I10 - Essential (primary) hypertension
  ...

STREAMING — batch_lookup_streaming
[10:01:06] Calling tool... (watch results appear one by one)
[10:01:06] Starting batch lookup for 6 conditions...
[10:01:07] [1/6] diabetes: E11.9 - Type 2 diabetes mellitus ...
[10:01:08] [2/6] hypertension: I10 - Essential (primary) hypertension
[10:01:09] [3/6] covid: U07.1 - COVID-19
...
```

---

#### B2 — Add a progress header

Modify `batch_lookup_streaming` to also yield a **summary line at the end** that includes total elapsed time and how many conditions were found vs not found.

Example final chunk:
```
Summary: 6 processed, 5 found, 1 not found. Total time: 6.1s
```

---

#### B3 — Think about real-world use cases

Streaming is most valuable when:
- Results take time to compute (LLM calls, external API, slow DB)
- The user benefits from seeing partial output early
- The full response could be very large (file generation, reports)

Write 3–4 bullet points in a comment block at the top of `icd_server_stream.py` describing real-world healthcare or clinical use cases where a streaming MCP tool would be significantly better than a blocking one.

---

## Key Differences: All Three Transports

| | `stdio` (original) | `sse` (Part A) | `streamable-http` (Part B) |
|---|---|---|---|
| How server starts | Subprocess per client | Persistent HTTP process | Persistent HTTP process |
| Who can connect | Spawning process only | Any network client | Any network client |
| Multiple clients | No | Yes | Yes |
| Tool result delivery | All-at-once | All-at-once | **Progressive chunks** |
| Tools can `yield` | No | No | **Yes** |
| Best for | Local VS Code tools | Web APIs, remote access | Long-running / LLM-backed tools |
| Debugging | Hard | `curl`, browser | `curl`, browser, streaming logs |

---

## Submission Checklist

- [ ] `icd_server.py` runs without errors
- [ ] `test_client.py` connects and calls all tools successfully
- [ ] Task 2 verified via browser or `curl`
- [ ] Task 3: `search_by_code` tool added to server and called in test client
- [ ] Task 4: observation comment added to `test_client.py`
- [ ] (Stretch A) `icd_server_flask.py` implemented and tested
- [ ] (Stretch B1) `icd_server_stream.py` and `test_client_stream.py` running, timestamps observed
- [ ] (Stretch B2) Summary chunk added to streaming tool
- [ ] (Stretch B3) Real-world use-case comment block added to `icd_server_stream.py`
