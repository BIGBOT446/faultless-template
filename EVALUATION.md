# Evaluation

A reproducible benchmark of the review pipeline, added after the initial build to answer
a question the system could not previously answer: **how well does it actually work, and
where is the bottleneck?**

Everything below is measured with `bench/run_bench.py`, which bypasses Django and the web
flow but reproduces the production path exactly — the same rules from `db.sqlite3`, the
same prompt template as `prompt.py`, the same sequential per-rule calls, and the same
`JsonOutputParser` used by `ai_output`.

## Test material and its limits

Stated up front, because it bounds every number on this page:

- **One document.** A geotechnical report supplied by the client: 5,372 words of body
  text, 13 tables, 6 top-level sections.
- **It is an acceptance document with deliberately seeded errors**, so issue density is
  far higher than a normal report. Counts here are not representative of production load.
- **No answer key.** The client did not provide a list of the errors they injected, so
  recall cannot be computed. Precision requires manual labelling (`bench/sample_review.py`).
- **Model non-determinism.** Even at `temperature=0`, repeated runs on identical input
  differ substantially — the terminology rule returned between 3 and 27 issues across
  runs of the same configuration. **Every figure below is the mean of three runs, with the
  range given**, and single-run numbers are not used as evidence.

## Two defects found before any measurement

**Langfuse tracing was never active on the review path.** `ai_output` passed
`config={"callbacks": [CallbackHandler]}` — the class, not an instance. LangChain
silently skips a non-instance handler, so no rule-level trace was ever recorded.
`summary.py` used `CallbackHandler()` correctly, which is why traces appeared for the
summary step only. Fixed by instantiating the handler.

**Truncated output was silently repaired.** `JsonOutputParser` does not raise on JSON cut
off mid-object; it drops the tail and returns the remainder, with the last match missing
fields — which then raises `KeyError` downstream in `summary.py`. Verified directly: a
three-match response truncated mid-object parses as two matches. Enabling DeepSeek JSON
Output turns this into a hard API error instead, so truncation now fails loudly. The
benchmark counts truncated and incomplete results separately rather than as successes.

## Finding 1 — a quarter of every report was never reviewed

`prompt.py` extracted the report with:

```python
text = "\n".join([para.text for para in body.paragraphs])
```

`Document.paragraphs` does not include table cells. On the test report that is **10,720
characters — 23% of the document — that never reached the model**, including every
bearing capacity, modulus and design parameter table. The rule most dependent on that
content, *Units and Symbols Consistency*, was reviewing a document with all its units
removed.

The annotation side needed no change: `marker/rules.py` locates text with Spire's
`FindAllString`, which already searches table cells (verified with a string that occurs
only inside a table). Only extraction was at fault.

`faultless/extract.py` now walks the document with `Document.iter_inner_content()` and
renders tables as Markdown pipe tables in place, preserving row and column context.
Extracted text grew from 35,091 to 43,009 characters.

## Finding 2 — restoring the missing content did not improve results

Three runs per configuration, whole document per call:

| Rule | Paragraphs only | With tables |
|---|---|---|
| Grammar and Spelling | **101.7** (101–102) | 68.0 (42–104) |
| Units and Symbols | 3.0 (3–3) | 3.0, **2 of 3 runs failed** |
| Terminology Consistency | 23.7 (17–27) | 21.0 (12–30) |
| Mandatory Sections | 1.0 | 1.0 |
| Acronym Definitions | 8.7 (6–14) | **34.3** (17–59) |
| **Total per run** | **138.0** (128–147) | 125.3 (100–143) |
| Latency per report | 28.3 s | 54.0 s |

- **Only the acronym rule clearly benefited** (+294%), and its ranges do not overlap
  (max 14 without tables, min 17 with) — table headers are dense with acronyms that had
  never been reviewed.
- **The grammar rule degraded.** It was remarkably stable on the shorter input
  (101, 102, 102) and became erratic on the longer one (104, 58, 42), with output tokens
  falling from 6,960 to 2,713 across runs. The model performed a shallower pass over the
  longer document rather than finding more.
- **The units rule became unstable**, exhausting a 16,384-token output limit in two of
  three runs after 40 s each, while returning exactly 3 issues whenever it succeeded.
- Latency roughly doubled.

Feeding the model more of the document did not make the system better. The limiting
factor was not coverage.

## Finding 3 — chunking helps, but only for some rules

The document was split into 11 section-sized chunks (≤6,000 characters, split on
top-level headings, each chunk labelled with its section), and every rule was run against
every chunk. Three runs, tables included:

| Rule | Whole document | Chunked (11 chunks) | Verdict |
|---|---|---|---|
| Units and Symbols | 3.0, 2 of 3 runs failed | **26.3** (24–29), 0 failures | Fixed |
| Mandatory Sections | 1.0 | 19.3 (19–20) | **Invalid** |
| Grammar and Spelling | 68.0 (42–104) | 185.3 (98–284), 5 failed calls | Not fixed |
| Terminology Consistency | 21.0 (12–30) | 67.3 (43–88), 2 failed calls | Unverified |
| Acronym Definitions | 34.3 (17–59) | 32.3 (32–33) | Unchanged |
| Latency per report | 54.0 s | 209.1 s | 3.9× cost |

- **Units and Symbols is genuinely fixed**: from failing two runs in three and returning
  three issues when it did not, to zero failures and a stable 24–29. Three unit issues in
  a geotechnical report full of kPa, MPa and mm was never a plausible result.
- **Mandatory Sections is broken by chunking, by construction.** It checks whether
  required sections exist in the report. Once the report is 11 fragments, each fragment
  is missing the introduction and the conclusion; 19 is the same judgement repeated
  eleven times, not nineteen findings.
- **Grammar is not a context-length problem.** A 6,000-character chunk still exhausted a
  16,384-token output limit. The rule flags something in nearly every sentence; it needs
  an output bound or a tighter definition, not a smaller input.
- Latency rose almost fourfold.

## Conclusion

**Chunking is not a pipeline-wide optimisation; its validity depends on the scope of the
rule.** Three distinct classes emerged from the data:

| Class | Example | Correct strategy |
|---|---|---|
| Local | Units, Grammar, Spelling | Chunk — accuracy improves, output stays bounded |
| Document-level | Mandatory Sections | Never chunk — the judgement requires the whole document |
| Unbounded output | Grammar | Cap the number of issues or tighten the rule definition |

The `faultless_rules` table already carries a `scale` column for severity; the natural
next step is a `scope` column, with the pipeline routing each rule to the matching
strategy instead of applying one uniform path to all of them.

## Not yet measured

- **Precision.** The grammar rule reports around 100 issues per run on a 5,372-word
  document. Whether those are findings or noise requires manual labelling;
  `bench/sample_review.py` draws a reproducible random sample and scores it.
- **Recall**, which needs the client's list of seeded errors.
- **Generalisation.** One document, and an atypical one.

## Reproducing

```bash
python bench/run_bench.py --no-tables --repeat 3      # paragraphs only
python bench/run_bench.py --repeat 3                  # with tables
python bench/run_bench.py --repeat 3 --chunk 6000     # chunked
python bench/sample_review.py --report <file> --n 20  # precision worksheet
```

Results are written to `bench/results/`. Quoted source text is stored only as a hash, so
no client content enters the repository; report files and review worksheets are
git-ignored.
