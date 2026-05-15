# Multi-Agent Brand Health Monitoring & Insight Synthesis
## Synthetic Dataset Description & Demo Guide

**Project:** Project 4 — Multi-Agent Brand Health Monitoring & Insight Synthesis  
**Brand:** NovaBrew (fictional CPG beverage brand)  
**Dataset Version:** 1.0  
**Coverage:** 13 weeks (Q1 2025 — January 6 to March 31)  
**Domain:** Marketing Analytics; Brand Measurement; Campaign Analytics; Social Media Intelligence

---

## Overview

The NovaBrew universe: A fictional premium coffee pod brand tracked over 13 weeks (Q1 2025) across India Urban, UK, US, and SEA. Four competitors — CafePulse, BrewRush, ZenSip, BoltDrink. Four live campaigns.
9 signal folders.

This dataset simulates the full signal environment for a brand health monitoring system serving NovaBrew, a premium coffee pod and cold brew brand. It covers 6 signal types across 13 weekly periods, with 4 deliberate anomaly events that drive each specialist agent's reasoning and the synthesizer's weekly brief. The data is designed to demonstrate every stage of the progressive multi-agent demo — from single-LLM context overload through specialist decomposition, contradiction detection, HITL approval, and observability.

---

## Dataset Inventory

| File | Format | Records | Description |
|------|--------|---------|-------------|
| `social_listening/social_listening_weekly.json` | JSON | 78 | Weekly aggregates per platform: volume, sentiment, SOV, anomaly flags |
| `social_listening/social_listening_weekly.csv` | CSV | 78 | Same, tabular |
| `social_listening/social_posts_raw.json` | JSON | ~1,900 | Daily raw social posts with sentiment, text, platform, market, week |
| `social_listening/social_posts_raw.csv` | CSV | ~1,900 | Same, tabular |
| `search_trends/search_trends_weekly.json` | JSON | 156 | Weekly search index per keyword (12 keywords × 13 weeks) |
| `search_trends/search_trends_weekly.csv` | CSV | 156 | Same, tabular |
| `campaign_metrics/campaign_metrics_weekly.json` | JSON | 36 | Weekly campaign metrics (impressions, CTR, CPA, brand lift) per campaign |
| `campaign_metrics/campaign_metrics_weekly.csv` | CSV | 36 | Same, tabular |
| `campaign_metrics/campaign_definitions.json` | JSON | 4 | Campaign names, objectives, channels, date ranges, budgets |
| `campaign_metrics/campaign_definitions.csv` | CSV | 4 | Same, tabular |
| `review_exports/review_exports.json` | JSON | 390 | Weekly consumer reviews with rating, sentiment, SKU, theme tag |
| `review_exports/review_exports.csv` | CSV | 390 | Same, tabular |
| `competitor_news/competitor_news.json` | JSON | 8 | Competitor news snippets with impact, threat level, summary |
| `competitor_news/competitor_news.csv` | CSV | 8 | Same, tabular |
| `brand_tracker/brand_tracker_weekly.json` | JSON | 13 | Weekly brand funnel: awareness, consideration, NPS, SOV, equity index |
| `brand_tracker/brand_tracker_weekly.csv` | CSV | 13 | Same, tabular |
| `weekly_kpi_dashboard/weekly_kpi_dashboard.json` | JSON | 13 | Integrated KPI snapshot per week across all channels + health score |
| `weekly_kpi_dashboard/weekly_kpi_dashboard.csv` | CSV | 13 | Same, tabular |
| `agent_outputs/specialist_agent_evidence_cards.json` | JSON | 20 | Simulated specialist agent outputs for 4 key anomaly weeks × 5 agents |
| `agent_outputs/specialist_agent_evidence_cards.csv` | CSV | 20 | Same, tabular |
| `agent_outputs/synthesizer_brief_W11.json` | JSON | 1 | Full InsightSynthesizerAgent + CriticQA output for W11 (richest anomaly) |
| `agent_outputs/agent_trace_log.json` | JSON | 320 | Per-tool-call trace log: agent, tool, status, latency, tokens, cost |
| `agent_outputs/agent_trace_log.csv` | CSV | 320 | Same, tabular |
| `evaluation_set/agent_eval_benchmark.json` | JSON | 12 | Graded evaluation cases mapped to demo steps with expected findings |
| `evaluation_set/agent_eval_benchmark.csv` | CSV | 12 | Same, tabular |

