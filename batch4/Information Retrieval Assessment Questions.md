# Information Retrieval — Assessment Questions & Answers

> **Grading guide**
> - **Core** questions (Q1, Q4, Q6, Q9, Q11) — answerable from close reading of the demo code and comments
> - **Math** questions (Q2, Q5, Q7) — require understanding the algorithm's mathematics, not just its output
> - **Stretch** questions (Q3, Q8, Q10, Q12) — require reasoning beyond what the demos show; test whether participants thought critically about stated limitations

---

## Demo 1 — TF-IDF · [`01_tfidf_demo.py`](01_tfidf_demo.py)

### Q1 · Core

In Demo 1, Query Q2 asks `"heart attack treatment aspirin antiplatelet"` but the most relevant document uses the terms `"myocardial infarction"` and `"STEMI"`. The demo notes this as a "vocabulary gap." Given that `TfidfVectorizer` is configured with `ngram_range=(1,2)`, would adding trigrams (`ngram_range=(1,3)`) fix this problem? Why or why not?

> **A1**
>
> No. The problem is not phrase granularity — it is that `"heart attack"` and `"myocardial infarction"` are entirely different character sequences. TF-IDF is a bag-of-words model: it treats each term as an atomic symbol with no semantic relationship to any other. The bigram `"myocardial infarction"` and the bigram `"heart attack"` occupy two separate dimensions in the vocabulary, and their cosine similarity is exactly zero unless both appear in the same document.
>
> Trigrams would only help if a phrase like `"heart attack myocardial"` bridged the two terms in a document — which never happens in natural clinical text. The fix requires either:
> - **Query expansion** using a medical ontology (UMLS, SNOMED CT) to rewrite `"heart attack"` → `"myocardial infarction OR STEMI OR ACS"`, or
> - **Dense retrieval** (Demo 3), where the encoder has learned that both phrases map to nearby vectors in embedding space.

---

### Q2 · Core

The demo runs `show_idf_analysis()` and prints the terms with the lowest and highest IDF scores. Explain what it means for a medical term like `"patient"` to have a *low* IDF in this corpus, and what it means for `"semaglutide"` to have a *high* IDF. Then explain: if 50 new documents about semaglutide were added to the corpus, what happens to semaglutide's IDF?

> **A2**
>
> **Low IDF for `"patient"`:** `IDF = log(N / df(t))`. If `"patient"` appears in all 30 documents, then `df = N = 30`, so `IDF = log(1) = 0`. The term contributes nothing to any document's score. This is correct behaviour — a word that appears in every document distinguishes nothing.
>
> **High IDF for `"semaglutide"`:** If `"semaglutide"` appears in only 2 of 30 documents, `IDF = log(30/2) = log(15) ≈ 2.71`. Multiplied by even a modest TF, it strongly upweights documents specifically about semaglutide — the discriminative power of IDF.
>
> **Adding 50 semaglutide documents:** The corpus grows to `N = 80` and `df` rises to ~52. `IDF = log(80/52) ≈ log(1.54) ≈ 0.43`. The IDF collapses — semaglutide becomes a common term and loses its discriminative power. This illustrates a fundamental fragility of TF-IDF: IDF values are **corpus-dependent and non-stationary**. Adding or removing documents changes every term's IDF, requiring a full index rebuild.

---

### Q3 · Stretch

`TfidfVectorizer` uses `sublinear_tf=True`, which applies `1 + log(tf)` instead of raw term frequency. Demo 2 explicitly shows a BM25 saturation curve. If you removed `sublinear_tf=True` from Demo 1 and re-ran Q6 from Demo 2 (where `"diabetes"` is repeated 4 times in the query), which document would unfairly rank higher, and why? How does sklearn's L2 normalization interact with this, and does it fully compensate?

