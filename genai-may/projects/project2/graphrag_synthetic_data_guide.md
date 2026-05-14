# GraphRAG Demo — Synthetic Data Guide

## Domain Overview

The dataset models a fictional **Indian children's nutrition supplement market** with four competing brands across four consumer segments. Every pattern is designed to make graph traversal *demonstrably* superior to vector-only retrieval — each key insight requires connecting nodes across at least three hops.

| Brand | Positioning | Primary Segment |
|---|---|---|
| **NutriKids** | Premium / Market Leader (eroding) | ValueParents, HealthConscious |
| **FreshStart** | Value-for-money (gaining fast) | ValueParents |
| **VitaPlus** | Science-backed premium | HealthConscious, SeniorWellness |
| **QuickNutrish** | Convenience-first D2C | BusyProfessional |

| Segment | Market Size | Primary Channel | Top Purchase Driver |
|---|---|---|---|
| **ValueParents** | 38.2% | Supermarket | Price |
| **HealthConscious** | 22.7% | Pharmacy | Ingredient transparency |
| **BusyProfessional** | 19.4% | Online D2C | Convenience |
| **SeniorWellness** | 19.7% | Pharmacy | Doctor recommendation |

---

## File Inventory — 16 Files across 10 Folders

### 1. `customer_feedback/customer_feedback.csv`
**Format:** CSV | **Rows:** 25 feedback records

Survey responses from real-purchase customers across all four brands and segments. Each row captures brand mentions, competitor mentions, sentiment, NPS score, purchase driver, and a free-text verbatim.

**Key patterns embedded:**
- 14 of 25 records show a brand switch (10 to FreshStart, 3 to VitaPlus, 1 to QuickNutrish)
- NutriKids complaints cluster around `price`, `packaging`, and `shrinkflation`
- FreshStart gains driven by `price + taste + packaging + doctor_recommendation` in combination
- VitaPlus gains in `HealthConscious` driven by `ingredient_quality` and `doctor_recommendation`
- QuickNutrish gains in `BusyProfessional` driven by `convenience` and `subscription`

**Columns:** `feedback_id`, `customer_id`, `segment`, `age_group`, `channel`, `date`, `brand_mentioned`, `product_mentioned`, `competitor_mentioned`, `sentiment`, `rating`, `feedback_text`, `nps_score`, `purchase_driver`, `complaint_type`

---

### 2. `product_catalog/product_catalog.json`
**Format:** JSON | **Brands:** 4 | **Products:** 6

Full product master with canonical names, aliases, ingredients, pricing, certifications, and scored attributes. Structured to support both entity resolution (via aliases) and attribute comparison queries.

**Key patterns embedded:**
- Each product has 4–7 **alias variants** (e.g. `NutriKids GrowPack` → `NutriKid`, `NK GrowPack`, `Grow Pack 500g`, `NK-GP`) for the entity resolution demo
- NutriKids ProFormula explicitly lists `Acesulfame K`, `Carrageenan`, `Artificial Vanilla Flavour` — the three additives HealthConscious parents reject
- VitaPlus OmegaBlend lists zero artificial additives and three certifications (FSSAI, USDA Organic, Non-GMO)
- NutriKids GrowPack `recent_changes` field documents the January 2024 price hike and the undisclosed portion reduction (shrinkflation)
- Attribute scores enable quantitative comparisons: `packaging_ease` (NutriKids 2.9 vs FreshStart 4.4), `doctor_recommendation_rate` (VitaPlus 0.72 vs NutriKids 0.28)

---

### 3. `competitor_profiles/competitor_intelligence.json`
**Format:** JSON | **Competitors:** 3

Competitive intelligence report covering market share trends (Q1 2023 → Q1 2024), key winning attributes, recent strategic moves, and switching drivers from NutriKids.

**Key patterns embedded:**
- FreshStart: 40.5% YoY growth rate; share in ValueParents rose from 13.1% → 18.4% overall
- VitaPlus: 31.3% YoY growth; dominates HealthConscious (38.9%) and SeniorWellness (42.1%)
- QuickNutrish: 200% YoY growth (from low base); BusyProfessional share at 28.4%
- Each competitor's `recent_moves` array captures 2–3 dated strategic actions with impact quantification
- `switching_drivers_from_NutriKids` field directly surfaces the causal chain for graph loading