**Total: 26 files across 9 folders**

---

## The NovaBrew Universe

**Brand:** NovaBrew — premium coffee pods, cold brew concentrate, and oat milk coffee blends  
**Markets:** India Urban (primary), UK, US, SEA  
**Competitors:** CafePulse, BrewRush, ZenSip, BoltDrink  
**Campaigns (Q1 2025):**
- `#MorningRush` (Paid Social — Reels/Instagram, W09–W12) — awareness + trial
- `PodSubscribe30` (Paid Search, W01–W13) — subscription conversion
- `InfluencerQ1` (Influencer, W01–W13) — consideration (uses @BrewMasterAlex)
- `ColdBrewLaunch` (OTT + Programmatic, W05–W10) — new product trial

**KPIs tracked:** Social sentiment, share of voice, branded search index, complaint search index, campaign CTR/CPA/brand lift, review rating, NPS, consideration, brand equity index, competitor SOV

---

## The Four Anomaly Events (Demo Drivers)

All data patterns are anchored to four deliberately seeded anomaly weeks. Each agent must detect, diagnose, and recommend — and the synthesizer + critic must resolve cross-agent contradictions.

### Anomaly 1 — Week 7 (W07): BrewRush Viral Campaign → SOV Drop
**What happened:** Competitor BrewRush launched #FuelYourDay TikTok campaign — 12M views in 48hrs. NovaBrew share of voice dropped -6pp. BrewRush running 25% subscription discount.

**Signal pattern across agents:**
- SocialListeningAgent: SOV 24.1% → 18.3%; positive sentiment intact (NOT a product issue)
- SearchTrendAgent: BrewRush search index doubled; NovaBrew stable; 'NovaBrew vs BrewRush' queries up 45%
- CampaignAgent: Paid metrics STABLE — campaign is performing; this is organic-only impact
- ReviewThemeAgent: Reviews stable — product quality not implicated
- CompetitorAgent: BrewRush Amazon rank #4→#2; 25% discount targeting NovaBrew subscribers

**KEY DEMO MOMENT:** CampaignAgent and SocialListeningAgent appear to contradict — social is negative but campaigns are fine. CriticQA resolves: it's a *channel bifurcation*, not a contradiction. Social is organic-driven; paid operates on search demand which is unaffected. This is the most important multi-agent insight vs. single-LLM demo point.

---

### Anomaly 2 — Week 9 (W09): #MorningRush Campaign Launch → Positive Surge
**What happened:** NovaBrew's #MorningRush campaign launched on Reels. All signals are positive.

**Signal pattern across agents:**
- SocialListeningAgent: Net sentiment +0.54 (highest Q1); SOV 29.1%; organic amplification
- SearchTrendAgent: Branded search index 89 (+86%); 'NovaBrew MorningRush' appears in rising queries
- CampaignAgent: Reels CTR 2.4x benchmark; brand lift +2.8pp awareness, +1.9pp consideration
- ReviewThemeAgent: Rating 4.4; new theme 'discovered via MorningRush ad' — campaign driving trial
- CompetitorAgent: CafePulse -12% price cut (potential demand interception); BrewRush winding down

**KEY DEMO MOMENT:** All 5 agents converge on positive anomaly. No contradictions. This week demonstrates the "amplify" use case: synthesizer should recommend budget reallocation to Reels. Good contrast to W11 crisis week.

---

