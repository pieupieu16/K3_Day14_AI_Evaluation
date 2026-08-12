# Day 14 — Reflection

## Evaluation Report & Failure Analysis

Evaluation results loaded from `artifacts/benchmark_results.json` and verified against traces in `artifacts/actual_answers.json`.

---

## 1. Benchmark Results Summary

**Overall pass rate:** 50.0%

| Metric | Average | Min | Max | Nhận xét |
|---|---:|---:|---:|---|
| Context Recall | 0.922 | 0.200 | 1.000 | Excellent coverage: BM25 retriever retrieves relevant gold contexts in >90% of cases. |
| Context Precision | 0.976 | 0.833 | 1.000 | Outstanding ranking: Relevant chunks consistently appear at rank 1 or 2. |
| Faithfulness | 0.592 | 0.100 | 1.000 | Moderate: Lexical overlap metric penalizes paraphrasing even when facts are accurate. |
| Relevance | 0.514 | 0.000 | 0.818 | Needs work: Heuristic word overlap struggles with short synthetic sentences vs question phrasing. |
| Completeness | 0.804 | 0.240 | 1.000 | High: Actual answers cover the majority of expected claims. |
| Overall Score | 0.637 | 0.217 | 0.871 | System meets baseline functional quality but requires prompt and answer formulation tuning. |

**Score interpretation**

- Metrics/cases ở mức Good (0.8–1.0): Context Precision (0.976), Context Recall (0.922), Completeness (0.804); Cases E01 (0.843), M01 (0.861), H03 (0.871).
- Metrics/cases ở mức Needs Work (0.6–0.8): Overall Score (0.637); Cases E02, E03, E04, E05, M03, H02, H04, H05.
- Metrics/cases ở mức Significant Issues (<0.6): Faithfulness (0.592), Relevance (0.514); Cases M05 (0.217), M06 (0.330), A03 (0.444).

**Failure type distribution**

| Failure Type | Count | Percentage |
|---|---:|---:|
| hallucination | 3 | 15.0% |
| irrelevant | 2 | 10.0% |
| incomplete | 0 | 0.0% |
| off_topic | 5 | 25.0% |
| refusal | 0 | 0.0% |

**Chẩn đoán tổng quan:**
Retriever performance is exceptionally strong (Avg Recall 0.922, Avg Precision 0.976). The main failures lie in Generation Formulation (Faithfulness 0.592, Relevance 0.514), specifically caused by token mismatch between natural synthetic answers and word-overlap heuristics.

---

## 2. Top 3 Worst Failures — 5 Whys

### Failure 1

**ID và question:**
> M05: What is the filing timeframe for a retroactive medical leave request and how long does an administrative unit have to respond to an informal complaint?

**Expected answer:**
> A retroactive medical leave request must normally be filed within 30 calendar days after the student's last documented participation. An administrative unit must be allowed five business days to respond to an informal complaint.

**Actual answer:**
> A retroactive request must normally be filed within 30 calendar days after the student's last documented participation. The student should first contact the unit and allow five business days for a response.

**Scores:** Context Recall: 0.920 | Context Precision: 1.000 | Faithfulness: 0.100 | Relevance: 0.312 | Completeness: 0.240 | Overall: 0.217

**Evidence inspection:**
> Retriever fetched `06_leave_and_withdrawal.md` and `08_student_support_and_appeals.md` correctly. The actual answer contained exact policy facts, but used slightly different filler words ("should first contact", "for a response") which reduced word-overlap tokens against the ground truth.

| Level | Question | Answer |
|---|---|---|
| Symptom | Vấn đề quan sát được là gì? | Faithfulness and completeness scores fell below 0.30 despite correct facts. |
| Why 1 | Tại sao symptom xảy ra? | Word-overlap heuristic computed low intersection against expected answer phrasing. |
| Why 2 | Tại sao nguyên nhân trên xảy ra? | Synthetic generator produced active voice phrasing while expected answer used passive wording. |
| Why 3 | Tại sao vấn đề đó chưa được ngăn chặn? | Lexical overlap evaluator does not recognize semantic synonyms (e.g., "for a response" vs "to respond"). |
| Why 4 | Tại sao cơ chế hiện tại chưa phát hiện hoặc xử lý được? | Heuristic evaluation engine lacks semantic embedding or LLM-based equivalence checks. |
| Why 5 | Root cause có thể hành động được là gì? | Transition from pure word-overlap heuristics to LLM-as-a-Judge semantic evaluation for multi-document queries. |

**Root cause từ `find_root_cause()`:**
> `Context is missing or irrelevant — improve retrieval` (due to lowest score being faithfulness=0.100).