---

### 4. `campaign_metadata/campaign_metadata.csv`
**Format:** CSV | **Rows:** 10 campaign records

Marketing and trade campaign history across all four brands, with budget, channel, segment target, conversion rate, and qualitative outcome notes.

**Key patterns embedded:**
- FreshStart PricePromise (CAM003): 7.2% conversion — highest among trade promotions; explicitly confirms NutriKids customer acquisition
- FreshStart MommyCircle (CAM010): 14.1% conversion at only INR 35 lakhs — demonstrates community-driven efficiency
- VitaPlus ScienceFirst (CAM005): +22pp premium consideration in HealthConscious via content marketing
- NutriKids IngredientTrust (CAM009): Only +8pp — underperformed because artificial additives were not reformulated
- QuickNutrish SubscriptionFirst (CAM007): 9.1% conversion + 68% subscriber signup rate

**Columns:** `campaign_id`, `campaign_name`, `brand`, `product`, `target_segment`, `channel`, `start_date`, `end_date`, `budget_lakhs_inr`, `campaign_type`, `message_theme`, `kpi_primary`, `kpi_value_achieved`, `reach_thousands`, `conversion_rate_pct`, `outcome_notes`

---

### 5. `ecommerce_reviews/ecommerce_reviews.json`
**Format:** JSON | **Reviews:** 10

Amazon India, Flipkart, 1mg, and PharmEasy reviews with pre-tagged NER entities and extracted relationships. Simulates the output of a real review scrape + NER pipeline.

**Key patterns embedded:**
- Each review includes `canonical_brand` and `canonical_product` fields alongside `brand_raw` / `product_name_raw` to demonstrate alias normalisation
- `entities_extracted` block shows tagged brands, products, attributes, segments, and complaints
- `relationships_extracted` block shows directed relationships ready for graph loading
- REV006 (Flipkart) is the shrinkflation detection review — 456 helpful votes, explicitly weighs 920g vs 1kg
- REV009 confirms QuickNutrish subscription loyalty and peer referral conversion in BusyProfessional

---

### 6. `social_listening/social_listening_themes.csv`
**Format:** CSV | **Rows:** 10 aggregated theme records

Social listening themes aggregated from Twitter, Facebook mommy groups, Instagram, LinkedIn, and WhatsApp, with volume, average sentiment, top keywords, and three example verbatims per theme.

**Key patterns embedded:**
- SL001 (NutriKids price shock): 8,420 mentions, sentiment 0.21 — largest negative volume in dataset
- SL009 (FreshStart Mommy Network Effect): 9,810 mentions, sentiment 0.81 — largest positive volume
- SL008 (Artificial Additives Concern): 4,120 mentions linked to NutriKids ProFormula specifically
- SL010 (Price vs Quality Debate): Mixed sentiment (0.51) — represents the undecided consideration stage
- `need_state` and `action_signal` columns map directly to graph NeedState nodes

**Columns:** `theme_id`, `theme_name`, `brand_mentioned`, `segment_cluster`, `channel_source`, `date_range`, `volume_mentions`, `sentiment_avg`, `top_keywords`, `sub_themes`, `example_verbatim_1/2/3`, `associated_competitors`, `need_state`, `action_signal`

---

### 7. `segmentation_summaries/segmentation_report.json`
**Format:** JSON | **Segments:** 4

Full segment profiles from a mixed-method study (quant survey n=4,200 + 48 IDIs + 12 ethnographic observations). Includes demographics, psychographics, ranked purchase drivers, unmet needs, brand preferences, channel preferences, and a strategic trajectory note.

**Key patterns embedded:**
- Each segment's `purchase_drivers_ranked` array uses `importance_score` (1–5) — directly loadable as `DRIVEN_BY` relationship weights
- `brand_switching_intent_12months` captures switch rate and primary trigger per segment
- `unmet_needs` array surfaces verbatim insight statements for the strategy layer
- SeniorWellness segment: 0.8% NutriKids share and 1.2% FreshStart share — complete absence, no competition for VitaPlus
- `segment_trajectory` field provides the narrative that stitches together individual data points

