# Mini Assignments — Transformer Models

Three hands-on modifications to the existing code files. Each assignment targets
one file and takes roughly 15–30 minutes.

---

## Assignment 1 — Sampling Parameters & Prompt Engineering
**File:** [01_transformer_basic_pipeline.py](01_transformer_basic_pipeline.py)

### Background
GPT-2's output quality and diversity depend heavily on the sampling strategy.
`temperature`, `top_p`, and `top_k` interact in non-obvious ways.

> **Concept — Temperature**
> At each step the model produces a score (logit) for every token in its
> vocabulary. Those scores are divided by the temperature value before the
> softmax turns them into probabilities. A low temperature (e.g. 0.1) sharpens
> the distribution — the highest-scoring token gets almost all the probability,
> so output is near-deterministic and repetitive. A high temperature (e.g. 1.8)
> flattens the distribution — low-probability tokens get a real chance, so
> output is more varied but can become incoherent.

> **Concept — Top-k sampling**
> Instead of sampling from the full vocabulary (50 000+ tokens), only the `k`
> highest-probability tokens are kept; the rest are zeroed out. This prevents
> the model from accidentally picking a very unlikely token. `top_k=50` is a
> common default.

> **Concept — Nucleus (top-p) sampling**
> A dynamic alternative to top-k: keep the smallest set of tokens whose
> cumulative probability adds up to `p`. When the model is confident,
> that set is small (maybe 5 tokens). When the model is uncertain, it is
> large (maybe 500 tokens). `top_p=0.9` is a common default and often
> produces more natural text than a fixed top-k.

### Tasks

**1a. Explore temperature extremes**
Run the generator with these three temperatures and compare the outputs:
- `temperature=0.1` (near-deterministic)
- `temperature=1.0` (default distribution)
- `temperature=1.8` (very random)

For each run, keep all other parameters the same (`top_p=0.9`, `top_k=50`,
`num_return_sequences=3`). Write a one-sentence observation about what changes.

**1b. Change the domain**
Replace the cricket prompt with a technical prompt from your own field
(e.g. "The key advantage of transformer models over RNNs is").
Generate 3 completions with `temperature=0.7` and `max_length=80`.
Which completion reads most coherently? Does increasing `max_length` help?

**Expected outcome:** You should be able to explain the trade-off between
`temperature`, `top_p`, and `top_k` in your own words.

---

## Assignment 2 — Decoding the Logit Distribution
**File:** [02_next_token_prediction.py](02_next_token_prediction.py)

### Background
The file already shows top-k logits, top-k probabilities, and a filtered list
that skips single-character tokens. Your job is to extend it with two new analyses.

> **Concept — Logits**
> A logit is the raw, unnormalised score a neural network assigns to each
> possible output before any probability conversion. Think of it as a
> "confidence vote" in arbitrary units — a logit of 8.5 is more confident
> than a logit of 2.1, but the numbers themselves have no direct meaning
> until you apply softmax.

> **Concept — Softmax**
> Softmax converts a vector of logits into a proper probability distribution:
> each value is exponentiated and then divided by the sum of all exponentiated
> values. The result always sums to 1.0 and every entry is positive, so you
> can interpret each number as "the probability the model assigns to this token
> being next".

### Tasks

**2a. Change the prompt and observe the shift**
Replace `"Hello, my name is"` with two prompts of your choice — one factual
(e.g. `"The capital of France is"`) and one open-ended
(e.g. `"Once upon a time there was a"`) — and print the top-5 probability
table for each. Do the probability distributions look different
(peaked vs. spread out)? What does that tell you about how confident
the model is?

**2b. Compute entropy of the distribution**
After the softmax step, compute the Shannon entropy of the full probability
distribution over the vocabulary.

> **Concept — Shannon Entropy**
> Shannon entropy measures how "spread out" or uncertain a probability
> distribution is. For a distribution over N tokens it is defined as:
>
> `H = -Σ p(token) × log₂(p(token))` (summed over every token)
>
> - **Low entropy** (e.g. 2 bits): the distribution is peaked — one or two
>   tokens have almost all the probability. The model is confident about
>   what comes next (e.g. after "The Eiffel Tower is in").
> - **High entropy** (e.g. 12 bits): probability is spread over many tokens.
>   The model is uncertain — many continuations are plausible
>   (e.g. after "Once upon a time").
>
> Entropy gives you a single number that summarises the whole distribution,
> making it easy to compare how "sure" the model is across different prompts.
> The `1e-12` added inside the log is just a small constant to avoid
> `log(0)` for tokens with zero probability.

