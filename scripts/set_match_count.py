"""Kursregel umsetzen: 3 Matches pro Spiel in der installierten luxai_s3 (params.py).

    python -m scripts.set_match_count          # setzt 3 (idempotent)
    python -m scripts.set_match_count --check  # nur pruefen, Exit-Code 1 wenn != 3
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PATTERN = re.compile(r"(match_count_per_episode\s*:\s*int\s*=\s*)(\d+)")


def params_file() -> Path:
    import luxai_s3

    return Path(luxai_s3.__file__).parent / "params.py"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    p = params_file()
    text = p.read_text()
    m = PATTERN.search(text)
    if not m:
        sys.exit(f"match_count_per_episode nicht gefunden in {p}")
    current = int(m.group(2))
    if args.check:
        print(f"{p}: match_count_per_episode = {current}")
        sys.exit(0 if current == args.count else 1)
    if current != args.count:
        p.write_text(PATTERN.sub(rf"\g<1>{args.count}", text, count=1))
    print(f"{p}: match_count_per_episode {current} -> {args.count}")


if __name__ == "__main__":
    main()