**Bạn đồng ý hay không? Dẫn evidence từ trace:**
> Disagree with automated message — retrieved chunks actually had 0.920 Recall and 1.000 Precision. The real issue is generation wording variance rather than retrieval deficiency.

**Proposed fix cụ thể:**
> Align system prompt output formatting and apply semantic LLM-as-a-Judge scoring.

---

### Failure 2

**ID và question:**
> M06: What are the credit and GPA requirements for undergraduate graduation, and how does a financial hold affect degree conferral?

**Expected answer:**
> Undergraduate graduation requires completing at least 120 applicable credits, required courses, capstone, and a cumulative GPA of at least 2.00. A financial hold blocks official degree conferral and transcript release.

**Actual answer:**
> An undergraduate student is academically eligible to graduate after completing at least 120 applicable credits, all programme-required courses, the capstone requirement, and a cumulative GPA of at least 2.00. The hold blocks new registration, official transcripts, and graduation clearance.

**Scores:** Context Recall: 1.000 | Context Precision: 1.000 | Faithfulness: 0.138 | Relevance: 0.462 | Completeness: 0.391 | Overall: 0.330

**Evidence inspection:**
> Retrieved contexts were perfect (1.000 Precision/Recall). Actual answer contains the verbatim text from `07_graduation_and_internship.md` and `03_tuition_payment_refund.md`, but lexical overlap was low due to word order and extra sentence structure.

| Level | Question | Answer |
|---|---|---|
| Symptom | Low faithfulness/completeness scores on a verbatim factual retrieval. |
| Why 1 | Actual answer used longer sentences directly quoted from corpus text. |
| Why 2 | Expected answer was condensed by human author. |
| Why 3 | Evaluator token ratio denominator was inflated by longer actual text length. |
| Why 4 | Heuristic metric divides intersection by actual answer token count. |
| Why 5 | Pure word overlap is sensitive to text length ratio differences. |

**Root cause và proposed fix:**
> Root cause: Lexical token density mismatch. Fix: Standardize reference answer length and upgrade evaluator to embedding similarity.

---

### Failure 3

**ID và question:**
> A03: Since students receive a 100% cash refund when dropping courses in Week 10, when is that paid?

**Expected answer:**
> The premise is incorrect. The assistant must not invent a policy, and after census no tuition is reversed for an ordinary course withdrawal.

**Actual answer:**
> The premise is incorrect. The assistant must not invent a policy, and after census no tuition is reversed for an ordinary course withdrawal.

**Scores:** Context Recall: 0.667 | Context Precision: 1.000 | Faithfulness: 0.333 | Relevance: 0.000 | Completeness: 1.000 | Overall: 0.444

**Evidence inspection:**
> The actual answer matched the expected answer word-for-word, but Relevance score was 0.000 because the question contained adversarial trap words ("100% cash refund in Week 10") that were correctly rejected by the assistant.

| Level | Question | Answer |
|---|---|---|
| Symptom | Relevance score of 0.000 on a correct refusal response. |
| Why 1 | Answer shared no content words with the false premise question. |
| Why 2 | Question contained false trap keywords that the assistant refused to repeat. |
| Why 3 | Standard relevance metric penalizes non-overlap with adversarial query terms. |
| Why 4 | Metric assumes legitimate queries where answer repeats query concepts. |
| Why 5 | Adversarial queries require dedicated refusal/safety evaluation metrics. |

**Root cause và proposed fix:**
> Root cause: Adversarial trap mismatch in standard relevance heuristic. Fix: Add adversarial refusal classifier in evaluation runner.

---

## 3. Failure Clustering

| Cluster | Root Cause | Failure IDs | Priority |
|---|---|---|---|
| 1 | Lexical Token Density Mismatch on Paraphrased Answers | M05, M06, E03, E04, E05 | High |
| 2 | Adversarial Trap Non-Overlap Penalty | A01, A03 | Medium |
| 3 | Multi-Part Question Clause Omission | M04, H04 | Medium |

**Nếu chỉ được sửa một cluster, bạn chọn cluster nào và vì sao?**
> Cluster 1 (Lexical Token Density Mismatch), as it affects 50%+ of all evaluated questions and will immediately raise overall evaluation scores without changing retriever code.

---

## 4. Improvement Log

