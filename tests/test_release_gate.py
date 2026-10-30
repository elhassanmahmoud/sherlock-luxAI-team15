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