---

### 8. `segmentation_summaries/survey_raw_responses.csv`
**Format:** CSV | **Rows:** 20 individual survey responses

Raw survey responses at the individual respondent level, including Likert scale scores for six attributes and a free-text field. Designed for the NER extraction and entity resolution demo steps.

**Key patterns embedded:**
- 13 of 20 respondents report a brand switch in the last 6 months
- Free-text `free_text_response` column contains informal brand name variants (e.g. "NK", "Fresh Start", "Vita Plus") for entity resolution demo
- Purchase driver columns are pre-coded but free text shows the human language behind the codes
- Respondents R011 and R012 are SeniorWellness — explicitly document the VitaPlus SeniorCare journey from generic pharmacy brands

**Columns:** `respondent_id`, `age`, `gender`, `city`, `tier`, `household_income_band`, `children_count`, `occupation`, `primary_supplement_brand_q1`, `purchase_channel_primary`, `switch_in_last_6months`, `switch_from`, `switch_to`, `switch_reason_main`, `purchase_driver_1st/2nd/3rd`, `nps_current_brand`, `q_price_sensitivity` through `q_convenience_importance` (Likert 1–5), `free_text_response`

---

### 9. `market_research/market_research_report_Q1_2024.txt`
**Format:** Plain text | **Length:** ~191 lines

Full-length analyst market research report structured as a real deliverable with sections, findings, supporting data, IDI verbatim quotes, and strategic implications. Designed for vector RAG chunking — each section is self-contained enough to be retrieved as a chunk, but the strategic insight requires connecting across sections.

**Key patterns embedded:**
- Section 1: ValueParents + FreshStart + price/packaging/promotion — with two IDI verbatims confirming the shrinkflation detection
- Section 2: HealthConscious + VitaPlus + clean label + additives — with one IDI verbatim from a paediatrician visit
- Section 3: SeniorWellness + VitaPlus SeniorCare — uncontested new category
- Section 4: BusyProfessional + QuickNutrish — subscription moat quantified
- Section 5: Cross-segment relationship matrix — the key section that vector RAG alone cannot synthesise
- Section 6: Strategic implications for NutriKids — three prioritised action areas

---

### 10. `market_research/market_research_snippets.txt`
**Format:** Plain text | **Snippets:** 15

Short, labelled research snippets (MRS-001 to MRS-015) from Nielsen retail audit, IQVIA pharmacy panel, conjoint analysis, shopper observation, D2C benchmarking, social commerce, and clinical evidence studies. Each snippet is 5–10 lines, ideal for demonstrating RAG chunking and retrieval.

**Key patterns embedded:**
- MRS-003: Shrinkflation detection rate (38%) and post-detection switching funnel (71% switched within 90 days)
- MRS-005: Price elasticity contrast — ValueParents at -2.8 (elastic) vs HealthConscious at -0.6 (inelastic)
- MRS-008: WhatsApp group influence study — 67% of ValueParents switched following a group recommendation
- MRS-013: Full switching funnel with conversion rates at each stage (Awareness 74% → Full Switch 44%)
- MRS-015: Three future signals including temporal graph shifts, community-driven commerce, subscription as moat

---

### 11. `graph_schema/graph_schema.json`
**Format:** JSON | **Node types:** 11 | **Relationship types:** 17

Complete graph schema definition with property lists, examples, and Cypher-style relationship syntax for every node and edge type in the knowledge graph.

**Node types:** `CustomerSegment`, `Brand`, `Product`, `Competitor`, `NeedState`, `ReviewTheme`, `Channel`, `Campaign`, `Attribute`, `Study`, `Insight`

**Key relationship types:**