### Anomaly 3 — Week 11 (W11): Quality Complaint Thread Goes Viral (PRIMARY DEMO WEEK)
**What happened:** Reddit thread on r/IndianCoffee (2,300 upvotes) claims NovaBrew Dark Roast Pods formula changed. Thread amplified on TikTok. Review volume 3x normal; average rating collapses to 2.9.

**Signal pattern across agents:**
- SocialListeningAgent: Net sentiment -0.04 (first negative week); 287% spike in negative mentions; Reddit + TikTok epicentre
- SearchTrendAgent: 'NovaBrew complaint' index 78 (was 9); 'NovaBrew alternative' up 89%
- CampaignAgent: Conversion rate -38% — but creative CTR strong → demand suppression, not creative failure
- ReviewThemeAgent: 68 reviews (3x normal); 48% are 1-2 star; ALL referencing Dark Roast Pods SKU specifically
- CompetitorAgent: BrewRush Cold Brew at 18% below NovaBrew price — launched same week

**KEY DEMO MOMENTS:**
1. ReviewThemeAgent isolates issue to ONE SKU — this is a supply chain / batch issue, not brand-wide
2. CampaignAgent correctly distinguishes demand suppression from creative failure
3. CompetitorAgent identifies opportunistic competitive flanking
4. CriticQA resolves the campaign CTR vs conversion rate apparent contradiction
5. Synthesizer produces 5-priority action brief with owners and SLAs
6. HITL: brand manager should edit "BrewRush timing appears deliberate" to descriptive language (MEDIUM confidence flag)

---

