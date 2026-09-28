"""Benchmark Faultless review latency, token usage and output robustness.

Bypasses Django and the web flow but reproduces the production review path: rules
are read from ``db.sqlite3``, prompts are built with the same template as
``prompt.py``, each rule is sent to the model sequentially (as in production), and
responses are parsed with the same ``JsonOutputParser`` that ``ai_output`` uses.

Usage (run from the repository root)::

    python bench/run_bench.py                  # all .docx files in bench/reports/
    python bench/run_bench.py --reports <dir>  # a different report folder
    python bench/run_bench.py --langfuse       # also send traces to Langfuse

Results are written to ``bench/results/bench_<timestamp>.json`` and a summary is
printed to the terminal.
"""

import argparse
import hashlib
import json
import sqlite3
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
MYSITE = ROOT / "src" / "faultless" / "mysite"
sys.path.insert(0, str(MYSITE))  # make `import faultless` resolve to the Django app

from dotenv import load_dotenv  # noqa: E402
from langchain_core.exceptions import OutputParserException  # noqa: E402
from langchain_core.output_parsers import JsonOutputParser  # noqa: E402

load_dotenv(ROOT / ".env")

from faultless.extract import extract_chunks  # noqa: E402
from faultless.llm_factory import get_chat_model, model_name  # noqa: E402

# ai_output parses with JsonOutputParser, so the benchmark uses the same parser to keep
# the numbers comparable. It silently repairs truncated JSON by dropping the tail, and
# the last match may lose fields. Truncation and incomplete matches are therefore
# counted separately instead of being reported as plain successes.
PARSER = JsonOutputParser()
REQUIRED_KEYS = {"error_type", "message", "original"}
ERROR_PREVIEW = 200

# Identical to the template in prompt.py (typos included) so that the benchmark
# measures the prompts that actually run in production.
PROMPT_HEADER = (
    "You are a proofreader, designed to review an engineering report(it might contains "
    "sepcial words in engineering area so please be careful when you review) and find "
    "all the errors in it, please use the original report to find all the errors before "
    "you modify it. below there are some rules that help you to check the report\n"
)


def build_prompt(rule: dict[str, Any], report_text: str) -> str:
    """Build a rule prompt exactly as ``prompt.py`` registers it in Langfuse."""
    fmt = str(rule["output_format"]).strip().replace("{", " ").replace("}", " ")
    return (
        f"{PROMPT_HEADER}\n"
        f"error name: {rule['name']}\n"
        f"{rule['description']}\n"
        "return in a json object with following structure:\n"
        f"{fmt}\n\n"
        "Report: \n\n"
        f"{report_text}"
    )


def load_rules(db_path: Path) -> list[dict[str, Any]]:
    """Read all review rules from the Django SQLite database."""
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    query = "select name, scale, description, output_format from faultless_rules"
    rows = [dict(r) for r in con.execute(query)]
    con.close()
    return rows


def read_report(path: Path, *, include_tables: bool, chunk_chars: int) -> list[str]:
    """Return the review units: one whole-document string, or section chunks."""
    if chunk_chars <= 0:
        whole = extract_chunks(path, include_tables=include_tables, max_chars=10**9)
        return ["\n".join(whole)]
    return extract_chunks(path, include_tables=include_tables, max_chars=chunk_chars)


def parse_response(content: str) -> dict[str, Any]:
    """Parse a model response with the production parser and check match fields."""
    try:
        data = PARSER.parse(content)
    except OutputParserException as e:
        return {"ok": False, "stage": "parse", "error": str(e)[:ERROR_PREVIEW]}
    matches = data.get("matches", []) if isinstance(data, dict) else []
    incomplete = sum(1 for m in matches if not (isinstance(m, dict) and m.keys() >= REQUIRED_KEYS))
    # Hash the quoted text so the results file holds no client content.
    keys = [
        hashlib.sha1(  # noqa: S324 - a stable digest for de-duplication, not security
            str(m.get("original", "")).strip().lower().encode()
        ).hexdigest()[:12]
        for m in matches
        if isinstance(m, dict)
    ]
    return {
        "ok": True,
        "n_matches": len(matches),
        "incomplete_matches": incomplete,
        "match_keys": keys,
    }


def call_model(model: Any, prompt: str, callbacks: list[Any] | None) -> dict[str, Any]:
    """Send one prompt, then record latency, token usage and parse outcome."""
    t0 = time.perf_counter()
    try:
        resp = model.invoke(prompt, config={"callbacks": callbacks} if callbacks else None)
    except Exception as e:  # noqa: BLE001 - network or rate-limit errors must not abort the run
        latency = time.perf_counter() - t0
        return {"ok": False, "stage": "api", "error": str(e)[:ERROR_PREVIEW], "latency_s": latency}
    latency = time.perf_counter() - t0

    usage = getattr(resp, "usage_metadata", None) or {}
    meta = getattr(resp, "response_metadata", None) or {}
    rec = {
        "latency_s": round(latency, 3),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "finish_reason": meta.get("finish_reason"),
    }
    # A finish_reason of "length" means the output hit max_tokens and was cut off.
    rec["truncated"] = rec["finish_reason"] == "length"

    content = (resp.content or "").strip()
    if not content:
        return {**rec, "ok": False, "stage": "empty", "error": "empty response"}
    return {**rec, **parse_response(content)}


