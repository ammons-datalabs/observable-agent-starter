"""Run DSPy teleprompting to improve the video idea generator prompt."""

from __future__ import annotations

import argparse
from pathlib import Path
import os
import math
from typing import List, Tuple, Dict, Set
from types import SimpleNamespace
import sys

import dspy

# Ensure the example's src/ is importable when run directly
EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = EXAMPLE_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from influencer_assistant.dspy.video_ideas import (  # noqa: E402
    VideoIdeaSignature,
    VideoIdeasStructuredSignature,
)
from influencer_assistant.dspy.config import configure_lm_from_env  # noqa: E402
from influencer_assistant.training.dataset import build_training_dataset  # noqa: E402

try:
    from dspy.teleprompt import BootstrapFewShotWithRandomSearch
except ImportError as exc:  # pragma: no cover - teleprompt availability depends on DSPy version
    raise SystemExit(
        "DSPy teleprompting components are unavailable. Upgrade dspy-ai to >=2.4."
    ) from exc

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "video_ideas_optimized.txt"
REPORT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "video_ideas_tuning_report.md"


def _lines_from_obj(obj: object) -> List[str]:
    """Extract up to 3 standardized lines from either structured or text outputs.

    Robust to partially-filled structured outputs: builds a line if at least one
    of title/summary/pillar is present, adding the pillar section only when set.
    Falls back to the free-form `response` text when no structured fields exist.
    """

    def get(name: str) -> str:
        return str(getattr(obj, name, "") or "").strip()

    titles = [get(f"idea{i}_title") for i in (1, 2, 3)]
    summaries = [get(f"idea{i}_summary") for i in (1, 2, 3)]
    pillars = [get(f"idea{i}_pillar") for i in (1, 2, 3)]

    if any(titles) or any(summaries) or any(pillars):
        out: List[str] = []
        for i in range(3):
            t = titles[i]
            s = summaries[i]
            p = pillars[i]
            if not (t or s or p):
                continue
            core = " - ".join(part for part in (t, s) if part)
            if p:
                out.append(f"{core} | {p}" if core else f"{p}")
            else:
                out.append(core)
        if out:
            return out[:3]

    # Fallback to free-form response string
    text = str(getattr(obj, "response", "") or "")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[:3]


def similarity_metric(
    example: dspy.Example, prediction: dspy.Prediction, trace: object | None = None
) -> float:
    """Fuzzy similarity between expected and predicted idea lists.

    - Normalizes numbering/punctuation/case.
    - Uses both token Jaccard and difflib ratio per line.
    - Counts a match if max(sim) >= 0.6, then returns fraction matched.
    """

    import difflib
    import re

    def normalize_line(s: str) -> str:
        s = s.strip().lower()
        # Drop leading numbering like "1.", "2)", etc.
        s = re.sub(r"^\s*\d+[\.)\-\s]*", "", s)
        # Unify separators
        s = s.replace(" — ", " - ").replace("–", "-")
        # Collapse whitespace
        s = re.sub(r"\s+", " ", s)
        return s

    def token_set(s: str) -> set[str]:
        return {t for t in re.split(r"[^a-z0-9]+", s) if t}

    expected_lines = [normalize_line(line) for line in _lines_from_obj(example)]
    predicted_lines = [normalize_line(line) for line in _lines_from_obj(prediction)]

    if not expected_lines:
        return 0.0
    if not predicted_lines:
        return 0.0

    matched = 0
    used = set()
    for exp in expected_lines:
        exp_tokens = token_set(exp)
        best = 0.0
        best_idx = -1
        for i, pred in enumerate(predicted_lines):
            if i in used:
                continue
            pred_tokens = token_set(pred)
            j = 0.0
            if exp_tokens or pred_tokens:
                inter = len(exp_tokens & pred_tokens)
                union = len(exp_tokens | pred_tokens) or 1
                j = inter / union
            r = difflib.SequenceMatcher(None, exp, pred).ratio()
            score = max(j, r)
            if score > best:
                best = score
                best_idx = i
        # Count as match if reasonably similar
        if best >= 0.6:
            matched += 1
            used.add(best_idx)

    return matched / max(1, len(expected_lines))


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / math.sqrt(na * nb)


