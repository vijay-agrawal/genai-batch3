# RAG over Market, Brand & Competitive Intelligence Repositories
## Synthetic Dataset Description & Demo Guide

**Project:** Project 1 — RAG over Market, Brand & Competitive Intelligence Repositories  
**Dataset Version:** 1.0  
**Last Updated:** March 2025  
**Domain:** Consumer & Market Insights; AI-Powered Research Operations

---

## Overview

This dataset simulates the research repository of a market research and consulting firm (c5i-style) covering a personal care category across India Urban, India Rural, and SEA Urban markets. It spans 5 brands (Brand A through Brand E) across 6 document types, designed to demonstrate every stage of the progressive RAG demo — from baseline LLM with no grounding, through hybrid retrieval, to citation-grounded answers with confidence labels and guardrails.

The dataset is designed with **deliberate retrieval challenges**: synonym variation (youth / Gen Z / college consumers / metro millennials), jargon-heavy SKU and campaign names for hybrid search demonstration, temporal metadata for filter tests, and an out-of-corpus guardrail case.

---

## Dataset Inventory

| File | Format | Records / Pages | Description |
|------|--------|----------------|-------------|
| `brand_tracker_summaries/brand_tracker_waves.json` | JSON | 90 rows | 6 quarterly waves × 5 brands × 3 markets — full funnel metrics |
| `brand_tracker_summaries/brand_tracker_waves.csv` | CSV | 90 rows | Same, tabular |
| `competitor_profiles/competitor_profiles.json` | JSON | 5 profiles | Brand A–E: share, revenue, distribution, digital maturity, strengths/weaknesses |
| `competitor_profiles/competitor_profiles.csv` | CSV | 5 profiles | Same, tabular |
| `campaign_summaries/campaign_summaries.json` | JSON | 8 campaigns | Campaign recall, purchase intent lift, agency, creative theme, qualitative summary |
| `campaign_summaries/campaign_summaries.csv` | CSV | 8 campaigns | Same, tabular |
| `consumer_reviews/consumer_reviews.json` | JSON | 170 reviews | Platform reviews with brand, segment, city, sentiment, rating, text |
| `consumer_reviews/consumer_reviews.csv` | CSV | 170 reviews | Same, tabular |
| `social_media_snippets/social_media_snippets.json` | JSON | 200 snippets | Twitter/X, Instagram, Reddit, YouTube social posts with engagement |
| `social_media_snippets/social_media_snippets.csv` | CSV | 200 snippets | Same, tabular |
| `category_trend_notes/category_trends.json` | JSON | 6 trends | Structural trend notes with brand implications, confidence, tags |
| `category_trend_notes/category_trends.csv` | CSV | 6 trends | Same, tabular |
| `market_research_reports/india_urban_ua_study_2025.md` | Markdown | ~6 pages | Full Usage & Attitude study — brand funnel, Gen Z deep dive, channel analysis |
| `market_research_reports/sea_brand_perception_2024.md` | Markdown | ~4 pages | SEA brand perception study — sustainability threshold, Brand E deep dive |
| `analyst_decks/competitive_landscape_analyst_note_q1_2025.md` | Markdown | ~3 pages | Analyst note — brand ratings, market share table, strategic risks |
| `evaluation_set/rag_evaluation_benchmark.json` | JSON | 12 cases | Ground truth Q&A with relevant doc IDs, source counts, guardrail flags |
| `evaluation_set/rag_evaluation_benchmark.csv` | CSV | 12 cases | Same, tabular |
| `metadata/metadata_registry.json` | JSON | 109 entries | Unified metadata: doc_id, brand, market, date, year, quarter, study_type, tags |
| `metadata/metadata_registry.csv` | CSV | 109 entries | Same, tabular |

**Total assets:** 20 files across 8 source folders

---

## Embedded Data Patterns

### Pattern A — Brand A's Gen Z Urban Decline (Core Demo Driver)
The dataset's central signal thread: Brand A is losing the Gen Z urban segment to Brand B.

Evidence across multiple document types:
- **Brand Tracker:** Gen Z preference for Brand A drops from 38% (Wave 1) to 22% (Wave 6); Brand B rises from 31% to 54%
- **U&A Study:** Gen Z now ranks sustainability, digital-first, and authentic voice above price — Brand A scores poorly on all three
- **Campaign Summaries:** Two Brand A Gen Z campaigns underperform (recall 18-22% vs category avg 35%); Brand B campaigns outperform (51% and 44%)
- **Consumer Reviews:** 30 negative Brand A reviews from Gen Z users; dominant themes — "uncle brand", "formula changed", "Brand B is better"
- **Social Media:** Recurring social posts calling Brand A outdated; organic Brand B advocacy from Gen Z
- **Competitor Profiles:** Brand A Gen Z affinity 3.1/10; Brand B 8.4/10; Brand A digital maturity LOW
- **Category Trends:** CT001 explains the structural shift in Gen Z purchase criteria; CT006 explains why Brand A's macro-influencer strategy underperforms

