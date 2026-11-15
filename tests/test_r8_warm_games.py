from collections import Counter
from types import SimpleNamespace

import pytest

from scripts import r8_warm_games as games


def receipt():
    example=dict(archives=[],per_map={},totals={},old_reference=games.OLD_REPORT,
                 checks=dict(new_beats_r3=True,new_beats_warm_control=True,old_at_least_r3=True),
                 passes_offline_gate=True)
    for name,maps in games.DIAGNOSIS.items():
        per_map={}
        all_counts=Counter()
        for seed in maps:
            both=Counter()
            for seat in games.SEATS:
                c=dict(rows=3255+int(name=="old_validation" and (seed-maps.start)*2+int(seat[-1])<3),
                       v14_correct=9,r3_correct=8,control_correct=8,r8_correct=9,
                       r8_gained_over_r3=2,r8_lost_from_r3=1,r8_gained_over_control=1,r8_lost_from_control=0)
                if name=="old_validation":
                    i=(seed-maps.start)*2+int(seat[-1])
                    part=lambda total:total//48 + int(i<total%48)
                    c.update(r3_correct=part(98938),v14_correct=part(82581),r3_hurt_correct_v14=part(2343))
                    c.update(control_correct=c["r3_correct"],r8_correct=c["r3_correct"]+1)
                example["archives"].append(dict(seed=seed,side=seat,opponent=games.opponent_for(seed),sha256="a"*64,
                                                  protocol=games.PROTOCOLS[name],counts=c,cohort=name))
                both.update(c)
            per_map[str(seed)]=dict(both)
            all_counts.update(both)
        example["per_map"][name]=per_map
        example["totals"][name]=dict(all_counts)
    return example


def test_registered_outcomes_reject_duplicate_diagnoses_and_modified_totals():
    report=receipt()
    games.verified_offline(report)
    report["archives"][1]["side"]="player_0"
    with pytest.raises(ValueError):
        games.verified_offline(report)
    report=receipt()
    report["totals"]["new_validation"]["r8_correct"]+=1
    with pytest.raises(ValueError):
        games.verified_offline(report)


def test_panel_counts_and_strict_comparisons():
    screen,confirm=games.blocks("screen"),games.blocks("confirm")
    assert {arm:2*len(maps)*len(foes) for arm,(maps,foes) in screen.items()}=={"r8":96,"v14":64,"r3":64,"control":64}
    assert sum(2*len(maps)*len(foes) for maps,foes in confirm.values())==600
    assert len(set(screen["r8"][0])|set(confirm["r8"][0])|set(confirm["direct"][0]))==16+60+60
    def c(ext,sol):
        return dict(external={"net_wins":ext},by_opponent={"solution92":{"net_wins":sol}})
    assert all(games.control_gates(c(1,0),c(1,-1)).values())
    assert not all(games.control_gates(c(0,0),c(1,1)).values())
    assert not all(games.control_gates(c(1,0),c(0,1)).values())
    assert not all(games.control_gates(c(2,-1),c(2,0)).values())


def test_confirm_requires_sealed_positive_screen(monkeypatch,tmp_path):
    a=SimpleNamespace(out=tmp_path)
    fresh={"game_gates_pass":True}
    monkeypatch.setattr(games,"report",lambda *args:fresh)
    with pytest.raises(ValueError):
        games.verified_selection(a)
    path=tmp_path/"screen/assessment.json"
    path.parent.mkdir()
    path.write_text('{"game_gates_pass":true}')
    assert games.verified_selection(a)==games.game.digest(path)
    fresh["game_gates_pass"]=False
    with pytest.raises(ValueError):
        games.verified_selection(a)


def test_admission_binds_both_models_and_executed_fit_sources(tmp_path,monkeypatch):
    import json

    r=receipt()
    models=tmp_path/"models"
    models.mkdir()
    r3=tmp_path/"r3.pth"
    r3.write_bytes(b"anchored parent")
    paths={"r3":r3,"control":models/"control.pth","r8":models/"r8.pth"}
    paths["control"].write_bytes(b"warm control")
    paths["r8"].write_bytes(b"on policy")
    r["models"]={k:games.game.digest(p) for k,p in paths.items()}
    monkeypatch.setattr(games,"R3",r["models"]["r3"])
    source=tmp_path/"fit"
    (source/"scripts").mkdir(parents=True)
    r["source_sha256"]={}
    for f in ("scripts/r8_warm.py","scripts/r8_warm_assess.py","scripts/imitate.py"):
        (source/f).write_text(f)
        r["source_sha256"][f]=games.game.digest(source/f)
    audit=tmp_path/"validation.json"
    audit.write_text(json.dumps(r))
    a=SimpleNamespace(models=models,r3=r3,fit_root=source,audit=audit,audit_sha256=games.game.digest(audit))
    assert games.admission(a)["models"]==r["models"]
    paths["r8"].write_bytes(b"warm control")
    with pytest.raises(ValueError):
        games.admission(a)
    paths["r8"].write_bytes(b"on policy")
    (source/"scripts/r8_warm.py").write_text("changed")
    with pytest.raises(ValueError):
        games.admission(a)