> **A3**
>
> Without `sublinear_tf=True`, TF grows linearly. Query Q6 — `"diabetes diabetes diabetes diabetes insulin"` — produces a query vector with `TF = 4` for `"diabetes"` and `TF = 1` for `"insulin"`. Without sublinear dampening, `"diabetes"` contributes 4× as much weight to the query vector as `"insulin"`.
>
> The document that would unfairly rank higher is **D004 (DKA Management Protocol)**, which repeats `"diabetes"` multiple times. Each repetition stacks additively, boosting D004 even though it is not specifically about insulin initiation.
>
> **On L2 normalization:** sklearn's L2 normalization normalizes each *document* vector, preventing long documents from having a larger magnitude than short ones — it addresses **document length bias**. However, it does *not* address **term frequency inflation in the query vector** — the query `"diabetes × 4"` still produces a heavily `"diabetes"`-weighted query vector. L2 on documents helps somewhat (a document repeating `"diabetes"` 40 times is length-normalized), but does not fully compensate. BM25's `k1` parameter saturates TF in *both* query and document, which is the complete solution.

---

## Demo 2 — BM25 · [`02_bm25_demo.py`](02_bm25_demo.py)

### Q4 · Core

Demo 2 adds Query Q6 — `"diabetes diabetes diabetes diabetes insulin"` — explicitly to test TF saturation. Based on the saturation curve plotted by `plot_tf_saturation()`, at `k1=1.5`, approximately what is the BM25 TF contribution for a term appearing 10 times vs. 1 time? If `k1` were set to `0`, what behaviour would BM25 exhibit, and when might that actually be useful in a healthcare context?

> **A4**
>
> BM25 TF component = `TF × (k1 + 1) / (TF + k1)`, with `k1 = 1.5`:
>
> | Term frequency | Calculation | Result |
> |---|---|---|
> | TF = 1 | `1 × 2.5 / (1 + 1.5)` | **1.00** |
> | TF = 10 | `10 × 2.5 / (10 + 1.5)` | **≈ 2.17** |
>
> A term appearing 10 times contributes only ~2.17× more than one appearing once — far from the 10× of raw TF. The curve asymptotes toward `k1 + 1 = 2.5`.
>
> **When `k1 = 0`:** The formula becomes `TF × 1 / (TF + 0) = 1` for any `TF > 0`. BM25 degenerates to **binary presence/absence** — a term either appears or it doesn't, and repetition is ignored entirely.
>
> **Healthcare use case for `k1 = 0`:** Rare-disease lookups using ICD-10 or CPT codes. A code like `Z87.891` either appears in a note or it doesn't; how many times it appears is irrelevant. Binary TF is also appropriate for formulary restriction lookups where only the *presence* of a drug name in an authorization request matters.

---

### Q5 · Stretch

The demo notes that BM25 is the default ranker in Elasticsearch since v7.0. In a hospital EHR system with two document types — 50-word lab reports and 5,000-word discharge summaries — both about `"metformin toxicity"`, which would BM25 (with default `b=0.75`) tend to rank higher, all else equal? What value of `b` would you use to make BM25 length-agnostic, and when would that be appropriate?

> **A5**
>
> BM25 applies length normalization via the denominator factor `(1 - b + b × |d| / avgdl)`.
>
> - A 5,000-word discharge summary has `|d|/avgdl >> 1` → large denominator → TF contributions heavily penalized.
> - A 50-word lab report has `|d|/avgdl << 1` → denominator near 1.0 → TF weights barely penalized.
>
> **Result:** The 50-word lab report ranks higher, because each mention of `"metformin toxicity"` suffers less length penalization. This is actually *appropriate* — a short report entirely about metformin toxicity is more focused than a discharge summary where it appears as one section among many.
>
> **`b = 0` (length-agnostic):** Removing length normalization entirely is appropriate for corpora of uniform document length — for example, a set of standardized radiology report templates all ~300 words long. When `avgdl` is stable and representative of all documents, normalizing against it adds noise rather than signal.

---

## Demo 3 — Dense Bi-Encoder + ANN · [`03_dense_ann_demo.py`](03_dense_ann_demo.py)