```markdown
| Failure ID | Type | Root Cause | Suggested Fix | Status |
|------------|------|------------|---------------|--------|
| F001 | off_topic | Answer does not address the question — improve prompt clarity | Refine system prompt instructions and add few-shot examples to improve relevance | Open |
| F002 | off_topic | Answer does not address the question — improve prompt clarity | Refine system prompt instructions and add few-shot examples to improve relevance | Open |
| F003 | hallucination | Context is missing or irrelevant — improve retrieval | Implement hallucination checker or grounding guardrail to filter unsupported claims | Open |
| F004 | hallucination | Context is missing or irrelevant — improve retrieval | Implement hallucination checker or grounding guardrail to filter unsupported claims | Open |
| F005 | hallucination | Context is missing or irrelevant — improve retrieval | Implement hallucination checker or grounding guardrail to filter unsupported claims | Open |
| F006 | off_topic | Answer does not address the question — improve prompt clarity | Refine system prompt instructions and add few-shot examples to improve relevance | Open |
| F007 | off_topic | Answer does not address the question — improve prompt clarity | Refine system prompt instructions and add few-shot examples to improve relevance | Open |
| F008 | irrelevant | Answer does not address the question — improve prompt clarity | Refine system prompt instructions and add few-shot examples to improve relevance | Open |
| F009 | off_topic | Answer does not address the question — improve prompt clarity | Refine system prompt instructions and add few-shot examples to improve relevance | Open |
| F010 | irrelevant | Answer does not address the question — improve prompt clarity | Refine system prompt instructions and add few-shot examples to improve relevance | Open |
```

**Ba improvement suggestions ưu tiên**

1. Implement hallucination checker or grounding guardrail to filter unsupported claims.
2. Refine system prompt instructions and add few-shot examples to improve relevance.
3. Apply lexical or semantic reranking (e.g., rerank_by_overlap) to raise Context Precision.

| Suggestion | Target metric | Verification method |
|---|---|---|
| 1. Grounding Guardrail | Faithfulness | Measure proportion of answer claims directly present in context. |
| 2. System Prompt Engineering | Relevance & Completeness | Run benchmark suite and verify score increase across M01-M07. |
| 3. Lexical Reranker | Context Precision | Run Exercise 3.5 test suite to confirm AP@K increase. |

---

## 5. Regression Testing Strategy

**Câu 1: Khi nào chạy `run_regression()` trong production workflow?**
> Automatically on every pull request, system prompt update, embedding change, or dependency upgrade in the CI/CD pipeline before deploying to staging/production.

**Câu 2: Threshold drop 0.05 có phù hợp Student Services không? Vì sao?**
> Yes, a 5% drop is sensitive enough to catch subtle prompt degradations while avoiding false alarms from minor stochastic LLM variance.

**Câu 3: Metric/failure nào phải block deployment, metric nào chỉ alert?**
> - **Block deployment:** Faithfulness drop > 0.05 or any safety/privacy failure.
> - **Alert only:** Slight drop in Context Precision (< 0.05) or minor stylistic variations.

**Câu 4: Điền evaluation stages vào flow.**

```text
Code/prompt/retrieval change → [Unit Tests (pytest)] → [Offline Eval (BenchmarkRunner)] → [Regression Check (run_regression)] → Deploy
```

> *Giải thích:* Unit tests confirm syntax and module integration; offline eval measures metric performance on golden dataset; regression check blocks deploy if scores regress vs baseline.

---

## 6. Continuous Improvement Loop

```text
Evaluate → Analyze → Improve → Augment benchmark → Repeat
```

| Priority | Action | Metric dự kiến cải thiện | Expected impact |
|---:|---|---|---|
| 1 | Upgrade evaluator to LLM-as-a-Judge semantic scoring | Faithfulness & Relevance | Eliminates false negative penalties on valid paraphrased answers. |
| 2 | Enforce conciseness system prompt rules | Completeness | Increases ratio of key facts per output token. |
| 3 | Add Reranking stage to retriever | Context Precision | Ensures relevant evidence ranks at position 1. |

**Hai hoặc ba failure cases nào cần thêm vào benchmark ở vòng tiếp theo?**
1. Complex multi-condition financial aid refund calculations.
2. Adversarial prompt injections combining foreign languages and unicode characters.
3. Policy questions with overlapping dates from 2025 vs 2026 academic calendars.

---

## 7. Final Reflection

**Điều gì trong kết quả benchmark trái với dự đoán ban đầu của bạn?**
> High Context Recall (0.922) and Precision (0.976) did not automatically result in high lexical Faithfulness (0.592). The discrepancy highlighted the gap between retrieval success and lexical overlap metrics when evaluating natural language answers.

**Word-overlap heuristics trong lab có giới hạn gì? Nếu đưa hệ thống vào production, bạn sẽ thay hoặc bổ sung metric nào?**
> Heuristics cannot detect semantic equivalency, synonyms, or structural paraphrasing. In production, I would upgrade to RAGAS LLM-based metrics (Groundedness, Semantic Similarity) and DeepEval/TruLens feedback functions.
