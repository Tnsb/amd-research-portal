# Phase 2 Evaluation Report

**Domain:** Trustworthy RAG Evaluation Methods  
**Main question:** How do different faithfulness metrics fail, and how can we combine them?

---

## 1. Query set design

- **Total queries:** 23 (≥20 required).
- **Direct (12):** Q01–Q10, Q22, Q23 — single-concept questions (e.g. “What does RAGAS measure?”, “What is the FactCC benchmark?”) answered from one or few chunks. These map to the main question by probing individual metrics and benchmarks (RAGAS, ARES, BERTScore, SummaC, FaithEval, TRUE, NLI, G-Eval) and failure modes.
- **Synthesis / multi-hop (6):** Q11–Q16 — compare two papers or approaches (RAGAS vs ARES, BERTScore vs SummaC, NLI vs QA-based, RAGAS vs survey, FactCC vs FIB, REALM vs REPLUG). They require combining multiple sources and support the main question by contrasting how different metrics work and where they agree or differ.
- **Edge / ambiguity (5):** Q17–Q21 — yes/no or evidence-checking (“Does the corpus contain evidence that …?”, “Does the corpus discuss GPT-5?”). They test correct use of “corpus does not contain evidence” and retrieval limits.

**Rationale:** Queries were chosen to (1) cover key papers in the manifest (RAGAS, ARES, BERTScore, FactCC, SummaC, FaithEval, TRUE, NLI, G-Eval, REALM, REPLUG, surveys), (2) mix direct lookup with synthesis and edge cases, and (3) align with the domain question on faithfulness metrics and their failure modes. Expected behavior is documented in `src/eval/query_set.csv` (e.g. “Describe RAGAS faithfulness with citations to RAGAS2023”).

---

## 2. Metrics

1. **Groundedness / faithfulness:** For each answer we assess whether the claims are supported by the retrieved chunks (no fabrication, no unsupported claims). Scored here by manual inspection of a sample and by identifying clear failures: answers that state “corpus does not contain evidence” when the relevant source is in the corpus but was not retrieved, or answers that cite the wrong source. Scale: binary (grounded vs not) for failure-case analysis; a full run could use a 1–4 scale per answer.

2. **Citation / source correctness:** For direct and synthesis queries, we check whether the answer cites the expected source(s) from the manifest (e.g. FactCC → FactCC2020, TRUE → TRUE_Benchmark2023). Failures include: (a) retrieval did not return the relevant document, so the model correctly said “not in passages” but the corpus does contain it; (b) model cited a source that was retrieved but the claim was not supported by that chunk. This metric is computed by comparing `retrieved_chunk_ids` and cited source_ids in `model_output` against the expected sources in `query_set.csv` and the manifest.

*Computation note:* The current run does not include automated metric scripts; the results and failure cases below are based on inspection of `logs/eval_run_20260215_195940.jsonl`. Phase 3 could add automated faithfulness (e.g. NLI or LLM-as-judge) and citation precision/recall.

---

## 3. Results

- **Run:** 23 queries, model=groq, log file `logs/eval_run_20260215_195940.jsonl`.
- **Summary:** Most direct queries (e.g. Q01, Q02, Q03, Q05, Q06, Q10, Q22, Q23) received grounded answers with correct citations to retrieved chunks. Synthesis queries (Q11, Q13, Q14) often succeeded when retrieval returned the right sources; several (Q12, Q15, Q16) failed because retrieval did not return the primary expected source (e.g. SummaC, FactCC, FIB, REALM, REPLUG). Edge queries (Q17–Q21) were generally handled correctly (yes/no with citations or “corpus does not contain” where appropriate).
- **Structured citations:** The appended “## References” block (from `data/data_manifest.csv`) lists title, authors, year, and URL for each cited/retrieved source_id. This improves traceability and readability: users can verify sources without opening the manifest. In failure cases where the model cited only retrieved (but wrong) sources, the reference list still reflected what the model used, not what was missing; so structured citations help when retrieval is correct and make it easier to spot when the cited set is incomplete.

*Table (illustrative):*

| Query type | Count | Subjective outcome (from log inspection) |
|------------|-------|----------------------------------------|
| Direct     | 12    | ~8 strong (correct source + grounded), ~4 weak (wrong/missing retrieval or hedging) |
| Synthesis  | 6     | ~3 strong, ~3 failed (missing key source in retrieval) |
| Edge       | 5     | ~5 appropriate (correct yes/no and citations or “no evidence”) |