### Q6 · Core

The demo states that `"myocardial infarction"` and `"heart attack"` would have a cosine similarity of ~0.85 in the `all-MiniLM-L6-v2` embedding space. Contrast this with how TF-IDF from Demo 1 would score these two phrases against each other. If you were building a retrieval system for a patient-facing chatbot where users type natural language (`"my chest hurts and I can't breathe"`), which retrieval approach from the demos would you use first, and why?

> **A6**
>
> **TF-IDF:** Would assign `"myocardial infarction"` and `"heart attack"` a cosine similarity of **exactly 0** — zero vocabulary overlap, zero score, no relationship whatsoever.
>
> **Bi-encoder:** These phrases map to vectors with cosine similarity ~0.85 because the model was trained contrastively on semantically equivalent pairs. It has internalized that both expressions refer to the same clinical event, regardless of surface form.
>
> **For a patient-facing chatbot:** Use the **dense bi-encoder** (Demo 3) as the first-stage retriever. Patient queries use natural, colloquial language (`"my chest hurts and I can't breathe"`) with zero lexical overlap with clinical terms like `"dyspnea"`, `"angina"`, or `"STEMI"`. TF-IDF would return near-zero scores for every document. The bi-encoder maps the natural language query into a semantic space where clinically relevant documents cluster nearby — precisely the "paraphrase and natural-language query" strength listed in Demo 3's tradeoffs section.

---

### Q7 · Core

Demo 3 introduces three FAISS index types: `IVFFlat`, `HNSW`, and `IVF-PQ`. For a hospital with 10 million clinical notes and a strict latency requirement of <50 ms per query on a CPU-only server with 16 GB RAM, which index would you choose and what tradeoff are you accepting? The demo mentions IVF-PQ achieves "~2–3% recall loss for 8× memory savings" — is that acceptable in a point-of-care setting?

> **A7**
>
> **Choose IVF-PQ.**
>
> | Index | Memory estimate (10M docs, 384-dim) | Verdict |
> |---|---|---|
> | IVFFlat | 10M × 384 × 4 bytes ≈ **15.4 GB** | Exhausts RAM, eliminated |
> | HNSW | Full vectors + graph overhead > IVFFlat | Eliminated on memory grounds |
> | IVF-PQ | 10M × ~96 bytes ≈ **960 MB** | Fits comfortably |
>
> IVF-PQ compresses vectors via product quantization; with tuned `nprobe` it easily achieves <50 ms on CPU.
>
> **Accepted tradeoff:** ~2–3% recall loss — you may miss 2–3 of the true top-100 neighbors.
>
> **Is this acceptable at point-of-care?** Generally **no** in isolation — missing a critical drug-interaction guideline is unacceptable. However, you compensate by: (1) retrieving a larger candidate set (e.g., top-200) with IVF-PQ, then (2) reranking with a cross-encoder (Demo 4). The recall loss at the retrieval stage is typically recovered by the reranker. This is precisely the two-stage pipeline motivation in Demo 4.

---

### Q8 · Stretch

Demo 3 lists domain-specific models: `BioLORD-2023`, `Clinical-BERT` (trained on MIMIC-III), and `MedCPT`. The demo uses `all-MiniLM-L6-v2` for mechanics. If you ran Demo 3's exact queries on `Clinical-BERT` instead, for which type of query would you expect the *largest* improvement in ranking, and for which type would the improvement be *smallest*? Justify your answer by reasoning about what Clinical-BERT's training data (MIMIC-III) does and does not contain.