### Anomaly 4 — Week 12 (W12): Influencer Controversy → Compound Crisis
**What happened:** Accounts allege @BrewMasterAlex (NovaBrew's lead influencer in InfluencerQ1 campaign) doesn't actually use NovaBrew. Controversy goes viral compounding W11 quality concerns.

**Signal pattern across agents:**
- SocialListeningAgent: Net sentiment -0.11 (all-time low); TikTok alleging paid promotion inauthenticity; 4.2M negative impression reach
- SearchTrendAgent: 'NovaBrew influencer fake' in rising queries; branded demand continues to decline
- CampaignAgent: InfluencerQ1 @BrewMasterAlex CPE +340%; #MorningRush CTR -28% (halo effect)
- ReviewThemeAgent: 'influencer ad was misleading' appears as new review theme — cross-channel contamination
- CompetitorAgent: Competitors staying quiet, letting crisis play out; ZenSip Swiggy launch confirmed W14

The synthesizer_brief_W11.json is a fully hand-crafted gold-standard executive output for W11 — including contradiction resolutions, confidence labels per claim, 5-priority action list with owners and SLAs, HITL pending flag, and agent trace cost summary. Use it to compare live agent output against, or as the "reveal" in the demo.

**KEY DEMO MOMENT:** Cross-channel contamination — influencer controversy is now showing up in *reviews*, not just social. The synthesizer must diagnose a compound crisis and recommend a unified brand response (not separate responses to each issue). HITL approval is critical here — do not let AI auto-send any brand communications.

---

## Agent Architecture Reference

| Agent | Signal Sources | Key Tool Calls | Output Format |
|-------|---------------|----------------|---------------|
| SocialListeningAgent | social_posts_raw, social_listening_weekly | fetch_social_data, sentiment_aggregator | Evidence card: sentiment, SOV, themes, anomaly |
| SearchTrendAgent | search_trends_weekly | get_search_trends, keyword_classifier | Evidence card: indices, rising queries, anomaly |
| CampaignAgent | campaign_metrics_weekly, campaign_definitions | query_campaign_db, brand_lift_fetch | Evidence card: KPIs, efficiency, anomaly |
| ReviewThemeAgent | review_exports | fetch_reviews, theme_extractor | Evidence card: rating, themes, SKU flags, anomaly |
| CompetitorAgent | competitor_news, brand_tracker | get_competitor_news, sov_compare | Evidence card: threats, SOV delta, recommendation |
| InsightSynthesizerAgent | All 5 evidence cards | call_synthesizer, retrieve_kpi_dashboard | Executive brief with citations |
| CriticQAAgent | Synthesizer brief + all evidence cards | run_critic_check, contradiction_detector | QA findings, confidence by claim, flags |

---

## Demo Step ↔ Dataset Mapping

| Step | What to Show | Key Files |
|------|-------------|-----------|
| 1 | Executive question framing | `weekly_kpi_dashboard.json` — W11 row |
| 2 | Single LLM baseline failure | All 5 signal CSVs fed as one prompt; show context overload vs multi-agent |
| 3 | Sequential ingest workflow | Load weekly_kpi_dashboard → show organization but no specialist reasoning |
| 4 | Specialist agents + evidence cards | `specialist_agent_evidence_cards.json` — W11 entries for all 5 agents |
| 5 | Targeted agent questions | Individual agent evidence cards for W07, W09, W11, W12 |
| 6 | Synthesizer narrative | `synthesizer_brief_W11.json` — executive_summary + key_findings_by_agent |
| 7 | Critic/QA + contradiction detection | `synthesizer_brief_W11.json` — contradictions_identified + critic_qa_findings |
| 8 | HITL approval | `synthesizer_brief_W11.json` — hitl_status field; show BrewRush confidence edit |
| 9 | Observability | `agent_trace_log.json` — filter by week=2025-W11; show failed calls, latency, cost |
| 10 | Limitations | `agent_outputs/` — failed tool calls in trace; synthetic data caveats |
| 11 | Future scope | KPI dashboard + brand tracker — show what real-time streaming would add |

---

## Demo Questions — By Stage

### Stage 1 — Framing the Executive Question
> **Q1.** "What changed in NovaBrew brand health this week and what should marketing do?"

> **Q2.** "Give me the headline KPIs for NovaBrew in Week 11 across social, search, campaigns, reviews, and competitors."

> **Q3.** "How does Week 11 compare to Week 9 (our campaign launch week) on the same KPIs?"

---

### Stage 2 — Single LLM Failure (Show the Baseline Problem)
> **Q4.** [Feed all 5 signal CSVs in one prompt] "Summarize NovaBrew brand health for Week 11 and recommend actions."
*(Expect: generic crisis language, misses SKU-specific signal, misses campaign CTR vs conversion nuance, no citations, treats all negatives as equally urgent)*

> **Q5.** "What is wrong with using a single LLM for this task? What signals did it miss or conflate?"
*(Expected answer: context overload; no specialist reasoning on channel mechanics; cannot resolve contradictions; no traceability)*

---

### Stage 3 — Sequential Workflow (Organized but Shallow)
> **Q6.** "Ingest social, reviews, search, and campaign data in sequence and produce a summary."
*(Show: organized output, better structure — but ReviewThemeAgent's SKU-specific insight still missing; no contradiction check)*

---

### Stage 4 — Specialist Agents: Evidence Cards (Demo Step 4)
> **Q7.** "Social Listening Agent — what negative themes spiked this week and is this a product issue or a competitive issue?"  
*(Expected: Reddit viral thread, Dark Roast Pods specific, NOT a general brand issue)*

> **Q8.** "Search Trend Agent — what keyword signals changed this week? Are any complaint keywords crossing into the decision stage?"  
*(Expected: 'NovaBrew complaint' index 78, 'NovaBrew alternative' up 89% — yes, decision stage impact)*

> **Q9.** "Campaign Agent — did the campaign move consideration this week? If conversion dropped, is it a creative problem?"  
*(Expected: creative CTR is strong; conversion dropped due to demand suppression — NOT a creative failure)*

> **Q10.** "Review Theme Agent — what does the review data reveal that social listening alone cannot?"  
*(Expected: SKU-specific — ALL complaints reference Dark Roast Pods. Batch issue, not brand-wide. 9 reviews mention switching to BrewRush.)*

> **Q11.** "Competitor Agent — what did BrewRush do this week and is the timing significant?"  
*(Expected: Cold Brew launch at 18% below NovaBrew — same week as quality crisis. MEDIUM confidence on deliberate timing.)*

---

### Stage 5 — Targeted Agent Questions (Demo Step 5)
> **Q12.** "Social Agent — going back to Week 7: was the SOV drop caused by a product problem or a competitor campaign?"  
*(Expected: purely competitive — product quality reviews were stable that week)*

> **Q13.** "Campaign Agent — in Week 9, which channel and creative format drove the highest brand lift?"  
*(Expected: Paid Social / Instagram Reels — 2.4x benchmark CTR, +2.8pp awareness lift)*

> **Q14.** "Review Theme Agent — across all 13 weeks, which SKU has the highest concentration of 1-2 star reviews?"  
*(Expected: Dark Roast Pods — concentrated in W11-W12)*

> **Q15.** "Search Trend Agent — at what point did complaint-related search volume become large enough to suppress branded conversion?"  
*(Expected: W11 — complaint search index crossed 70, at which point branded purchase intent search dropped)*

---

### Stage 6 — Insight Synthesizer (Demo Step 6)
> **Q16.** "Synthesize all 5 agent evidence cards for Week 11 into an executive-ready brand health brief."  
*(Expected: synthesizer_brief_W11.json executive_summary — SKU-specific diagnosis, competitor flanking, 5-priority actions)*

> **Q17.** "What is the single most important finding from Week 11 that requires immediate action in the next 24 hours?"  
*(Expected: Dark Roast Pods quality complaint — SKU escalation to QA and supply chain)*

> **Q18.** "Contrast the Week 11 brief with the Week 9 brief — what should marketing have done differently between weeks 9 and 11?"  
*(Expected: W09 was amplify moment; W11 should have triggered monitoring alerts earlier via review rating trajectory)*

---

### Stage 7 — Critic/QA Agent (Demo Step 7)
> **Q19.** "Does the synthesizer's claim that 'BrewRush timing appears deliberate' have strong evidence?"  
*(Expected: Critic flags as MEDIUM confidence — circumstantial timing; recommend softening language for executive brief)*

> **Q20.** "Do the Campaign Agent and Social Listening Agent contradict each other in Week 11? If so, resolve it."  
*(Expected: No true contradiction — campaign CTR fine (creative works) but conversion dropped (demand suppressed). Channel bifurcation insight.)*

> **Q21.** "Which of the synthesizer's Week 11 recommendations are fully evidence-backed and which need caveating?"  
*(Expected: 8/9 claims supported; root cause of formula change is NOT in corpus — needs QA investigation flag)*

> **Q22.** "Run a source quality check — which agent evidence cards for Week 11 have the highest and lowest confidence?"  
*(Expected: SocialListeningAgent, SearchTrendAgent, ReviewThemeAgent all HIGH. CompetitorAgent MEDIUM on BrewRush intent. Agent trace shows 2 failed tool calls.)*

---

### Stage 8 — HITL Approval (Demo Step 8)
> **Q23.** "[Brand Manager] Review this brief. The claim 'BrewRush timing appears deliberate' — should this go to the CMO?"  
*(Expected HITL edit: change to 'BrewRush Cold Brew launch coincided with NovaBrew quality complaints this week' — descriptive, not causal)*

> **Q24.** "[Brand Manager] The brief recommends pausing all paid media. Is that the right call given #MorningRush was performing well in Week 9?"  
*(Expected nuance: pause boosting of InfluencerQ1 and performance campaigns; maintain #MorningRush creative on lower budget to preserve equity)*

> **Q25.** "Which insights in the Week 11 brief would you mark as 'weak' or requiring more data before acting?"  
*(Expected: (1) Root cause of formula change — needs supply chain input; (2) Consumer intent to switch — review mentions are not panel data)*

---

### Stage 9 — Observability (Demo Step 9)
> **Q26.** "Show me the agent trace for Week 11. How many tool calls were made, which failed, and what was the total cost?"  
*(Expected: 31 tool calls, 2 failures (6.5% failure rate), $0.84 total cost, 42.3 seconds)*

> **Q27.** "Compare the cost and latency of the multi-agent run vs a single LLM for Week 11. What is the trade-off?"  
*(Expected: Single LLM: ~$0.12, 8 sec. Multi-agent: $0.84, 42 sec. Trade-off: 7x cost for SKU-specific diagnosis, contradiction detection, and cited brief)*

> **Q28.** "Which agent had the highest failure rate in tool calls and what was the impact on the brief?"  
*(Expected: From trace log — identify which agent's tool calls failed; assess whether synthesizer had to proceed with partial data)*

> **Q29.** "Set up an alert: if the 'NovaBrew complaint' search index exceeds 50 in any week, trigger an immediate CriticQA review."  
*(Expected: Search trend anomaly detection logic — week 11 would have triggered this alert in W10 with index at 65, giving 1-week earlier warning)*

---

### Stage 10 — Limitations Discussion
> **Q30.** "The agents identified a quality complaint — but can they determine whether the formula actually changed?"  
*(Expected: No — agents only see consumer signals, not supply chain or QA data. Root cause requires human investigation.)*

> **Q31.** "If the social listening API failed in Week 11, what would the multi-agent system have missed?"  
*(Expected: SOV drop, complaint virality, Reddit thread — the primary signal. Search and reviews would partially compensate but the velocity of the social signal is critical.)*

> **Q32.** "How would the multi-agent system handle a week where all 5 agents produce conflicting signals?"  
*(Expected: CriticQA escalates to HITL rather than auto-publishing — the contradiction threshold triggers mandatory human review)*

---

### Stage 11 — Future Scope
> **Q33.** "How would you extend this system to provide 24-hour anomaly alerts rather than weekly briefs?"  
*(Expected: Real-time streaming from social APIs; alert thresholds on complaint search index, sentiment net score, review rating drop)*

> **Q34.** "If we integrated MMM (Marketing Mix Modeling) data, how would the Campaign Agent's diagnosis of Week 11 change?"  
*(Expected: MMM would provide causal attribution between search demand suppression and conversion drop — replacing the agent's inference with a measured causal estimate)*

---

## Data Patterns Reference Table

| Week | Anomaly Type | Social Signal | Search Signal | Campaign Signal | Review Signal | Competitor Signal | Correct Diagnosis |
|------|-------------|---------------|---------------|-----------------|---------------|-------------------|-------------------|
| W07 | SOV Drop — Competitive | SOV -6pp; sentiment stable | BrewRush search +100% | Paid metrics STABLE | Reviews stable | BrewRush viral | Competitive, not product |
| W09 | Campaign Surge — Positive | SOV +5pp; sentiment peak | Branded search +86% | CTR 2.4x; lift +2.8pp | Rating 4.4; trial mentions | CafePulse -12% price | Amplify — all signals green |
| W11 | Quality Complaint Viral | Net sentiment negative (-0.04) | Complaint index 78 | CTR fine; conversion -38% | Rating 2.9; 68 reviews; Dark Roast SKU | BrewRush Cold Brew launch | SKU crisis + competitive flanking |
| W12 | Influencer Controversy | Sentiment -0.11 (all-time low) | 'Influencer fake' rising | InfluencerQ1 CPE +340% | 'Misleading ad' theme in reviews | Competitors watching | Compound crisis — unified response needed |

---

## Generation Notes

- Random seeds: `42` (Part 1), `99` (Part 2), `7` (Part 3) — reproducible
- Brand name "NovaBrew" and competitors are fully fictional
- Anomaly weeks are deterministic — W07, W09, W11, W12 always show the described patterns
- `synthesizer_brief_W11.json` is a fully hand-crafted gold-standard output — use it to compare against live agent output
- `agent_trace_log.json` simulates realistic tool-call failure rates (8%) and latency variance for observability demo
- All financial values (spend, CPA, cost) are illustrative and scaled for demo clarity