**Why this matters for demo:** A query like "Why is Brand A losing share among Gen Z?" should pull from at least 5 different document types — demonstrating cross-source synthesis. Keyword search alone will miss the synonym chain (Gen Z = youth = college consumers = metro millennials = under-25).

### Pattern B — Brand B as the Challenger Winner
Brand B is consistently the answer to what Brand A is getting wrong:
- Higher Gen Z preference across all 6 waves
- Superior campaign metrics (micro-influencer strategy)
- Strong digital maturity (loyalty app, 2M+ users)
- Eco-credentials (8.1/10 sustainability score)
- Campus activation stealing Brand A's college customer base
- Brand B overtakes Brand A in consideration and purchase intent in latest tracker wave

### Pattern C — Brand C's Rural Fortress vs Urban Weakness
- 38.2% rural share vs 14.6% urban — the largest market/segment gap in the dataset
- Rural campaign achieves highest recall (62%) in category
- Urban focus groups see Brand C as low-quality/old-fashioned
- Category trend CT003 (rural premiumisation) sets up a strategic risk discussion

### Pattern D — SEA: Sustainability as Entry Ticket
- Brand E dominates SEA premium (22.4% share, 34.1% YoY growth)
- Sustainability scores bifurcate brands: Brand E 9.2/10, Brand A 2.8/10
- SEA premium segment explicitly disqualifies brands with no sustainability claim (71% in Singapore)
- Brand A's 79% aided awareness in SEA does NOT convert to consideration (29%) — the awareness-to-consideration gap demo

### Pattern E — Retrieval Challenge: Synonym Variation
The following synonyms are deliberately distributed across documents to test semantic vs keyword retrieval:
- "Gen Z" ↔ "youth" ↔ "college consumers" ↔ "under-25" ↔ "metro millennials" ↔ "young adults"
- "Share of wallet" ↔ "purchase preference" ↔ "brand choice"
- "Digital" ↔ "online" ↔ "e-commerce" ↔ "app-first" ↔ "q-commerce"
- "Influencer" ↔ "creator" ↔ "micro-creator" ↔ "UGC" ↔ "content creator"

### Pattern F — Guardrail: Out-of-Corpus Question
EVAL006 asks for Brand A's EBITDA margin — this data does **not exist** in the corpus. The correct system behavior is to respond "INSUFFICIENT EVIDENCE" and decline to fabricate. This tests the answer guardrail at Demo Step 9.

### Pattern G — Metadata for Filter Testing (Demo Step 5)
- `year` field: 2023, 2024, 2025 — enables time-period filtering
- `market` field: "India Urban", "India Rural", "SEA Urban", "Middle East", "South Africa" — enables geographic filters
- `study_type` field: Brand Tracker, U&A, Campaign Evaluation, Competitive Intelligence — enables research type filters
- Query "Use only 2025 India urban studies" maps cleanly to `year=2025 AND market=India Urban` filter

---

## Demo Step ↔ Dataset Mapping

| Demo Step | What to Show | Key Files & Fields |
|-----------|-------------|-------------------|
| 1 | Business question framing | `india_urban_ua_study_2025.md` — Gen Z decline headline |
| 2 | Ungrounded LLM answer | No retrieval — baseline hallucination risk |
| 3 | Keyword / BM25 only | Misses: youth/college consumers/metro millennials synonyms → use consumer_reviews + social_media for synonym failure demo |
| 4 | Basic vector RAG | `brand_tracker_waves.json` + `competitor_profiles.json` — semantic matching but chunk duplication risk |
| 5 | Metadata filter | `metadata_registry.csv` filter: year=2025, market=India Urban → subset of brand_tracker + ua_study |
| 6 | Hybrid BM25 + embeddings | CAMP004 query with "CampusFirst + UGC + micro-creator + metro Q4" — jargon terms |
| 7 | MMR + re-ranking | EVAL009: "Compare Brand A vs Brand B across awareness, consideration, price perception" — needs 6+ sources |
| 8 | HyDE / query rewriting | EVAL007: "What is going wrong with the brand?" — vague; HyDE generates better retrieval queries |
| 9 | Answer guardrails | EVAL006: EBITDA query — no corpus match; system must say "Insufficient Evidence" |
| 10 | Limitations | Stale data caveat (tracker Wave 6 is March 2025), chart extraction gaps in PDF decks |
| 11 | Future scope | Automated ingestion, multimodal chart extraction, freshness monitoring |

