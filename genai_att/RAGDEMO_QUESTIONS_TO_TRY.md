# RAG Demo — Questions to Try

This app (`retriever.py`) indexes everything in `data/` into Chroma using **pure vector
similarity search** (`search_type='similarity', k=3`), 256-character chunks
(`indexer.py` line 49), and **no metadata extraction** (no structured fields for
"years of experience," "degree," "document date," etc.). That specific setup is what
makes each limitation below reproducible — they aren't generic RAG folklore, they're
consequences of this code.

Run the app, ask each question, and look at the **retrieved source chunks**, not just
the final answer — that's where you'll see *why* it worked or failed.

---

## Part 1 — Where RAG shines (semantic value)

### V1. "I need someone who can manage vendor invoices, reduce outstanding balances, and stay compliant with GST/TDS — who fits?"
- **Data:** `kunal.pdf` (Accounts Payable/Receivable Specialist, DSO reduction, TDS/GST compliance).
- **Why it works:** None of these phrases are copy-pasted from the resume — vector
  search matches on *meaning* (invoice management ≈ Accounts Payable, "reduce
  outstanding balances" ≈ "reducing DSO by 10%"), not literal keywords. This is the
  headline value of embeddings over keyword search.

### V2. "What was HDFC Bank's profit after tax and return on equity for FY24?"
- **Data:** `hdfc_financial_statement_2024.pdf` (₹60,812 crore PAT, 16.1% ROE, in the
  "Our Performance" KPI tiles).
- **Why it works:** Instant answer from a 600+ page annual report without anyone
  manually flipping to the right page. This is the core RAG pitch: point at a huge
  document, ask a plain-English question, skip the table of contents.

### V3. "Summarize what happens when ABC Bank enters the Yellow Zone with 6 VaR exceptions."
- **Data:** `VAR Backtesting policy.md`, §5.1 + the worked capital example in §3.3
  (multiplication factor jumps 3.00→3.50, ₹35 crore additional capital, CRO escalation
  to CEO/BRMC, RBI notified within 2 days).
- **Why it works:** The answer is scattered across several non-adjacent sections of a
  30-page policy. RAG assembles it into one coherent paragraph — this is a genuine
  time-saver over reading the whole document.

### V4. "Who has the strongest background in campus recruitment and employer branding?"
- **Data:** `pooja.pdf` (Talent Acquisition Lead, campus recruitment programs,
  employer branding campaigns with 30% increase in applications).
- **Why it works:** Again, paraphrase-to-resume matching — "strongest background in
  employer branding" isn't a verbatim phrase, but semantically it's an easy match.

### V5. "What's the practical effect of a bank's VaR model entering the Red Zone?"
- **Data:** `VAR Backtesting policy.md`, §6 (multiplication factor to 4.00, 50%/severe
  trading restrictions, external validation by Deloitte/PwC/Oliver Wyman, RBI on-site
  inspection).
- **Why it works:** Turns a dense regulatory-procedure section into a plain-English
  explanation on demand — good for onboarding someone unfamiliar with Basel jargon.

---

## Part 2 — Where RAG breaks (and how you'd fix it)

### L1. "List every candidate who has an MBA."
- **Ground truth:** Pooja Iyer (MBA-HR, IIM Bangalore) and Rahul Gupta (MBA-HR, Christ
  University) — Kunal (B.Com) and Pankaj (B.E.) do not.
- **Likely failure:** With `k=3`, the retriever returns only 3 chunks total across the
  *entire* corpus — it isn't guaranteed to surface every resume, let alone the
  "Education" section of each one. You'll often get an incomplete list, or the model
  will confidently answer from whichever 1-2 resumes happened to score highest.
- **Root cause:** No structured metadata field for "degree." Vector similarity finds
  *relevant* chunks, not *all matching* records — it has no concept of "run this filter
  over every row."
- **Fix:** Extract structured fields (degree, years of experience, industry) into
  metadata at index time, and answer filter-style questions with a metadata query or
  SQL, not similarity search. This is the classic "RAG isn't a database" gap.

### L2. "Which candidate has the most total years of professional experience?"
- **Likely failure:** This requires reading and summing experience across *all four*
  resumes, but only 3 chunks come back, so the model reasons over partial data — it
  may miss a candidate entirely or misreport their year count.
- **Root cause:** Same as L1 — aggregation/ranking queries need full corpus recall,
  which top-k similarity search does not provide by design.
- **Fix:** Pre-compute "years of experience" as metadata at ingestion, or route
  aggregation questions to a different pipeline (e.g., a map-reduce pass over every
  document, or a text-to-SQL layer over structured fields) instead of top-k retrieval.

### L3. "What RBI circular number covers the current market risk guidelines, and what circular did it replace?"
- **Ground truth:** `rbi_risk_basel_extracts.md` — supersedes
  **DBR.No.BP.BC.85/21.04.098/2021-22** with **DBR.No.BP.BC.102/21.04.098/2023-24**.
- **Likely failure:** Ask for just "102" or just "85" and watch the retriever
  sometimes pull the wrong one, or the LLM present the two numbers with the
  supersede/superseded relationship flipped.
- **Root cause:** Embeddings encode *semantic* similarity, not exact character
  matches. "DBR.No.BP.BC.102/..." and "DBR.No.BP.BC.85/..." embed almost identically
  because they're the same kind of token in the same kind of sentence — vector search
  has no special affinity for exact digit sequences the way keyword search does.
- **Fix:** This is the textbook case for **hybrid search (BM25/keyword + vector)** —
  BM25 nails exact alphanumeric IDs (circular numbers, account numbers, patch/CVE
  numbers, part numbers) that embeddings blur together.

### L4. "Give me the complete VaR backtesting multiplication-factor schedule, from 0 exceptions to 10+."
- **Ground truth:** `VAR Backtesting policy.md` §3.3 has a 6-row table
  (0-4→3.00, 5→3.40, 6→3.50, 7→3.65, 8→3.75, 9→3.85, 10+→4.00).
- **Likely failure:** `chunk_size=256` characters (indexer.py line 49) is small
  enough to split a markdown table mid-row, and `k=3` only returns ~768 characters of
  context total — you'll typically get 2-3 rows of the table, not all of them, and the
  model may present a partial table as if it were complete.
- **Root cause:** Naive character-based chunking doesn't respect table/structural
  boundaries, and small k means even correct chunks don't add up to full context.
- **Fix:** Chunk by structural unit (keep tables intact, e.g. table-aware or
  markdown-header-aware splitting), increase `k` for tabular/numeric queries, or
  extract tables separately at ingestion so they're retrieved as one atomic block.

### L5. "Which patch fixes security vulnerability SEC-3478?"
- **Data:** `att_device_security_patch_bulletin.pdf` — a synthetic AT&T-style patch
  bulletin generated for this demo (`generate_att_patch_bulletin.py`). It contains 20
  patches; several are deliberately near-duplicates of each other. Rows 1-3 alone
  cover three different devices with three different vuln IDs that all read as
  "authentication bypass in the admin web interface/portal/API":
  `SEC-3477`→BGW210-700, `SEC-3478`→BGW320-500, `SEC-3479`→NVG599 — same for the
  buffer-overflow cluster (`SEC-2201`/`2203`/`2204`) and the XSS cluster
  (`SEC-2890`/`2891`/`2892`).
- **Ground truth:** `SEC-3478` → **PATCH-AT-2024-047**, AT&T BGW320-500 Wi-Fi Gateway.
- **Likely failure:** Ask for `SEC-3478` and there's a good chance you get back the
  fix for `SEC-3477` or `SEC-3479` instead — same wording, same structure, adjacent
  gateway devices, only the ID number differs. There's also a second, sneakier
  failure: because the ID column is narrow, the PDF text extraction sometimes splits
  the ID itself across a line break (e.g. "SEC-347" and "7" land as separate tokens),
  so the exact string "SEC-3478" may not even appear intact in any chunk — a keyword
  search would miss it too unless the query/index is ID-normalization aware.
- **Root cause:** Same as L3 (RBI circular numbers) — embeddings cluster on the
  *sentence*, and a 4-digit suffix contributes almost nothing to that vector. This
  file makes the failure much more visible than L3 because there are three
  near-identical rows sitting right next to each other instead of just two.
- **Fix:** Same as L3 — hybrid BM25 + vector search, or better, extract
  `(patch_number, vuln_id, model_number)` as structured metadata at ingestion and do
  an exact-match/metadata lookup for any query containing an ID pattern like
  `SEC-\d+`, falling back to vector search only for descriptive questions
  ("which patches fix authentication bypass issues?").

### L6. "What was the household's month-by-month electricity consumption trend over the last year?"
- **Ground truth:** `electricity_bill_aug_2025.pdf` page 1 has a **consumption-trend
  bar chart** (Aug 421 → Jul 580 kWh) — it's a rendered image with a numeric legend,
  not a text table.
- **Likely failure:** `PyPDFLoader` extracts raw text layout, so the chart's axis
  labels and bar values get flattened into a garbled run like
  `"Jul580Jun489May 536Apr474..."` with numbers and months interleaved out of order.
  The retriever will confidently hand this scrambled string to the LLM, which then
  either fabricates a plausible-sounding trend or misattributes numbers to the wrong
  months.
- **Root cause:** Text-only PDF extraction cannot parse charts/images — there's no
  vision step, so a visual bar chart becomes unreliable, unordered text.
- **Fix:** Use vision-capable parsing (multimodal PDF extraction, e.g. sending page
  images to a vision model, or a table/chart-extraction tool) for any PDF that encodes
  data visually rather than as text — plain `PyPDFLoader` text extraction is the wrong
  tool for chart data.

---

## Quick reference: root cause → fix

| Limitation | Root cause in this codebase | Fix |
|---|---|---|
| L1, L2 (completeness/aggregation) | `k=3`, no structured metadata | Metadata extraction + filtering/SQL, or full-corpus map-reduce |
| L3, L5(bonus) (exact IDs) | Pure vector similarity, no keyword search | Hybrid search: BM25 + vector |
| L4 (broken tables) | `chunk_size=256`, naive character splitting | Structure-aware chunking; keep tables atomic |
| L6 (charts/images) | Text-only PDF loader (`PyPDFLoader`) | Vision/multimodal extraction for visual data |

`att_device_security_patch_bulletin.pdf` is synthetic data generated by
`generate_att_patch_bulletin.py` in this folder — regenerate or extend it by editing
the `rows_raw` list in that script and re-running it.