**What improved with the enhancement (structured citations).** The single enhancement implemented is **structured citations** (inline citations plus a reference list from the data manifest). It improved: (1) **Traceability** — every cited source_id is resolved to title, authors, year, and URL in the “## References” block, so readers can verify sources without opening the manifest. (2) **Readability** — answers end with a consistent reference list instead of raw (source_id, chunk_id) only. (3) **Auditability** — when retrieval fails or the model cites the wrong source, the reference list still shows exactly which sources were used, making it easier to spot missing or incorrect citations. (4) **Trust** — hallucinated citation IDs are omitted from the reference list (only manifest source_ids are included), so the list reflects only resolvable sources.

---

## 4. Failure cases (≥3 required)

Document at least three representative failures with evidence (quote from log + chunk/source).

| Case | Query ID | What went wrong | Evidence (log/chunk) |
|------|----------|-----------------|----------------------|
| 1    | Q07      | **False “no evidence”:** Model stated “The corpus does not contain evidence for this” and “no mention of the TRUE benchmark,” but the corpus includes TRUE_Benchmark2023. Retrieval did not return any TRUE chunk. | **Query:** “What is the TRUE benchmark and what does it evaluate?” **Retrieved:** `RAG_Survey_LLM2025_chunk_18`, `RAG_Eval_Survey2024_chunk_08`, `RAG_Eval_Survey2024_chunk_06`, `BERTScore2019_chunk_56`, `RAG_Eval_Survey2024_chunk_04`. **Model output:** “The corpus does not contain evidence for this. There is no mention of the TRUE benchmark in any of the provided passages.” TRUE_Benchmark2023 is in `data/data_manifest.csv`; retrieval failure led to a correct inference from passages but an incorrect conclusion about the corpus. |
| 2    | Q04      | **Wrong retrieval → misleading answer:** User asked about FactCC. Retrieval returned no FactCC2020 chunk (only QASemConsistency, FIB2022, RAG surveys). Model correctly said “FactCC is not explicitly mentioned in the provided passages” but the corpus does contain FactCC2020. | **Query:** “What is the FactCC benchmark and how does it assess factual consistency?” **Retrieved:** `QASemConsistency2024_chunk_12`, `FIB2022_chunk_00`, `RAG_Eval_Survey2024_chunk_13`, `FIB2022_chunk_03`, `RAG_Survey_LLM2025_chunk_19`. **Model output:** “The FactCC benchmark is not explicitly mentioned in the provided passages. However, there are mentions of other benchmarks such as FIB …” FactCC2020 is in the manifest; retrieval missed it. |
| 3    | Q12      | **Missing source for synthesis:** Comparison of BERTScore vs SummaC. Retrieval returned BERTScore and FactCC chunks but no SummaC2021. Model stated “SummaC is not explicitly mentioned in the provided passages,” so the comparison could not be grounded. | **Query:** “Compare BERTScore vs SummaC for faithfulness evaluation.” **Retrieved:** `FactCC2020_chunk_26`, `BERTScore2019_chunk_26`, `FactCC2020_chunk_15`, `BERTScore2019_chunk_23`, `G-Eval2023_chunk_08`. **Model output:** “SummaC is not explicitly mentioned in the provided passages … we cannot directly compare BERTScore and SummaC based on the provided passages.” SummaC2021 is in the corpus; retrieval did not return it. |
| 4    | Q15      | **Missing both sources for comparison:** Query asked to compare FactCC and FIB. Retrieval had no FactCC2020 and no FIB2022 chunks in the top-5 (SummaC2021, RAG surveys, QASemConsistency). Model correctly said “corpus does not contain evidence for a direct comparison” and “no information about the FIB benchmark” given the passages, but both benchmarks are in the corpus. | **Query:** “Compare FactCC and FIB benchmarks: what do they measure and how do they differ?” **Retrieved:** `SummaC2021_chunk_11`, `RAG_Eval_Survey2024_chunk_10`, `RAG_Survey_LLM2025_chunk_19`, `QASemConsistency2024_chunk_12`, `RAG_Survey_LLM2025_chunk_08`. **Model output:** “The corpus does not contain evidence for a direct comparison … no information provided in the passages about the FIB benchmark.” Failure is retrieval-only. |