```python
import math
entropy = -sum(p * math.log(p + 1e-12) for p in probabilities.tolist())
print(f"Entropy: {entropy:.2f} bits")
```

Run this for both prompts from 2a. Which prompt produces higher entropy?
Does that match your intuition about which continuation is more predictable?

**2c. Filter by token type**
Instead of filtering out single-character tokens (Example 3), write a new
filter that keeps only tokens that start with a capital letter
(hint: `token_str.strip()[0].isupper()`). Print the top-5 results.
Under what kinds of prompts would this filter be useful?

**Expected outcome:** You will see concretely how logits → probabilities →
entropy tells you about model confidence, and practice custom token filtering.

---

## Assignment 3 — Translation with Beam Search and a New Language Pair
**File:** [04_transformer_encoder_decoder_translation.py](04_transformer_encoder_decoder_translation.py)

### Background
The file translates English → French using greedy decoding and then
`model.generate()`. Beam search and other `generate()` arguments can
significantly improve translation quality.

> **Concept — Greedy Decoding**
> At every decoding step, always pick the single highest-probability token.
> Fast and simple, but short-sighted: a locally good choice can lead to a
> globally poor sentence because the model never considers what comes after.

> **Concept — Beam Search**
> Instead of committing to one token at a time, beam search keeps the `N`
> most promising partial sequences (called "beams") alive in parallel.
> At each step every beam is extended by its top candidates, and only the
> `N` highest-scoring combined sequences survive. With `num_beams=5` the
> decoder explores 5 parallel hypotheses and returns the one with the best
> overall score. This usually produces more fluent and accurate translations
> than greedy decoding, at the cost of roughly N× more computation.

### Tasks

**3a. Switch to beam search**
Replace the `model.generate()` call with:

```python
translated_ids = model.generate(
    **inputs,
    num_beams=5,
    early_stopping=True,
    max_length=40
)
```

Translate these sentences and compare beam-search output to greedy decoding
(step-by-step loop):
- `"The patient was admitted to the hospital yesterday."`
- `"Transformers have revolutionized natural language processing."`

Does beam search produce noticeably better translations?

**3b. Try a different language pair**
Swap the model for `Helsinki-NLP/opus-mt-en-de` (English → German) or
`Helsinki-NLP/opus-mt-en-es` (English → Spanish). Translate the same two
sentences from 3a. You only need to change the `model_name` variable —
everything else stays the same. Verify the output looks correct using an
online translator.

**3c. Inspect the encoder hidden states**
After computing `hidden_states` for the sentence
`"Transformers have revolutionized natural language processing."`,
answer these questions in a comment at the bottom of the file:

> **Concept — Contextual vs Static Embeddings**
> A *static embedding* (e.g. Word2Vec) gives every word a single fixed
> vector regardless of context — "bank" always has the same representation
> whether you mean a river bank or a financial bank.
>
> A *contextual embedding* is produced by running the full sentence through
> the transformer. Each token's vector is shaped by every other token via
> the self-attention mechanism, so "bank" gets a different vector in
> "river bank" vs. "bank account". The encoder hidden states are contextual
> embeddings — that is what makes them powerful for downstream tasks.

> **Concept — Hidden State Shape `[batch, seq_len, hidden_dim]`**
> - `batch`: number of sentences processed together (usually 1 here).
> - `seq_len`: number of tokens in the input sentence (including any
>   special tokens added by the tokenizer).
> - `hidden_dim`: the size of each token's embedding vector (512 for this
>   Helsinki-NLP model). Every token is represented as a point in a
>   512-dimensional space.

1. What is the shape of `hidden_states`? What does each dimension represent?
2. Use `hidden_states[0].mean(dim=0)` to get a single sentence-level vector.
   What is its shape, and what does it represent conceptually?
3. Why do you think the encoder produces *contextual* embeddings rather than
   static (lookup-table) embeddings?

**Expected outcome:** You will understand how `generate()` arguments affect
output quality, how to swap Helsinki-NLP models for different language pairs,
and what the encoder hidden states actually represent.

---

## Submission

For each assignment, include in your code file:
- The modified code with your changes clearly marked by a comment `# MY CHANGE:`
- A brief comment explaining what you observed or learned