| Relationship | From → To | Key Properties |
|---|---|---|
| `BELONGS_TO` | Product → Brand | — |
| `TARGETS_SEGMENT` | Product → CustomerSegment | `primary`, `market_share_pct` |
| `PREFERS` | CustomerSegment → Product | `share_pct`, `trend`, `primary_driver` |
| `DRIVEN_BY` | CustomerSegment → NeedState | `rank`, `importance_score` |
| `SATISFIED_BY` | NeedState → Product | `satisfaction_score` |
| `SWITCHES_TO` | CustomerSegment → Competitor | `switch_rate_pct`, `primary_trigger` |
| `WINS_ON` | Competitor → Attribute | `in_segment`, `score` |
| `LOSING_ON` | Brand → Attribute | `in_segment`, `score`, `trend` |
| `DISTRIBUTED_IN` | Product → Channel | `strength` |
| `MENTIONS` | ReviewTheme → Brand | `sentiment`, `volume` |
| `COMPETES_WITH` | Brand → Competitor | `segment_contested`, `share_gap_pp` |

---

### 12. `graph_schema/neo4j_graph_loader.py`
**Format:** Python script

Ready-to-run Neo4j loader with all node data (as Python lists of dicts) and relationship loading functions. Uses `MERGE` throughout to make it idempotent.

**Nodes loaded:** CustomerSegment (4), Brand (4), Product (6), NeedState (10), ReviewTheme (10), Channel (5), Attribute (12), Campaign (7)

**Relationships loaded:** `BELONGS_TO`, `DRIVEN_BY`, `PREFERS`, `SWITCHES_TO`, `WINS_ON`, `DISTRIBUTED_IN`, `MENTIONS`

**Usage:**
```bash
pip install neo4j
# Update NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD at top of file
python neo4j_graph_loader.py
```

---

### 13. `graph_schema/entity_resolution_mapping.csv`
**Format:** CSV | **Rows:** 42 alias mappings

Maps every real-world alias variant found across data sources to its canonical entity name. Includes the resolution method, source, and confidence score.

**Key patterns embedded:**
- 17 brand alias variants across 4 brands (e.g. `NK`, `Nutri Kids`, `NutriKid`, `NutriKids India` → `NutriKids`)
- 25 product alias variants across 6 products (e.g. `GrowPack 500g`, `NK-GP`, `NutriKids Grow Pack` → `NutriKids GrowPack`)
- Resolution methods: `whitespace_normalization`, `abbreviation_expansion`, `suffix_stripping`, `punctuation_normalization`, `code_expansion`, `brand_context_inference`
- Confidence scores range from 0.78 (ambiguous abbreviation) to 0.99 (whitespace only)

**Columns:** `raw_mention`, `canonical_entity`, `entity_type`, `source`, `confidence`, `resolution_method`, `resolution_note`

---

### 14. `graph_schema/ner_extraction_results.json`
**Format:** JSON | **Documents processed (sample shown):** 5

Simulated output of an NER + relationship extraction pipeline run on reviews, survey responses, and report excerpts. Shows both successful extractions and documented failure modes.

**Key patterns embedded:**
- Each result includes character-level `span` positions, confidence scores, and `canonical` resolved entity
- `relationships_extracted` block with directed triples (from → relation → to) and confidence
- `extraction_errors` block documents real failure modes: ambiguous product names, segment inference gap, negation handling, relationship direction ambiguity
- Aggregate stats: entity F1 = 0.83, relationship precision = 0.81 — realistic for a real pipeline
- REV003 (VitaPlus neurologist review) demonstrates multi-entity, multi-relationship extraction from a single sentence

---

### 15. `graph_schema/graphrag_vs_vectorrag_comparison.json`
**Format:** JSON | **Questions compared:** 3

Side-by-side comparison of Vector RAG vs GraphRAG answers for three demo questions, with retrieved chunks, answer text, quality scores, and failure mode analysis.

**Questions covered:**

| # | Question | Hops Required |
|---|---|---|
| Q1 | Which competitor is gaining among value-conscious parents, and what attributes drive the shift? | 4 |
| Q2 | Which unmet need connects price, packaging, and switching complaints? | 5 |
| Q3 | Show the evidence chain for why VitaPlus is winning in HealthConscious | 4 |

**Summary metrics:**