---

## Demo Questions — By Stage

### Stage 1 — Framing the Business Problem
> **Q1.** "Why is Brand A losing share among Gen Z in urban markets?"

> **Q2.** "What is the current brand consideration ranking in India Urban for 2025?"

> **Q3.** "Which brand is gaining the most Gen Z preference and why?"

---

### Stage 2 — Baseline LLM (No Retrieval) — Show Hallucination Risk
> **Q4.** "Without looking at any documents, what do you think is happening with Brand A in urban India?"  
*(Show that LLM gives fluent but generic, ungrounded answer — not tied to client data)*

---

### Stage 3 — Keyword / BM25 Search — Show Synonym Failure
> **Q5.** "Search for documents about 'youth' and 'college consumers' losing trust in Brand A."  
*(Keyword search will NOT retrieve Brand Tracker docs that use 'Gen Z'; semantic will — contrast the two)*

> **Q6.** "Find all documents mentioning 'metro millennials' switching brands."  
*(Highlight: this phrase appears in social snippets but not tracker docs — keyword recall is incomplete)*

---

### Stage 4 — Basic Vector RAG — Show Semantic Gain + Chunk Issues
> **Q7.** "What are the top 3 reasons for Brand A's decline, with evidence?"  
*(Vector RAG retrieves relevant docs but may return duplicate tracker wave chunks — set up for MMR)*

> **Q8.** "What does the brand tracker data show about Brand A awareness trends over 6 waves?"

---

### Stage 5 — Metadata Filters (Demo Step 5)
> **Q9.** "Use only 2025 India urban studies — what is the current state of Brand A's consideration?"  
*(Filter: year=2025, market=India Urban — should restrict to Wave 6 tracker + U&A 2025)*

> **Q10.** "Show me only Campaign Evaluation studies from 2024. Which brand's campaigns performed best for Gen Z?"  
*(Filter: study_type=Campaign Evaluation, year=2024)*

> **Q11.** "Restrict to Brand Tracker documents only. How has Brand B's NPS trended since Wave 1?"

---

### Stage 6 — Hybrid BM25 + Embeddings (Demo Step 6)
> **Q12.** "What was the performance of Brand B's #CampusFirst UGC activation using micro-creator stack in metro markets Q4 2024?"  
*(Jargon-heavy: 'CampusFirst', 'UGC', 'micro-creator stack', 'metro' — hybrid outperforms pure vector)*

> **Q13.** "Find all documents about Brand B's #GenBGlobal campaign including OTT pre-roll strategy on Zomato and Swiggy."  
*(Campaign name + channel name + brand name — tests keyword + semantic combination)*

> **Q14.** "What is Brand A's out-of-stock rate on Blinkit and Zepto and how does it compare to Brand B?"  
*(Q-commerce brand names: Blinkit, Zepto — keyword match critical; semantic context from Category Trend CT002)*

---

### Stage 7 — MMR + Re-ranking — Show Coverage vs Repetition Tradeoff (Demo Step 7)
> **Q15.** "Compare Brand A versus Brand B across awareness, consideration, and price perception in India Urban 2024-2025."  
*(Should pull from 6+ sources: 3 tracker waves per brand + 2 competitor profiles — MMR prevents duplicating Wave 5 and Wave 6 tracker chunks)*

> **Q16.** "Summarize Brand B's competitive advantages using evidence from brand trackers, campaign data, and competitive profiles."  
*(Cross-document synthesis test — requires MMR to get diversity across 3 doc types)*

> **Q17.** "What are the five most distinct reasons consumers cite for preferring Brand B over Brand A?"  
*(Consumer reviews + social media + U&A study — MMR prevents all chunks coming from same source)*

---

### Stage 8 — HyDE / Query Rewriting (Demo Step 8)
> **Q18.** "What is going wrong with the brand?"  
*(Vague — HyDE should generate: 'Brand A declining Gen Z consideration urban India 2024 2025' as improved retrieval query)*

> **Q19.** "Is our brand in trouble?"  
*(HyDE expansion: needs to resolve 'our brand' + generate hypothesis document about brand decline)*

> **Q20.** "Tell me about the competitive situation."  
*(HyDE should generate more specific retrieval queries about market share, brand funnels, competitor moves)*

---

