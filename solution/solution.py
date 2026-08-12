"""
Day 14 — AI Evaluation & Benchmarking Pipeline
AICB-P1: AI Practical Competency Program, Phase 1

Key concepts from lecture:
    - Evaluation = Scientific Method for AI (Hypothesis → Experiment → Measure → Conclude → Iterate)
    - 4 nhóm metrics: Task Completion, Answer Quality, RAG-Specific, Business
    - RAG pipeline metrics: Context Recall → Context Precision → Faithfulness → Answer Relevancy
    - LLM-as-Judge: rubric scoring 1-5, detect bias (positional, verbosity, self-preference)
    - Golden dataset: stratified sampling (5 Easy + 7 Medium + 5 Hard + 3 Adversarial)
    - Failure taxonomy: hallucination, irrelevant, incomplete, off_topic, refusal
    - 5 Whys method for root cause analysis
    - CI/CD integration: eval as quality gate (score < threshold = block deploy)
    - Continuous Improvement Loop: Evaluate → Analyze → Improve → Augment → Repeat

Instructions:
    1. Fill in every required section marked with TODO.
    2. Do NOT change class/function signatures. The optional ``contexts``
       parameter in ``run_full_eval`` is part of the required interface.
    3. Copy this file to solution/solution.py when done.
    4. Run: pytest tests/ -v

The reranking helper is an optional bonus exercise and may remain unimplemented.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Task 1 — Data Models (Golden Dataset + Evaluation Results)
# ---------------------------------------------------------------------------

@dataclass
class QAPair:
    """
    A question-answer pair for evaluation (part of the Golden Dataset).

    Fields:
        question:        The question to answer.
        expected_answer: The reference/ground-truth answer (expert-written).
        context:            Source context (may be empty string if not applicable).
        metadata:           Optional metadata dict (difficulty, category, etc.).
        retrieved_contexts: List of retrieved chunks (ORDER = retriever rank).
                            Used by the retrieval-side metrics (Task 2b).
    """
    question: str
    expected_answer: str
    context: str | None = ""
    metadata: dict = field(default_factory=dict)
    retrieved_contexts: list = field(default_factory=list)


@dataclass
class EvalResult:
    """
    Evaluation result for a single Q&A pair.

    Fields:
        qa_pair:        The original QAPair.
        actual_answer:  What the agent actually returned.
        faithfulness:   Float 0-1, how grounded the answer is in context.
        relevance:      Float 0-1, how relevant the answer is to the question.
        completeness:   Float 0-1, how complete the answer is vs expected.
        passed:         True if all three scores >= 0.5.
        failure_type:   None if passed, otherwise one of:
                        "hallucination", "irrelevant", "incomplete", "off_topic".
        context_precision: Float 0-1 or None — quality of retrieval ranking.
        context_recall:    Float 0-1 or None — coverage of expected by context.
    """
    qa_pair: QAPair
    actual_answer: str
    faithfulness: float
    relevance: float
    completeness: float
    passed: bool
    failure_type: str | None = None
    context_precision: float | None = None
    context_recall: float | None = None

    def overall_score(self) -> float:
        """Compute the average of faithfulness, relevance, and completeness."""
        return (self.faithfulness + self.relevance + self.completeness) / 3.0


# ---------------------------------------------------------------------------
# Task 2 — RAGAS Evaluator (Simplified word-overlap heuristic)
# ---------------------------------------------------------------------------

STOPWORDS: set[str] = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "of", "in", "on", "at", "to", "for", "with", "as", "by", "and", "or",
    "it", "its", "this", "that", "these", "those", "from", "into", "than",
}


def _tokenize(text: str) -> set[str]:
    """Lowercase word tokenization, ignoring punctuation and stopwords."""
    if not text:
        return set()
    tokens = re.findall(r"\b\w+\b", text.lower())
    return {t for t in tokens if t not in STOPWORDS}


class RAGASEvaluator:
    """
    Evaluates RAG pipeline outputs using RAGAS-inspired heuristics.
    """

    def evaluate_faithfulness(self, answer: str, context: str) -> float:
        """Measure how grounded the answer is in the context."""
        context_str = context or ""
        ans_toks = _tokenize(answer)
        if not ans_toks:
            return 1.0
        ctx_toks = _tokenize(context_str)
        if not ctx_toks:
            return 0.0
        score = len(ans_toks & ctx_toks) / len(ans_toks)
        return min(1.0, max(0.0, score))

    def evaluate_relevance(self, answer: str, question: str) -> float:
        """Measure how relevant the answer is to the question."""
        q_str = question or ""
        q_toks = _tokenize(q_str)
        if not q_toks:
            return 1.0
        ans_toks = _tokenize(answer)
        score = len(ans_toks & q_toks) / len(q_toks)
        return min(1.0, max(0.0, score))

    def evaluate_completeness(self, answer: str, expected: str) -> float:
        """Measure how well the answer covers the expected answer."""
        exp_str = expected or ""
        exp_toks = _tokenize(exp_str)
        if not exp_toks:
            return 1.0
        ans_toks = _tokenize(answer)
        score = len(ans_toks & exp_toks) / len(exp_toks)
        return min(1.0, max(0.0, score))

    def evaluate_context_recall(self, contexts: list[str], expected: str) -> float:
        """Context Recall — how much of expected answer is covered by UNION of chunks."""
        exp_str = expected or ""
        exp_toks = _tokenize(exp_str)
        if not exp_toks:
            return 1.0
        union_toks = set().union(*[_tokenize(chunk) for chunk in contexts]) if contexts else set()
        score = len(exp_toks & union_toks) / len(exp_toks)
        return min(1.0, max(0.0, score))

    def evaluate_context_precision(
        self,
        contexts: list[str],
        expected: str,
        relevance_threshold: float = 0.1,
    ) -> float:
        """Context Precision — RANK-AWARE Average Precision (AP@K)."""
        exp_str = expected or ""
        exp_toks = _tokenize(exp_str)
        if not exp_toks:
            return 1.0
        if not contexts:
            return 0.0

        relevant_flags = []
        for chunk in contexts:
            chunk_toks = _tokenize(chunk)
            rel_ratio = len(chunk_toks & exp_toks) / len(exp_toks)
            relevant_flags.append(rel_ratio >= relevance_threshold)

        total_relevant = sum(1 for r in relevant_flags if r)
        if total_relevant == 0:
            return 0.0

        running_relevant = 0
        precision_sum = 0.0
        for k, rel in enumerate(relevant_flags, start=1):
            if rel:
                running_relevant += 1
                precision_sum += running_relevant / k

        score = precision_sum / total_relevant
        return min(1.0, max(0.0, score))

    def run_full_eval(
        self,
        answer: str,
        question: str,
        context: str,
        expected: str,
        contexts: list[str] | None = None,
    ) -> EvalResult:
        """Run standard answer metrics and optional retrieval metrics."""
        faithfulness = self.evaluate_faithfulness(answer, context)
        relevance = self.evaluate_relevance(answer, question)
        completeness = self.evaluate_completeness(answer, expected)

        passed = faithfulness >= 0.5 and relevance >= 0.5 and completeness >= 0.5
        failure_type: str | None = None
        if not passed:
            if faithfulness < 0.3:
                failure_type = "hallucination"
            elif relevance < 0.3:
                failure_type = "irrelevant"
            elif completeness < 0.3:
                failure_type = "incomplete"
            else:
                failure_type = "off_topic"

        ctx_recall: float | None = None
        ctx_precision: float | None = None
        if contexts is not None:
            ctx_recall = self.evaluate_context_recall(contexts, expected)
            ctx_precision = self.evaluate_context_precision(contexts, expected)

        qa_pair = QAPair(
            question=question,
            expected_answer=expected,
            context=context,
            retrieved_contexts=contexts if contexts is not None else [],
        )

        return EvalResult(
            qa_pair=qa_pair,
            actual_answer=answer,
            faithfulness=faithfulness,
            relevance=relevance,
            completeness=completeness,
            passed=passed,
            failure_type=failure_type,
            context_precision=ctx_precision,
            context_recall=ctx_recall,
        )


# ---------------------------------------------------------------------------
# Reranking helper (Exercise 3.5 — boosting Context Precision)
# ---------------------------------------------------------------------------

def rerank_by_overlap(contexts: list[str], query: str) -> list[str]:
    """A minimal lexical reranker: sort chunks by word overlap with query."""
    q_toks = _tokenize(query)
    return sorted(contexts, key=lambda c: len(_tokenize(c) & q_toks), reverse=True)


# ---------------------------------------------------------------------------
# Task 3 — LLM Judge
# ---------------------------------------------------------------------------

class LLMJudge:
    """Uses an LLM to score AI responses according to a rubric."""

    def __init__(self, judge_llm_fn: Callable[[str], str]) -> None:
        self.judge_llm_fn = judge_llm_fn

    def score_response(
        self,
        question: str,
        answer: str,
        rubric: dict[str, Any],
    ) -> dict[str, Any]:
        """Score an AI response using the judge LLM."""
        rubric_str = "\n".join(f"- {k}: {v}" for k, v in rubric.items())
        prompt = (
            f"Question: {question}\n"
            f"Answer: {answer}\n"
            f"Rubric:\n{rubric_str}\n"
            "Provide JSON output with 'scores' dict and 'reasoning' string."
        )
        raw_response = self.judge_llm_fn(prompt)
        parsed_scores = {}
        reasoning = raw_response

        try:
            match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                if isinstance(data, dict):
                    if "scores" in data and isinstance(data["scores"], dict):
                        parsed_scores = {
                            k: float(v) for k, v in data["scores"].items()
                        }
                    else:
                        parsed_scores = {
                            k: float(v)
                            for k, v in data.items()
                            if k in rubric and isinstance(v, (int, float))
                        }
                    if "reasoning" in data and isinstance(data["reasoning"], str):
                        reasoning = data["reasoning"]
        except Exception:
            pass

        if not parsed_scores:
            parsed_scores = {k: 0.5 for k in rubric}

        return {"scores": parsed_scores, "reasoning": reasoning}

    def detect_bias(self, scores_batch: list[dict[str, Any]]) -> dict[str, Any]:
        """Detect potential bias patterns in a batch of judge scores."""
        if not scores_batch:
            return {"positional_bias": False, "leniency_bias": False, "severity_bias": False}

        all_scores = []
        for item in scores_batch:
            scores_dict = item.get("scores", {})
            all_scores.extend(scores_dict.values())

        if not all_scores:
            avg_score = 0.5
        else:
            avg_score = sum(all_scores) / len(all_scores)

        leniency_bias = avg_score > 0.8
        severity_bias = avg_score < 0.3

        positional_bias = False
        if len(scores_batch) > 1:
            first_scores = list(scores_batch[0].get("scores", {}).values())
            rest_scores = []
            for item in scores_batch[1:]:
                rest_scores.extend(item.get("scores", {}).values())

            if first_scores and rest_scores:
                avg_first = sum(first_scores) / len(first_scores)
                avg_rest = sum(rest_scores) / len(rest_scores)
                positional_bias = (avg_first - avg_rest) > 0.15

        return {
            "positional_bias": positional_bias,
            "leniency_bias": leniency_bias,
            "severity_bias": severity_bias,
        }


# ---------------------------------------------------------------------------
# Task 4 — Benchmark Runner
# ---------------------------------------------------------------------------

class BenchmarkRunner:
    """Runs a full evaluation benchmark."""

    def run(
        self,
        qa_pairs: list[QAPair],
        agent_fn: Callable[[str], str],
        evaluator: RAGASEvaluator,
    ) -> list[EvalResult]:
        """Run all QA pairs through agent and evaluate each result."""
        results = []
        for pair in qa_pairs:
            answer = agent_fn(pair.question)
            res = evaluator.run_full_eval(
                answer=answer,
                question=pair.question,
                context=pair.context or "",
                expected=pair.expected_answer,
                contexts=pair.retrieved_contexts,
            )
            res.qa_pair = pair
            results.append(res)
        return results

    def generate_report(self, results: list[EvalResult]) -> dict[str, Any]:
        """Generate an aggregate report from evaluation results."""
        total = len(results)
        passed_cnt = sum(1 for r in results if r.passed)
        pass_rate = (passed_cnt / total) if total > 0 else 0.0

        avg_faith = (sum(r.faithfulness for r in results) / total) if total > 0 else 0.0
        avg_rel = (sum(r.relevance for r in results) / total) if total > 0 else 0.0
        avg_comp = (sum(r.completeness for r in results) / total) if total > 0 else 0.0

        rec_scores = [r.context_recall for r in results if r.context_recall is not None]
        prec_scores = [r.context_precision for r in results if r.context_precision is not None]

        avg_rec = (sum(rec_scores) / len(rec_scores)) if rec_scores else None
        avg_prec = (sum(prec_scores) / len(prec_scores)) if prec_scores else None

        failure_types: dict[str, int] = {}
        for r in results:
            if r.failure_type:
                failure_types[r.failure_type] = failure_types.get(r.failure_type, 0) + 1

        return {
            "total": total,
            "passed": passed_cnt,
            "pass_rate": pass_rate,
            "avg_faithfulness": avg_faith,
            "avg_relevance": avg_rel,
            "avg_completeness": avg_comp,
            "avg_context_recall": avg_rec,
            "avg_context_precision": avg_prec,
            "failure_types": failure_types,
        }

    def run_regression(self, new_results: list[EvalResult], baseline_results: list[EvalResult]) -> dict[str, Any]:
        """Compare new evaluation results against baseline."""
        n_len = len(new_results)
        b_len = len(baseline_results)

        n_faith = (sum(r.faithfulness for r in new_results) / n_len) if n_len > 0 else 0.0
        n_rel = (sum(r.relevance for r in new_results) / n_len) if n_len > 0 else 0.0
        n_comp = (sum(r.completeness for r in new_results) / n_len) if n_len > 0 else 0.0

        b_faith = (sum(r.faithfulness for r in baseline_results) / b_len) if b_len > 0 else 0.0
        b_rel = (sum(r.relevance for r in baseline_results) / b_len) if b_len > 0 else 0.0
        b_comp = (sum(r.completeness for r in baseline_results) / b_len) if b_len > 0 else 0.0

        regressions = []
        if (b_faith - n_faith) > 0.05:
            regressions.append("faithfulness")
        if (b_rel - n_rel) > 0.05:
            regressions.append("relevance")
        if (b_comp - n_comp) > 0.05:
            regressions.append("completeness")

        return {
            "new_avg_faithfulness": n_faith,
            "new_avg_relevance": n_rel,
            "new_avg_completeness": n_comp,
            "baseline_avg_faithfulness": b_faith,
            "baseline_avg_relevance": b_rel,
            "baseline_avg_completeness": b_comp,
            "regressions": regressions,
            "passed": len(regressions) == 0,
        }

    def identify_failures(
        self,
        results: list[EvalResult],
        threshold: float = 0.5,
    ) -> list[EvalResult]:
        """Return EvalResults where any score is below threshold."""
        return [
            r for r in results
            if r.faithfulness < threshold or r.relevance < threshold or r.completeness < threshold
        ]


# ---------------------------------------------------------------------------
# Task 5 — Failure Analyzer
# ---------------------------------------------------------------------------

class FailureAnalyzer:
    """Analyzes failed evaluation results to identify patterns and suggest fixes."""

    def categorize_failures(self, failures: list[EvalResult]) -> dict[str, int]:
        """Count failures by failure_type."""
        counts: dict[str, int] = {}
        for f in failures:
            if f.failure_type:
                counts[f.failure_type] = counts.get(f.failure_type, 0) + 1
        return counts

    def find_root_cause(self, failure: EvalResult) -> str:
        """Suggest a root cause for a single failure based on its scores."""
        scores = {
            "faithfulness": failure.faithfulness,
            "relevance": failure.relevance,
            "completeness": failure.completeness,
        }
        lowest_metric = min(scores, key=scores.get)

        if lowest_metric == "faithfulness":
            return "Context is missing or irrelevant — improve retrieval"
        elif lowest_metric == "relevance":
            return "Answer does not address the question — improve prompt clarity"
        elif lowest_metric == "completeness":
            return "Answer is missing key information — increase context window or improve generation"
        else:
            return "Multiple issues detected — review full pipeline"

    def generate_improvement_suggestions(self, failures: list[EvalResult]) -> list[str]:
        """Generate a prioritized list of improvement suggestions."""
        if not failures:
            return [
                "Pipeline performing well — monitor edge cases.",
                "Maintain test suite coverage across documents.",
                "Perform periodic human calibration on judge rubrics.",
            ]

        cats = self.categorize_failures(failures)
        suggestions = []

        if cats.get("hallucination", 0) > 0:
            suggestions.append("Implement hallucination checker or grounding guardrail to filter unsupported claims")
        if cats.get("incomplete", 0) > 0:
            suggestions.append("Increase chunk size or top_k in RAG pipeline to reduce context fragmentation")
        if cats.get("irrelevant", 0) > 0 or cats.get("off_topic", 0) > 0:
            suggestions.append("Refine system prompt instructions and add few-shot examples to improve relevance")

        default_candidates = [
            "Add few-shot examples showing complete answers to improve completeness",
            "Apply lexical or semantic reranking (e.g., cross-encoder) to raise Context Precision",
            "Harden system prompts against prompt injection and out-of-scope queries",
        ]
        for candidate in default_candidates:
            if len(suggestions) >= 3:
                break
            if candidate not in suggestions:
                suggestions.append(candidate)

        return suggestions

    def generate_improvement_log(self, failures: list[EvalResult], suggestions: list[str]) -> str:
        """Generate a Markdown table logging failures and improvement actions."""
        lines = [
            "| Failure ID | Type | Root Cause | Suggested Fix | Status |",
            "|------------|------|------------|---------------|--------|",
        ]

        for i, f in enumerate(failures, start=1):
            f_id = f"F{i:03d}"
            f_type = f.failure_type or "Unknown"
            rcause = self.find_root_cause(f)
            fix = suggestions[i - 1] if i - 1 < len(suggestions) else (suggestions[0] if suggestions else "Review pipeline")
            lines.append(f"| {f_id} | {f_type} | {rcause} | {fix} | Open |")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point for manual testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    qa_pairs = [
        QAPair(
            question="What is RAG?",
            expected_answer="RAG stands for Retrieval-Augmented Generation, which combines retrieval with text generation.",
            context="RAG is a technique that retrieves relevant documents and uses them to ground LLM generation.",
            metadata={"difficulty": "easy", "category": "definition"},
        ),
        QAPair(
            question="What is the capital of France?",
            expected_answer="Paris is the capital of France.",
            context="France is a country in Western Europe. Its capital city is Paris.",
            metadata={"difficulty": "easy", "category": "factual"},
        ),
        QAPair(
            question="Explain backpropagation and why it matters for training",
            expected_answer="Backpropagation is an algorithm for training neural networks by computing gradients efficiently, enabling deep learning models to learn from errors.",
            context="Neural networks learn through gradient descent. Backpropagation efficiently computes these gradients layer by layer.",
            metadata={"difficulty": "medium", "category": "explanation"},
        ),
        QAPair(
            question="Should I use RAG or fine-tuning for my chatbot?",
            expected_answer="It depends on the use case: RAG is better for frequently updated knowledge, fine-tuning for consistent style/behavior. Consider cost, latency, and data freshness.",
            context="RAG retrieves external documents at inference time. Fine-tuning modifies model weights during training.",
            metadata={"difficulty": "hard", "category": "comparison"},
        ),
        QAPair(
            question="What is the meaning of life?",
            expected_answer="This question is outside the scope of this system. I can help with AI and technology questions.",
            context="This is an AI assistant specialized in technology topics.",
            metadata={"difficulty": "adversarial", "category": "out_of_scope"},
        ),
    ]

    evaluator = RAGASEvaluator()
    runner = BenchmarkRunner()

    def mock_agent(question: str) -> str:
        return f"Based on my knowledge: {question[:30]}... The answer involves key concepts."

    results = runner.run(qa_pairs, mock_agent, evaluator)
    report = runner.generate_report(results)
    print("=== Benchmark Report ===")
    for k, v in report.items():
        print(f"  {k}: {v}")

    failures = runner.identify_failures(results, threshold=0.5)
    print(f"\n=== Failures ({len(failures)}) ===")
    analyzer = FailureAnalyzer()

    categories = analyzer.categorize_failures(failures)
    print("Failure Categories:", categories)

    for f in failures:
        cause = analyzer.find_root_cause(f)
        print(f"  Root cause: {cause}")

    suggestions = analyzer.generate_improvement_suggestions(failures)
    print("\nImprovement Suggestions:")
    for s in suggestions:
        print(f"  - {s}")

    log = analyzer.generate_improvement_log(failures, suggestions)
    print("\n=== Improvement Log ===")
    print(log)