| Metric | Vector RAG | GraphRAG |
|---|---|---|
| Avg completeness | 0.37 | 0.96 |
| Relationship coverage | 0.21 | 0.92 |
| Evidence chains provided | 0/3 | 3/3 |
| Analyst usefulness (1–5) | 2.1 | 4.7 |

---

### 16. `cypher_queries/graphrag_demo_queries.cypher`
**Format:** Cypher | **Queries:** 11

Annotated Cypher queries for every major demo question, from basic graph traversal to shortest-path explainability and temporal share movement.

| Query | Purpose |
|---|---|
| Q1 | Core GraphRAG demo — segment → competitor → winning attributes |
| Q2 | Evidence chain path — full 4-hop causal path with document citations |
| Q3 | Unmet need inference — connecting multiple complaint types to a single NeedState |
| Q4 | Full Segment-Competitor-Attribute-Channel path |
| Q5 | Brand share by segment and channel |
| Q6 | Doctor recommendation network effect |
| Q7 | Entity resolution check — canonical name and all aliases |
| Q8 | Review theme to strategy path |
| Q9 | GraphRAG vs Vector-RAG demo — relationship-heavy query (key demo moment) |
| Q10 | Temporal market share movement |
| Q11 | Shortest path between complaint and competitor gain (explainability) |

---

## Key Demo Patterns — Quick Reference

### Pattern 1: Multi-complaint → Single NeedState (Q2 demo)
Three separate complaint clusters (price frustration, packaging usability, shrinkflation detection) all point to a single NeedState node: **`affordable_honest_value`**. This is invisible to vector RAG (which sees three separate chunks) but obvious as a graph traversal (three ReviewTheme nodes, same NeedState target).

### Pattern 2: Segment-Channel-Competitor Alignment (Q1 demo)
FreshStart wins ValueParents specifically through **Supermarket** (52% of ValueParents' preferred channel) via BOGOF promotion. Vector RAG retrieves facts about FreshStart winning and supermarket promotions separately — graph traversal connects `Segment → Channel Preference → Campaign → Competitor → Attributes` in one path.

### Pattern 3: Segment × Purchase Driver × Product Alignment (Q3 demo)
VitaPlus OmegaBlend scores highest on the top 3 purchase drivers of HealthConscious (ingredient transparency, clinical evidence, doctor trust) — all three are graph edges with quantified weights. NutriKids ProFormula scores lowest. The graph makes this alignment instantly traversable.

### Pattern 4: Entity Resolution (Alias → Canonical)
42 alias variants across brands and products. `NK`, `NutriKid`, `Nutri Kids`, `Nutri-Kids`, `NutriKids India` all resolve to `NutriKids`. Same for products: `GrowPack`, `NK-GP`, `Grow Pack 500g` → `NutriKids GrowPack`. Needed before any graph loading step.

### Pattern 5: Subscription as Competitive Moat
QuickNutrish subscription data (70% subscriber rate, 8% churn vs 22% industry) quantifies lock-in. Contrasted with NutriKids (12% subscription rate, 26% churn). The moat is a graph property of the BusyProfessional → QuickNutrish → subscription_model path.

---

## How Files Map to Demo Steps

| Demo Step | Files Used |
|---|---|
| 1. Problem framing | `market_research_report_Q1_2024.txt` |
| 2. Data ingestion overview | All source files (6 source types) |
| 3. NER extraction | `customer_feedback.csv`, `ecommerce_reviews.json`, `survey_raw_responses.csv`, `market_research_snippets.txt` |
| 4. Entity resolution | `entity_resolution_mapping.csv`, `product_catalog.json` (aliases) |
| 5. Graph schema design | `graph_schema.json` |
| 6. Graph loading | `neo4j_graph_loader.py` |
| 7. Cypher queries | `graphrag_demo_queries.cypher` |
| 8. GraphRAG vs Vector RAG | `graphrag_vs_vectorrag_comparison.json` |
| 9. NER pipeline internals | `ner_extraction_results.json` |
| 10. Strategic insight output | `segmentation_report.json`, `competitor_intelligence.json` |
