"""Nachtraining (scripts.finetune): Config-Variante, Liga-Gegner im Mix, Endstand behalten."""
import csv
import json
import sys

import pytest

from agents.sherlock.main import Agent_x
from scripts import finetune
from scripts.variants import variant_cfg


def test_mix_accepts_league_opponents_and_rejects_unknown():
    mix = finetune.parse_mix("solution92=0.4,sol92_sq=0.3,sol92_weak=0.1,pool=0.1,rush=0.1", 0.5)
    assert mix["sol92_sq"] == 0.3 and abs(sum(mix.values()) - 1) < 1e-9
    assert finetune.parse_mix(None, 0.7) == {"solution92": 0.7, "default": pytest.approx(0.3)}
    with pytest.raises(SystemExit):
        finetune.parse_mix("solution92=0.5,self=0.5", 0.5)
    with pytest.raises(SystemExit):
        finetune.parse_mix("solution92=0.5,default=0.4", 0.5)


def test_finetune_with_v10_rules_and_league_mix_keeps_final_weights(tmp_path, monkeypatch):
    init = tmp_path / "init"
    (init / "weights").mkdir(parents=True)
    Agent_x("player_0", cfg=variant_cfg("full_rules"), seed=1).save_agent(str(init / "weights" / "agent.pth"))
    (init / "manifest.json").write_text(json.dumps({"variant": "full_rules", "train_games": 0}))
    runs = tmp_path / "runs"
    monkeypatch.setattr(finetune, "RUNS", runs)
    monkeypatch.setattr(sys, "argv", [
        "finetune", "--init", str(init), "--name", "ft", "--games", "2", "--val-every", "2",
        "--n-val", "1", "--prefill-games", "0", "--no-test", "--keep-final", "--seed", "1",
        "--variant", "full_rules_v10", "--mix", "sol92_sq=0.5,sol92_weak=0.5"])
    finetune.main()

    man = json.loads((runs / "ft" / "manifest.json").read_text())
    assert man["status"] == "done" and man["base_variant"] == "full_rules_v10"
    assert man["selection"].startswith("Endstand") and man["config"]["sap_still"]
    with open(runs / "ft" / "train.csv") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 2 and {r["opponent"] for r in rows} <= {"sol92_sq", "sol92_weak"}
    assert (runs / "ft" / "weights" / "agent.pth").is_file()
    assert (init / "weights" / "agent.pth").is_file()  # Init-Lauf bleibt unveraendert

    monkeypatch.setattr(sys, "argv", ["finetune", "--init", str(init), "--name", "ft", "--games", "2"])
    with pytest.raises(SystemExit):  # bestehender Lauf wird nicht ueberschrieben
        finetune.main()