> **A8**
>
> **Largest improvement — clinical shorthand and EHR-specific patterns:**
> Queries like `"pt w/ hx of MI p/w SOB, r/o PE"` are dense with notation that dominates MIMIC-III. `all-MiniLM-L6-v2` was trained on web text and rarely encounters this style; its embeddings for such queries are imprecise. Clinical-BERT maps them far closer to relevant clinical note embeddings.
>
> A secondary gain is on **negation in clinical text** — `"no signs of pneumonia"` vs. `"pneumonia present"`. Clinical-BERT has seen thousands of clinical negation patterns during training, giving it meaningfully better (though not perfect) negation representations.
>
> **Smallest improvement — precise biomedical named entities:**
> Queries like `"semaglutide GLP-1 receptor agonist"` consist of drug names, gene names, and ICD codes that appear extensively in web text (Wikipedia, medical news, drug forums). Even `all-MiniLM-L6-v2` handles these reasonably well. The gap between Clinical-BERT and MiniLM narrows sharply for precise medical terminology queries. For biomedical literature retrieval specifically, `BiomedBERT` or `MedCPT` (trained on PubMed Q&A pairs) would outperform Clinical-BERT here.

---

## Demo 4 — Rerankers · [`04_rerankers.py`](04_rerankers.py)

### Q9 · Core

Demo 4 implements four approaches: TF-IDF, Bi-Encoder, Cross-Encoder, and RRF. The cross-encoder takes `[CLS] query [SEP] document [SEP]` as a joint input. Explain precisely *why* a cross-encoder cannot retrieve from a 1-million-document corpus directly (without a first-pass retrieval step), while a bi-encoder can. What property of the cross-encoder's architecture makes pre-indexing impossible?

> **A9**
>
> The key property is **pre-indexability**.
>
> A **bi-encoder** encodes query and document *independently*. The document embedding `d_vec` is computed without any knowledge of the query. This means:
> 1. Encode all 1M documents offline at indexing time → store the 1M vectors
> 2. At query time, encode only the query (~1 ms) and run ANN search (~1 ms)
>
> Total: ~2 ms regardless of corpus size.
>
> A **cross-encoder** takes `[CLS] query [SEP] document [SEP]` as a *single joint sequence*. Every query token attends to every document token through all transformer layers. The document's internal representation **changes depending on the query** — there is no query-agnostic `d_vec` to precompute. Every (query, document) pair requires a full forward pass.
>
> At 5–20 ms per pair × 1M documents = **1,400–5,600 hours per query** — practically impossible. Cross-encoders are only viable when applied to a small candidate set (~10–100 documents) retrieved by a cheaper first-stage system, which is exactly the two-stage pipeline Demo 4 demonstrates.

---

### Q10 · Stretch

In Demo 4's Reciprocal Rank Fusion (RRF) implementation, the smoothing constant `k=60` is hardcoded. The RRF formula is `1/(k + rank)`. What happens to the relative influence of rank-1 vs. rank-10 documents as `k → ∞`? As `k → 0`? Then design a scenario involving a negation query like `"no signs of hepatic injury"` where RRF would still fail, and explain why none of the four approaches in Demo 4 would reliably handle it.

> **A10**
>
> **As `k → ∞`:** The formula `1/(k + rank) → 1/k` for all documents, regardless of rank position. Every document receives approximately the same RRF score. Rank ordering within each list becomes irrelevant — the fusion degenerates to treating all retrieved documents as equally relevant. Useless.
>
> **As `k → 0`:** The formula → `1/rank`. Rank-1 contributes `1.0`, rank-2 contributes `0.5`, rank-10 contributes `0.1`. Enormous weight is given to documents that top even one list. A single system's error at rank-1 propagates strongly into the fused result, making fusion brittle.
>
> `k = 60` is a pragmatic middle ground: top-ranked documents have meaningful but not overwhelming advantage.
>
> **Negation failure scenario — query: `"patient has no hepatic injury"`**
>
> | Approach | Why it fails |
> |---|---|
> | TF-IDF | `"no"` is stripped as a stopword; ranks documents *about* hepatic injury highly on `"hepatic"` + `"injury"` alone |
> | Bi-encoder | `all-MiniLM-L6-v2` was not trained on negation-specific contrastive pairs; embedding of `"no hepatic injury"` is geometrically close to `"hepatic injury"` because the dominant signal is the noun phrase |
> | Cross-encoder | `ms-marco-MiniLM` is trained on MS MARCO web passages, not clinical negation; fails on clinical patterns like `"no e/o"` or `"denies"` |
> | RRF | Inherits all the above failures; if both TF-IDF and bi-encoder rank hepatic-injury documents highly, RRF confidently surfaces them — wrong answer with high confidence |
>
> The fix requires **clinical NLP preprocessing** (e.g., the NegEx algorithm) to detect and exclude negated concepts before retrieval, or a model explicitly trained on negation-aware clinical IR datasets.