def _stats(values: list[float | None]) -> dict[str, float] | None:
    xs = [x for x in values if x is not None]
    if not xs:
        return None
    return {
        "mean": round(statistics.mean(xs), 2),
        "median": round(statistics.median(xs), 2),
        "min": round(min(xs), 2),
        "max": round(max(xs), 2),
    }


def _per_rule(records: list[dict[str, Any]], *, unique: bool) -> dict[str, Any]:
    """Aggregate matches per rule per run, so chunked and whole-document runs compare."""
    names = dict.fromkeys(r["rule"] for r in records)
    runs = sorted({r.get("run", 1) for r in records})
    out = {}
    for name in names:
        totals = []
        for run_no in runs:
            rows = [r for r in records if r["rule"] == name and r.get("run", 1) == run_no]
            if unique:
                totals.append(len({k for r in rows for k in r.get("match_keys", [])}))
            else:
                totals.append(sum(r.get("n_matches") or 0 for r in rows))
        out[name] = _stats(totals)
    return out


def summarize(records: list[dict[str, Any]], per_report: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-call records into benchmark-level metrics."""
    calls = len(records)
    ok = [r for r in records if r.get("ok")]
    failures: dict[str, int] = {}
    for r in records:
        if not r.get("ok"):
            stage = r.get("stage", "unknown")
            failures[stage] = failures.get(stage, 0) + 1

    return {
        "model": model_name(),
        "reports": len(per_report),
        "total_matches": sum(r.get("n_matches") or 0 for r in records),
        "calls": calls,
        "call_success_rate": round(len(ok) / calls, 4) if calls else None,
        "failures_by_stage": failures,
        "truncated_calls": sum(1 for r in records if r.get("truncated")),
        # Truncated but still parsed: production would silently lose results here.
        "silently_truncated_calls": sum(1 for r in records if r.get("truncated") and r.get("ok")),
        # Matches missing error_type, message or original make summary.py raise KeyError.
        "incomplete_matches": sum(r.get("incomplete_matches") or 0 for r in records),
        "per_report_latency_s": _stats([p["latency_s"] for p in per_report]),
        "per_report_input_tokens": _stats([p["input_tokens"] for p in per_report]),
        "per_report_output_tokens": _stats([p["output_tokens"] for p in per_report]),
        "per_call_latency_s": _stats([r.get("latency_s") for r in records]),
        "matches_per_call": _stats([r.get("n_matches") for r in ok]),
        "matches_per_rule": _per_rule(records, unique=False),
        "unique_matches_per_rule": _per_rule(records, unique=True),
        "failed_calls_per_rule": {
            name: sum(1 for r in records if r["rule"] == name and not r.get("ok"))
            for name in dict.fromkeys(r["rule"] for r in records)
        },
        "total_matches_per_run": [
            sum(r.get("n_matches") or 0 for r in records if r.get("run") == run_no)
            for run_no in sorted({r.get("run", 1) for r in records})
        ],
    }


def print_summary(s: dict[str, Any], out: Path) -> None:
    """Print the aggregated metrics."""
    print("\n" + "=" * 60)
    print(f"  Summary ({s['model']})")
    print("=" * 60)
    print(
        f"Reports {s['reports']} / calls {s['calls']} / "
        f"call success rate {s['call_success_rate']:.1%}"
    )
    if s["failures_by_stage"]:
        print(f"Failures by stage: {s['failures_by_stage']}")
    if s["truncated_calls"]:
        print(
            f"WARNING truncated outputs: {s['truncated_calls']} "
            f"(silently accepted by the parser: {s['silently_truncated_calls']})"
        )
    if s["incomplete_matches"]:
        print(f"WARNING incomplete matches: {s['incomplete_matches']} (summary.py would KeyError)")
    labels = [
        ("per_report_latency_s", "Latency per report (s)"),
        ("per_report_input_tokens", "Input tokens per report"),
        ("per_report_output_tokens", "Output tokens per report"),
    ]
    for key, label in labels:
        v = s[key]
        if v:
            print(
                f"{label:26s} mean {v['mean']}  median {v['median']}  "
                f"range {v['min']}-{v['max']}"
            )
    print(f"Total matches reported: {s['total_matches']}")
    runs = s["total_matches_per_run"]
    if len(runs) > 1:
        print(f"Per run: {runs}  (mean {statistics.mean(runs):.1f}, range {min(runs)}-{max(runs)})")
    print("\nMatches per rule per run (mean / range; unique = de-duplicated by quoted text):")
    for name, v in s["matches_per_rule"].items():
        u = s["unique_matches_per_rule"].get(name)
        failed = s["failed_calls_per_rule"].get(name, 0)
        note = f"   {failed} failed call(s)" if failed else ""
        if v:
            print(
                f"  {name:34s} {v['mean']:7.1f}  ({v['min']:.0f}-{v['max']:.0f})"
                f"   unique {u['mean']:6.1f}{note}"
            )
    print(f"\nDetailed results: {out}")


def run(  # noqa: PLR0913 - a benchmark entry point with independent switches
    reports: list[Path],
    rules: list[dict[str, Any]],
    *,
    use_langfuse: bool,
    include_tables: bool,
    repeat: int = 1,
    chunk_chars: int = 0,
) -> Path:
    """Review every report against every rule and write the results file."""
    model = get_chat_model(json_mode=True, temperature=0)
    callbacks = None
    if use_langfuse:
        from langfuse.callback import CallbackHandler

        callbacks = [CallbackHandler()]

    records: list[dict[str, Any]] = []
    per_report: list[dict[str, Any]] = []
    jobs = [(run_no, path) for run_no in range(1, repeat + 1) for path in reports]
    for i, (run_no, path) in enumerate(jobs, 1):
        chunks = read_report(path, include_tables=include_tables, chunk_chars=chunk_chars)
        chars = sum(len(c) for c in chunks)
        agg = {"report": path.name, "run": run_no, "chars": chars, "latency_s": 0.0}
        agg["chunks"] = len(chunks)
        agg.update(input_tokens=0, output_tokens=0)
        suffix = f"  run {run_no}/{repeat}" if repeat > 1 else ""
        parts = f", {len(chunks)} chunks" if len(chunks) > 1 else ""
        print(f"[{i}/{len(jobs)}] {path.name}  ({chars} chars{parts}){suffix}")
        for rule in rules:
            rule_records = []
            for ci, chunk in enumerate(chunks, 1):
                r = call_model(model, build_prompt(rule, chunk), callbacks)
                r.update({"report": path.name, "rule": rule["name"], "run": run_no, "chunk": ci})
                records.append(r)
                rule_records.append(r)
                for key in ("latency_s", "input_tokens", "output_tokens"):
                    agg[key] += r.get(key) or 0
            ok_n = sum(1 for r in rule_records if r.get("ok"))
            total = sum(r.get("n_matches") or 0 for r in rule_records)
            unique = len({k for r in rule_records for k in r.get("match_keys", [])})
            secs = sum(r.get("latency_s") or 0 for r in rule_records)
            mark = "OK  " if ok_n == len(rule_records) else "FAIL"
            fails = (
                "" if ok_n == len(rule_records) else f"  {len(rule_records) - ok_n} call(s) failed"
            )
            print(
                f"    {mark} {rule['name']:32s} {secs:5.1f}s  "
                f"{total} matches ({unique} unique){fails}"
            )
        agg["latency_s"] = round(agg["latency_s"], 3)
        per_report.append(agg)

    summary = summarize(records, per_report)
    out_dir = ROOT / "bench" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"bench_{datetime.now(tz=UTC):%Y%m%d_%H%M%S}.json"
    payload = {"summary": summary, "per_report": per_report, "calls": records}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print_summary(summary, out)
    return out


def main() -> None:
    """Parse arguments and run the benchmark."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--reports", default=str(ROOT / "bench" / "reports"))
    ap.add_argument("--db", default=str(MYSITE / "db.sqlite3"))
    ap.add_argument("--langfuse", action="store_true", help="also send traces to Langfuse")
    ap.add_argument("--repeat", type=int, default=1, help="run the whole set N times")
    ap.add_argument(
        "--chunk",
        type=int,
        default=0,
        metavar="CHARS",
        help="review the report in section-sized chunks of at most CHARS characters",
    )
    ap.add_argument(
        "--no-tables",
        action="store_true",
        help="reproduce the old paragraph-only extraction, for an A/B comparison",
    )
    args = ap.parse_args()

    reports = sorted(Path(args.reports).glob("*.docx"))
    if not reports:
        sys.exit(f"No .docx reports found in {args.reports}")

    rules = load_rules(Path(args.db))
    print(
        f"Model: {model_name()} | {len(rules)} rules | {len(reports)} reports | "
        f"{len(rules) * len(reports) * args.repeat} calls\n"
    )
    run(
        reports,
        rules,
        use_langfuse=args.langfuse,
        include_tables=not args.no_tables,
        repeat=args.repeat,
        chunk_chars=args.chunk,
    )


if __name__ == "__main__":
    main()