class _OpenAIEmbedder:
    """Tiny, dependency-free embedder using OpenAI's /v1/embeddings API.

    Requires OPENAI_API_KEY. Honors OPENAI_BASE_URL and OPENAI_EMBED_MODEL.
    Caches by exact string to avoid repeated calls.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise SystemExit("Semantic metric requires OPENAI_API_KEY to be set (via .env).")
        base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.url = f"{base}/embeddings"
        self.model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        self._cache: Dict[str, List[float]] = {}

    def embed(self, texts: List[str]) -> List[List[float]]:
        import json as _json
        from urllib import request as _req
        from urllib.error import HTTPError, URLError

        payload = {"model": self.model, "input": texts}
        data = _json.dumps(payload).encode("utf-8")
        req = _req.Request(self.url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        try:
            with _req.urlopen(req, timeout=60) as resp:
                body = resp.read()
            obj = _json.loads(body.decode("utf-8"))
            vectors = [d.get("embedding", []) for d in obj.get("data", [])]
            return vectors
        except (HTTPError, URLError, TimeoutError, Exception):  # pragma: no cover
            # On any failure, return empty list to trigger fallback logic
            return []

    def get(self, text: str) -> List[float]:
        vec = self._cache.get(text)
        if vec is not None:
            return vec
        vecs = self.embed([text])
        if vecs:
            self._cache[text] = vecs[0]
            return vecs[0]
        return []


def _normalize_for_semantic(s: str) -> str:
    import re

    s = s.strip().lower()
    s = re.sub(r"^\s*\d+[\.)\-\s]*", "", s)  # drop leading numbers
    s = s.replace(" — ", " - ").replace("–", "-")
    s = re.sub(r"\s+", " ", s)
    return s


def make_semantic_metric(threshold: float = 0.65):
    embedder = _OpenAIEmbedder()

    def metric(
        example: dspy.Example, prediction: dspy.Prediction, trace: object | None = None
    ) -> float:
        exp_lines_raw = [line for line in _lines_from_obj(example) if line.strip()]
        pred_lines_raw = [line for line in _lines_from_obj(prediction) if line.strip()]
        exp_lines = [_normalize_for_semantic(line) for line in exp_lines_raw]
        pred_lines = [_normalize_for_semantic(line) for line in pred_lines_raw]
        if not exp_lines or not pred_lines:
            return 0.0
        # Batch-embed all unique lines not yet in cache for efficiency
        unique: List[str] = []
        seen: Set[str] = set()
        for line in exp_lines + pred_lines:
            if line not in seen and line not in embedder._cache:
                seen.add(line)
                unique.append(line)
        if unique:
            vecs = embedder.embed(unique)
            if vecs and len(vecs) == len(unique):
                for line, v in zip(unique, vecs):
                    embedder._cache[line] = v
            else:
                # Embedding failed; fall back to fuzzy metric to avoid zeroing
                try:
                    return similarity_metric(example, prediction, trace)
                except Exception:
                    return 0.0

        matched = 0
        used: set[int] = set()
        for exp in exp_lines:
            e = embedder._cache.get(exp, [])
            best = 0.0
            best_i = -1
            for i, ptxt in enumerate(pred_lines):
                if i in used:
                    continue
                p = embedder._cache.get(ptxt, [])
                sim = _cosine(e, p)
                if sim > best:
                    best = sim
                    best_i = i
            if best >= threshold and best_i >= 0:
                matched += 1
                used.add(best_i)
        return matched / max(1, len(exp_lines))

    return metric


def main(
    num_candidates: int,
    save_path: Path,
    metric_name: str,
    semantic_threshold: float,
    report_output: Path,
) -> None:
    if not configure_lm_from_env():
        raise SystemExit(
            "No LM configured. Set OPENAI_* environment variables before running tuning."
        )

    trainset = build_training_dataset()
    # Capture baseline predictions before tuning for each labeled example
    baseline_predict = dspy.Predict(VideoIdeasStructuredSignature)
    baseline_results: List[Tuple[dspy.Example, object]] = []
    for ex in trainset:
        try:
            pred0 = baseline_predict(
                profile_context=getattr(ex, "profile_context", ""),
                request=getattr(ex, "request", ""),
            )
            baseline_results.append((ex, pred0))
        except Exception:
            baseline_results.append((ex, SimpleNamespace()))
    # Choose metric
    metric_func = similarity_metric
    if metric_name == "semantic":
        metric_func = make_semantic_metric(threshold=semantic_threshold)

    optimizer = BootstrapFewShotWithRandomSearch(
        metric=metric_func,
        num_candidate_programs=num_candidates,
        max_bootstrapped_demos=4,
        max_labeled_demos=4,
        max_rounds=1,
        max_errors=10,
    )

    # Pass the training set to the optimizer call/compile step, not the constructor.
    tuned_predict = optimizer.compile(
        student=dspy.Predict(VideoIdeasStructuredSignature), trainset=trainset
    )

    # Write tuned guidance for later reuse. Not all DSPy versions expose a raw
    # `prompt` string on compiled modules, so we persist a readable set of
    # few-shot demos that capture the tuned behavior.
    demos = getattr(tuned_predict, "demos", None)
    if not demos:
        # Some DSPy versions keep best demos on the teleprompter instance
        demos = getattr(optimizer, "best_demos", None)
    output_lines = [
        "Video Idea Generator — Tuned Few‑Shot Demos",
        "",
        "Use these examples to guide the predictor. Provide 3–5 concise ideas as",
        "a numbered list: 'Title - Summary | Pillar'.",
        "",
    ]

    if demos:
        for idx, demo in enumerate(demos, start=1):
            req = getattr(demo, "request", None)
            demo_lines = _lines_from_obj(demo)
            output_lines.append(f"Demo {idx} Request:")
            if isinstance(req, str):
                output_lines.append(req.strip())
            else:
                output_lines.append(str(req))
            output_lines.append("")
            output_lines.append("Demo Response:")
            output_lines.extend(demo_lines)
            output_lines.append("\n---\n")
    else:
        # Fallback: persist the training set as guidance if no tuned demos exist.
        output_lines.append("No tuned demos available; saving training examples instead.\n")
        for idx, ex in enumerate(trainset, start=1):
            output_lines.append(f"Train Example {idx} Request:")
            output_lines.append(getattr(ex, "request", "<unknown>") or "")
            output_lines.append("")
            output_lines.append("Expected Response:")
            output_lines.append(getattr(ex, "response", "<unknown>") or "")
            output_lines.append("\n---\n")

    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text("\n".join(output_lines))
    print(f"Optimized guidance saved to {save_path}")

    # Preview the tuned demos for quick inspection.
    demos = getattr(tuned_predict, "demos", None) or getattr(optimizer, "best_demos", None)
    if demos:
        print("\nTuned demos:\n-----------------")
        for idx, demo in enumerate(demos, start=1):
            print(f"Demo {idx}:")
            print(demo)
            print("-----------------")
    else:
        print("No tuned demos available on the compiled module.")

    # Write a Before/After markdown report with scores using the chosen metric
    try:
        metric_for_report = metric_func
        report_lines: List[str] = []
        lm = getattr(dspy.settings, "lm", None)
        model_name = getattr(lm, "model", None)
        report_lines.append("# Video Ideas Tuning Report")
        report_lines.append("")
        report_lines.append(f"- Model: {model_name}")
        report_lines.append(f"- Metric: {metric_name}")
        if metric_name == "semantic":
            report_lines.append(f"- Semantic threshold: {semantic_threshold}")
        report_lines.append(f"- Candidates: {num_candidates}")
        report_lines.append("")

        for idx, (ex, base_pred) in enumerate(baseline_results, start=1):
            tuned_pred = tuned_predict(
                profile_context=getattr(ex, "profile_context", ""),
                request=getattr(ex, "request", ""),
            )
            base_lines = _lines_from_obj(base_pred)
            tuned_lines = _lines_from_obj(tuned_pred)
            try:
                base_score = metric_for_report(ex, base_pred, None)
            except Exception:
                base_score = 0.0
            try:
                tuned_score = metric_for_report(ex, tuned_pred, None)
            except Exception:
                tuned_score = 0.0

            report_lines.append(f"## Example {idx}")
            report_lines.append("")
            report_lines.append("**Request**")
            report_lines.append("")
            report_lines.append(str(getattr(ex, "request", "")).strip())
            report_lines.append("")
            report_lines.append("**Expected (label)**")
            report_lines.append("")
            report_lines.append(str(getattr(ex, "response", "")).strip())
            report_lines.append("")
            report_lines.append(f"**Baseline score:** {base_score:.2%}")
            report_lines.append("")
            report_lines.append("```\n" + ("\n".join(base_lines)).strip() + "\n```")
            report_lines.append("")
            report_lines.append(f"**Tuned score:** {tuned_score:.2%}")
            report_lines.append("")
            report_lines.append("```\n" + ("\n".join(tuned_lines)).strip() + "\n```")
            report_lines.append("")

        report_output.parent.mkdir(parents=True, exist_ok=True)
        report_output.write_text("\n".join(report_lines))
        print(f"Before/After report saved to {report_output}")
    except Exception as exc:  # pragma: no cover
        print("Failed to write tuning report:", exc)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--num-candidates",
        type=int,
        default=4,
        help="Number of candidate prompts to explore during teleprompting.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="Where to save the optimized prompt text.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print LM config and a baseline prediction for sanity checks.",
    )
    parser.add_argument(
        "--metric",
        choices=["fuzzy", "semantic"],
        default="fuzzy",
        help="Scoring metric to use during optimization.",
    )
    parser.add_argument(
        "--semantic-threshold",
        type=float,
        default=0.8,
        help="Similarity threshold for semantic metric (cosine). Default 0.65.",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=REPORT_PATH,
        help="Where to save before/after tuning report (Markdown).",
    )
    args = parser.parse_args()
    if args.debug:
        # Quick sanity: show LM and a raw prediction before tuning.
        # Ensure we attempt configuration before reporting.
        configure_lm_from_env()
        lm = getattr(dspy.settings, "lm", None)
        print("LM configured:", type(lm).__name__ if lm else None, getattr(lm, "model", None))
        try:
            trainset = build_training_dataset()
            pred = dspy.Predict(VideoIdeaSignature)(
                profile_context=getattr(trainset[0], "profile_context", ""),
                request=getattr(trainset[0], "request", ""),
            )
            print(
                "Baseline prediction sample:\n", str(getattr(pred, "response", "")).splitlines()[:5]
            )
        except Exception as exc:  # pragma: no cover
            print("Baseline prediction failed:", exc)
    main(
        args.num_candidates,
        args.output,
        args.metric,
        args.semantic_threshold,
        args.report_output,
    )