---

## Demo 5 & 6 — Evaluation Metrics · [`05_retriever_evals.py`](05_retriever_evals.py) · [`06_reranker_eval_ndcg.py`](06_reranker_eval_ndcg.py)

### Q11 · Core

Demo 5 explains that evaluation metrics work purely on document IDs — they never read text. It also warns about "pooling bias" in TREC-style evaluations. Demo 6 uses a 4-level graded relevance scale (0–3). If a retrieval system returns a Grade-3 document at rank 5 instead of rank 1, how much does this hurt its nDCG@10 score? Show the DCG contribution at each position using the formula from Demo 6.

> **A11**
>
> DCG formula from Demo 6: `DCG contribution at position i = rel_i / log₂(i + 1)`
>
> | Scenario | Calculation | DCG contribution |
> |---|---|---|
> | Grade-3 doc at rank 1 | `3 / log₂(2) = 3 / 1.000` | **3.000** |
> | Grade-3 doc at rank 5 | `3 / log₂(6) = 3 / 2.585` | **1.160** |
>
> The rank-5 placement captures only **38.7%** of the possible DCG contribution for that document — a loss of 1.84 DCG points.
>
> Against the ideal DCG (IDCG, computed by sorting all corpus grades descending: `[3, 3, 2, 2, 2, 2, 2, 1, 1, 1]`), misplacing a Grade-3 document from rank 1 to rank 5 causes roughly a **0.06–0.12 drop in nDCG@10**, depending on what fills ranks 1–4. This is the quantitative argument for why position matters in point-of-care settings — nDCG is specifically designed to penalize exactly this misplacement.

---

### Q12 · Stretch

Demo 5 maps clinical use cases to specific metrics: point-of-care search → Precision@k, systematic review → Recall@k, drug interaction lookup → MRR. A hospital is building a RAG system where a physician asks questions and an LLM generates answers using the retrieved documents. The retriever fetches top-5 documents. Which metric from Demo 5 best measures whether the retrieved set gives the LLM enough to answer correctly, and why is nDCG potentially *misleading* in this specific RAG context compared to its use in Demo 6?

> **A12**
>
> **Best metric for RAG: `Recall@5`**
>
> In a RAG pipeline, the LLM conditions on *all* k=5 retrieved documents simultaneously and synthesizes an answer from them. If the single most relevant document is anywhere in the retrieved set, the LLM can use it — position within the set is irrelevant to the LLM. What matters is **whether the relevant document is in the set at all**. Recall@5 measures exactly this: of all relevant documents, how many were captured in the top 5?
>
> **Why nDCG is misleading for RAG:**
>
> nDCG assumes a document at rank 1 is more valuable than one at rank 5 — it models a *human* who reads results sequentially and stops early. This is the correct model for Demo 6's clinical trial search (a researcher scans results top-to-bottom). But an LLM prompt that concatenates all 5 documents treats them **uniformly**: it has no positional fatigue, no early-stopping behaviour, and attends to all tokens equally. The rank within the retrieved set does not affect generation quality.
>
> A secondary concern: nDCG requires expensive human-annotated graded relevance for every (query, document) pair. For a RAG evaluation pipeline, a more practical and meaningful proxy is **answer correctness** (did the LLM produce a factually correct answer?) — connecting retrieval evaluation directly to downstream task performance rather than to an intermediate relevance signal.
