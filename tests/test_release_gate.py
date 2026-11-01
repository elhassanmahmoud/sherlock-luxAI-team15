"""Uebernahme nur nach bestandener Bestaetigung (scripts/release_candidate.gate_passed, 30.10.2026)."""
from scripts.release_candidate import gate_passed


def test_gate_passed_accepts_confirmation_and_battle_confirmation_of_the_last_start(tmp_path):
    log = tmp_path / "gate.log"
    log.write_text("[30.10. 09:00] Start x (a.pth)\nGATE Bestaetigung: NICHT BESTANDEN\n"
                   "[30.10. 23:01] Battle-Bestaetigung: Start v11h (b.pth, SHA-256 13c7), Referenz V11\n"
                   "GATE Battle-Bestaetigung: BESTANDEN\n", encoding="utf-8")
    assert gate_passed(log, "v11h")
    assert not gate_passed(log, "x")
    assert not gate_passed(log, "y")
    log.write_text("[30.10. 23:01] Battle-Bestaetigung: Start v11h (b.pth)\nGATE Battle-Bestaetigung: NICHT BESTANDEN\n",
                   encoding="utf-8")
    assert not gate_passed(log, "v11h")


def test_gate_passed_accepts_the_targeted_nebula_confirmation(tmp_path):
    log = tmp_path / "gate.log"
    log.write_text("[01.11. 08:00] Nebel-25-Bestaetigung: Start v15cx (c.pth), Referenz V12\n"
                   "GATE Nebel-25-Bestaetigung: BESTANDEN\n", encoding="utf-8")
    assert gate_passed(log, "v15cx")
    log.write_text("[01.11. 08:00] Nebel-25-Bestaetigung: Start v15cx (c.pth)\nGATE Nebel-25-Bestaetigung: NICHT BESTANDEN\n",
                   encoding="utf-8")
    assert not gate_passed(log, "v15cx")


def test_gate_passed_separates_interleaved_confirmations_of_different_kinds(tmp_path):
    # wie experiments/pipeline_battle_gate.log am 01.11.: v17a startet, bevor v15cx sein Ergebnis hat
    log = tmp_path / "gate.log"
    log.write_text("[01.11. 04:27] Nebel-25-Bestaetigung: Start v15cx (c.pth), Referenz V12\n"
                   "GN_V12_n25.csv: default: 1.000 (600 Spiele)\n"
                   "[01.11. 07:56] Battle-Bestaetigung: Start v17a (d.pth), Referenz v12\n"
                   "GATE Nebel-25-Bestaetigung: BESTANDEN\n"
                   "[01.11. 09:04] Nebel-25-Bestaetigung v15cx fertig\n"
                   "GATE Battle-Bestaetigung: NICHT BESTANDEN\n", encoding="utf-8")
    assert gate_passed(log, "v15cx")
    assert not gate_passed(log, "v17a")
    # umgekehrt: das Battle-BESTANDEN gehoert nicht zum Nebel-Kandidaten
    log.write_text("[01.11. 04:27] Nebel-25-Bestaetigung: Start v15cx (c.pth)\n"
                   "[01.11. 07:56] Battle-Bestaetigung: Start v17a (d.pth)\n"
                   "GATE Battle-Bestaetigung: BESTANDEN\n"
                   "GATE Nebel-25-Bestaetigung: NICHT BESTANDEN\n", encoding="utf-8")
    assert not gate_passed(log, "v15cx")
    assert gate_passed(log, "v17a")
    # zwei Starts derselben Art vor dem Ergebnis: nicht zuordenbar
    log.write_text("[01.11. 07:56] Battle-Bestaetigung: Start a (a.pth)\n"
                   "[01.11. 08:56] Battle-Bestaetigung: Start b (b.pth)\n"
                   "GATE Battle-Bestaetigung: BESTANDEN\n", encoding="utf-8")
    assert not gate_passed(log, "a")
    assert gate_passed(log, "b")


def test_gate_passed_skips_summary_lines_of_old_logs(tmp_path):
    # Form von experiments/pipeline_v10.log (22.10.)
    log = tmp_path / "gate.log"
    log.write_text("[08:24] Start V8st (v10.pth, SHA-256 03cf) gegen REF v7.pth\n"
                   "GATE Auswahl: Solution_92 0.9300 vs 0.8600 -> BESTANDEN\n"
                   "GATE Bestaetigung: Solution_92 0.9031 vs Referenz 0.8281, Δ +7.50 pp\n"
                   "GATE Bestaetigung: BESTANDEN\n", encoding="utf-8")
    assert gate_passed(log, "V8st")
