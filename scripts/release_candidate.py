"""Bestaetigten Kandidaten als Abgabe einsetzen (Verfahren wie am 20.10.2026, CLAUDE.md-Freigabe).

    .venv/bin/python -m scripts.release_candidate --candidate experiments/ensembles/v6_Bs.pth \
        --label v6_Bs --gate-log experiments/pipeline_v6.log --gate-name Bs [--dry-run]

Bricht ab, wenn im Gate-Log fuer den Kandidaten nicht "GATE Bestaetigung: BESTANDEN" (bzw. "GATE Battle-
Bestaetigung: BESTANDEN") steht.
1. bisherige Abgabe (beide Dateien) bytegleich nach experiments/releases/<datum>_<alt>/ sichern
   (Manifest + Wiederherstellungsanleitung), 2. Kandidat installieren und Hashes pruefen,
3. Kurs-Runner-Pruefung der installierten Datei, 4. Uebernahme-Manifest schreiben.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEIGHTS = ROOT / "agents" / "sherlock" / "weights"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def gate_passed(log: Path, name: str) -> bool:
    lines = log.read_text(encoding="utf-8").splitlines()
    start = max((i for i, ln in enumerate(lines) if f"Start {name} (" in ln), default=None)
    if start is None:
        return False
    # 30.10.2026: nur bis zum Start des naechsten Kandidaten; auch die Battle-Bestaetigung (scripts/battle_confirm.sh)
    for ln in lines[start + 1:]:
        if re.search(r"\bStart \S+ \(", ln):
            return False
        if "GATE Bestaetigung: BESTANDEN" in ln or "GATE Battle-Bestaetigung: BESTANDEN" in ln:
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--old-label", default="all18_v3")
    ap.add_argument("--gate-log", type=Path, required=True)
    ap.add_argument("--gate-name", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not gate_passed(args.gate_log, args.gate_name):
        print("ABBRUCH: keine bestandene Bestaetigung im Gate-Log")
        return 1
    p0, p1 = WEIGHTS / "agent_p0.pth", WEIGHTS / "agent_p1.pth"
    old = sha(p0)
    if sha(p1) != old:
        print("ABBRUCH: agent_p0/agent_p1 unterschiedlich")
        return 1
    cand = sha(args.candidate)
    day = datetime.now().strftime("%Y%m%d")
    backup = ROOT / "experiments" / "releases" / f"{day}_{args.old_label}"
    print(f"bisherige Abgabe {old}\nKandidat {cand}\nSicherung {backup}")
    if args.dry_run:
        return 0
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if not backup.exists():
        backup.mkdir(parents=True)
        files = []
        for src in (p0, p1):
            dst = backup / src.name
            shutil.copyfile(src, dst)
            assert sha(dst) == old
            files.append(dict(original_path=str(src.relative_to(ROOT)), backup_file=src.name,
                              sha256=old, bytes=dst.stat().st_size))
        (backup / "manifest.json").write_text(json.dumps(dict(
            saved_at=day, label=args.old_label, source_commit=commit,
            reason=f"Rollback copy before promotion of {args.label}", files=files), indent=2))
        (backup / "README.md").write_text(
            f"# Sicherung der Abgabe {args.old_label}\n\nBytegleiche Kopien vor der Uebernahme von "
            f"`{args.label}` ({day}). SHA-256 beider Dateien: `{old}`.\n\n"
            "## Wiederherstellen (vom Projektverzeichnis, bei gestoppten Laeufen)\n\n```bash\n"
            f"shasum -a 256 {backup.relative_to(ROOT)}/agent_p0.pth {backup.relative_to(ROOT)}/agent_p1.pth\n"
            f"cp {backup.relative_to(ROOT)}/agent_p0.pth agents/sherlock/weights/agent_p0.pth\n"
            f"cp {backup.relative_to(ROOT)}/agent_p1.pth agents/sherlock/weights/agent_p1.pth\n"
            "shasum -a 256 agents/sherlock/weights/agent_p0.pth agents/sherlock/weights/agent_p1.pth\n```\n\n"
            "Danach Kurspruefung (`python -m scripts.check_candidate_runner`) und eigenen Commit.\n",
            encoding="utf-8")
    for dst in (p0, p1):
        shutil.copyfile(args.candidate, dst)
    assert sha(p0) == sha(p1) == cand
    out = ROOT / "experiments" / "analysis" / f"release_{args.label}_runner_installed.json"
    if out.exists():
        out.unlink()
    rc = subprocess.call([sys.executable, "-m", "scripts.check_candidate_runner", "--weights", str(p0),
                          "--out", str(out)], cwd=ROOT)
    manifest = dict(
        label=args.label, status="installed_and_verified" if rc == 0 else "installed_runner_check_failed",
        installed_at=datetime.now(timezone.utc).isoformat(), code_commit=commit,
        candidate=str(args.candidate), candidate_sha256=cand,
        installed_sha256={str(p.relative_to(ROOT)): sha(p) for p in (p0, p1)},
        rollback_manifest=str((backup / "manifest.json").relative_to(ROOT)),
        rollback_readme=str((backup / "README.md").relative_to(ROOT)),
        gate_log=str(args.gate_log), runner_report=str(out.relative_to(ROOT)))
    (ROOT / "experiments" / "releases" / f"{day}_{args.label}.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
