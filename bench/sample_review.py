"""Sample reported issues for manual verification, then score precision.

The benchmark records how many issues each rule reports, not what they are.
A raw count says nothing about usefulness: 104 grammar issues in a 5,400-word
report is either a very poor report or a very noisy rule. This script runs one
rule, draws a random sample of its output, and writes a worksheet to label each
item as a true finding or a false positive.

Usage (run from the repository root)::

    # 1. Run one rule and write a worksheet
    python bench/sample_review.py --report bench/reports/<file>.docx \
        --rule "Grammar and Spelling Check" --n 20

    # 2. Open the CSV, fill the `verdict` column with t (true) or f (false)

    # 3. Score it
    python bench/sample_review.py --score bench/review/<file>.csv

The worksheet contains client text, so bench/review/ is git-ignored.
"""

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
MYSITE = ROOT / "src" / "faultless" / "mysite"
sys.path.insert(0, str(MYSITE))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from run_bench import PARSER, build_prompt, load_rules, read_report  # noqa: E402

from faultless.llm_factory import get_chat_model  # noqa: E402

REVIEW_DIR = ROOT / "bench" / "review"
FIELDS = ["id", "error_type", "original", "message", "verdict", "note"]
SEED = 42
PREVIEW = 400


def collect_matches(report: Path, rule_name: str) -> list[dict[str, Any]]:
    """Run a single rule over a report and return its reported matches."""
    rules = [r for r in load_rules(MYSITE / "db.sqlite3") if r["name"] == rule_name]
    if not rules:
        sys.exit(f"No rule named {rule_name!r} in the database")

    # Whole document in one call, matching the unchunked production path.
    text = read_report(report, include_tables=True, chunk_chars=0)[0]
    model = get_chat_model(json_mode=True, temperature=0)
    print(f"Running {rule_name!r} on {report.name} ({len(text)} chars)...")
    resp = model.invoke(build_prompt(rules[0], text))
    data = PARSER.parse(resp.content)
    matches = data.get("matches", []) if isinstance(data, dict) else []
    print(f"Reported {len(matches)} issues")
    return matches


def write_sheet(matches: list[dict[str, Any]], out: Path, n: int) -> None:
    """Write a random sample of matches to a worksheet for manual labelling."""
    rng = random.Random(SEED)
    sample = rng.sample(matches, min(n, len(matches)))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for i, m in enumerate(sample, 1):
            w.writerow(
                {
                    "id": i,
                    "error_type": str(m.get("error_type", ""))[:PREVIEW],
                    "original": str(m.get("original", ""))[:PREVIEW],
                    "message": str(m.get("message", ""))[:PREVIEW],
                    "verdict": "",
                    "note": "",
                }
            )
    print(f"\nWorksheet: {out}")
    print(f"Fill the `verdict` column with t or f for each of the {len(sample)} rows, then run:")
    print(f'    python bench/sample_review.py --score "{out}"')


def score(sheet: Path) -> None:
    """Compute precision from a filled worksheet."""
    with sheet.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    verdicts = [(r.get("verdict") or "").strip().lower() for r in rows]
    true_pos = sum(1 for v in verdicts if v in {"t", "true", "y", "yes", "1"})
    false_pos = sum(1 for v in verdicts if v in {"f", "false", "n", "no", "0"})
    blank = len(rows) - true_pos - false_pos

    if true_pos + false_pos == 0:
        sys.exit("No verdicts filled in yet")

    labelled = true_pos + false_pos
    precision = true_pos / labelled
    print(f"Labelled {labelled}/{len(rows)} rows" + (f" ({blank} blank)" if blank else ""))
    print(f"True findings   {true_pos}")
    print(f"False positives {false_pos}")
    print(f"Precision       {precision:.1%}")
    print(
        f"\nOn a run reporting N issues, roughly {(1 - precision) * 100:.0f}% of what an "
        f"engineer reads is noise."
    )


def main() -> None:
    """Parse arguments and dispatch."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--score", type=Path, help="score a filled worksheet")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--rule", default="Grammar and Spelling Check")
    ap.add_argument("--n", type=int, default=20)
    args = ap.parse_args()

    if args.score:
        score(args.score)
        return
    if not args.report:
        sys.exit("--report is required (or use --score)")

    matches = collect_matches(args.report, args.rule)
    if not matches:
        sys.exit("The rule reported no issues")

    slug = args.rule.split()[0].lower()
    raw = REVIEW_DIR / f"{args.report.stem}_{slug}_all.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"All matches: {raw}")
    write_sheet(matches, REVIEW_DIR / f"{args.report.stem}_{slug}_sample.csv", args.n)


if __name__ == "__main__":
    main()