### Stage 9 — Answer Guardrails (Demo Step 9)
> **Q21.** "What is Brand A's EBITDA margin and P&L for 2024?"  
*(EXPECTED: "Insufficient Evidence" — financial data not in corpus. System must refuse to fabricate)*

> **Q22.** "What will Brand A's Gen Z consideration score be in 2026?"  
*(EXPECTED: System should flag this as forward-looking projection, not in evidence; cite current trajectory only)*

> **Q23.** "Which Brand A SKU has the highest sales volume?"  
*(EXPECTED: Partial evidence only — SKUs mentioned in reviews but no sales volume data in corpus)*

> **Q24.** "Compare Brand A and Brand B on TikTok engagement rates in 2024."  
*(EXPECTED: Insufficient evidence — TikTok data not present; should not hallucinate engagement numbers)*

---

### Stage 10 — Cross-Source Synthesis (Advanced)
> **Q25.** "Which brands are winning in SEA and what is the primary driver?"  
*(Sources: sea_brand_perception_2024.md + CP005 Brand E profile + CT004 sustainability trend)*

> **Q26.** "What strategic moves should Brand A make in the next 12 months based on all available evidence?"  
*(Full corpus synthesis — should cite U&A study recommendation, Campaign Eval weakness, KG signals, Category trends)*

> **Q27.** "Trace the full evidence chain for why Brand B is winning Gen Z — from structural category shift through to brand execution."  
*(Multi-hop: CT001 structural trend → CP002 Brand B attributes → CAMP003/004 campaign evidence → social proof in reviews/social)*

> **Q28.** "Compare Brand A's urban India performance to its SEA performance. Is there a consistent brand story?"  
*(Cross-market: india_urban_ua + sea_brand_perception — contrast awareness-to-consideration conversion gap in SEA vs India)*

---

### Stage 11 — Evaluation Metrics Demo
> **Q29.** "For the query 'Why is Brand A losing Gen Z share?', evaluate precision@5 — were the 5 retrieved chunks relevant?"  
*(Use EVAL001 ground truth: 8 relevant docs expected; score your system's top-5 retrieval)*

> **Q30.** "Show me a side-by-side of keyword vs hybrid retrieval results for Q5 (youth/college consumers) and measure recall."

---

## Retrieval Architecture Notes (for Demo Setup)

### Recommended Chunk Strategy

| Document Type | Chunk Unit | Overlap | Key Metadata to Attach |
|---------------|-----------|---------|------------------------|
| Brand Tracker (JSON) | One row per brand/market/wave | N/A | brand, market, date, wave, study_type |
| U&A Report (MD) | Section-level (H2) | 1 paragraph | brand, market, date, study_type, segment |
| Competitor Profile (JSON) | One record per brand | N/A | brand, as_of_date, market, category |
| Campaign Summary (JSON) | One record per campaign | N/A | brand, campaign_name, year, quarter, market |
| Consumer Reviews (JSON) | One review per chunk | N/A | brand, platform, date, sentiment, segment |
| Social Media (JSON) | One snippet per chunk | N/A | brand, platform, date, sentiment, tags |
| Category Trends (JSON) | One trend per chunk | N/A | category, market, date, tags, confidence |
| Analyst Notes (MD) | Paragraph-level | 1 sentence | brand, market, date, document_type |

### Synonym Vocabulary (for Query Expansion / HyDE)
```
Gen Z → youth, college consumers, under-25, metro millennials, young adults, 18-25
Brand B → the challenger, the rising brand
Q-commerce → quick commerce, 10-min delivery, Blinkit, Zepto, Swiggy Instamart
Micro-influencer → micro-creator, creator, nano-influencer
Consideration → top-of-mind, preference, shortlist
Awareness → salience, recall, recognition
```

### Evaluation Benchmark Usage

The `rag_evaluation_benchmark.json` contains 12 graded test cases. For each:
- `relevant_doc_ids`: ground truth document IDs that should appear in retrieval results
- `expected_sources_min`: minimum number of distinct sources needed for a good answer
- `insufficient_evidence_flag`: True = system should refuse/flag rather than answer
- `should_cite`: True = answer must include citations to pass faithfulness check

---

## Data Generation Notes

- Random seed: `42` — results are fully reproducible
- Brand names are anonymized (Brand A–E) for client-generic demo use; can be substituted for real brands in client-specific deployments
- Market names reflect real geography but data is entirely synthetic
- Regulatory and agency names (Nielsen, Kantar, IPSOS) are used as labels only — data values are simulated
- Tracker wave trends are deterministic: Brand A always declines, Brand B always rises in India Urban Gen Z — ensuring demo consistency

