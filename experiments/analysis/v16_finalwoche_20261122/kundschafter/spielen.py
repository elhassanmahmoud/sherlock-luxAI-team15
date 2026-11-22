"""Technischer Vier-Sitz-Vergleich, danach optional der getrennte vorab festgelegte Vergleich."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

from kandidat import PACKAGE, ROOT, Scout
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads

HERE = Path(__file__).resolve().parent
DIGEST = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
KEEP = ("our_wins", "opp_wins", "our_points", "opp_points", "game_win", "steps")


def passes(rows):
    def cases(tag):
        return {(r["seed"],r["side"]):r for r in rows if r["arm"]==tag}
    b,c=cases("v16"),cases("scout")
    expected = {(s,p) for s in (7261020,7267071) for p in ("player_0","player_1")}
    if (len(rows)!=8 or set(b)!=expected or set(c)!=expected or any(r["opponent"]!="solution92" for r in rows)):
        raise ValueError("Fehlende technische Vergleichsspiele")
    def earlier(r):
        return r["pair_turn"] if r["pair_turn"] is not None else 101
    improved=any(k[1]=="player_0" and earlier(c[k]) < earlier(b[k])
                 and (c[k]["known_at_third"]>b[k]["known_at_third"] or c[k]["our_wins"]>b[k]["our_wins"])
                 for k in b)
    no_loss=all(c[k]["game_win"]>=b[k]["game_win"] for k in b)
    return improved and no_loss


def technical_reference():
    path=ROOT/"experiments/analysis/devf_20261117/bestaetigung3_kandidat.csv"
    path5=ROOT/"experiments/analysis/devh_20261117/bestaetigung5_k.csv"
    rows={}
    for f in (path,path5):
        with f.open() as src:
            for row in csv.DictReader(src):
                if int(row["seed"]) in (7261020,7267071) and row["opponent"]=="solution92":
                    rows[int(row["seed"]),row["side"]]={k:int(row[k]) for k in KEEP}
    return rows


class MeasuredScout(Scout):
    """Passiver Zähler für nachträgliche Bestätigung eines aktiven Fernziels."""
    def new_game(self, side):
        super().new_game(side)
        self.confirmed_far_goal = []

    def act(self, step, obs):
        prev_goal = self.goal
        previously_active = self.enable and self.uid is not None and not self.finished
        before_n = len(self.changes)
        result = super().act(step, obs)
        belief = self.base._imitation.belief
        if (previously_active and prev_goal is not None and belief.match_idx == 1
                and belief.point_tiles[prev_goal] and belief.known_pairs() < 2 and not self.finished):
            self.confirmed_far_goal.append([int(belief.match_step),list(prev_goal),len(self.changes)>before_n])
        return result


def run(phase, out=None, resume=False):
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    if hashlib.sha256(PACKAGE.read_bytes()).hexdigest()!=DIGEST:
        raise ValueError("Abgabe stimmt nicht")
    tech=phase=="technik"
    if not tech:
        previous=json.loads((HERE/"technik.json").read_text())
        if (previous["v16_sha256"] != DIGEST or not passes(previous["rows"]) or previous["source_sha256"] != hashlib.sha256((HERE/"kandidat.py").read_bytes()).hexdigest()
                or previous["rules_sha256"] != hashlib.sha256((HERE/"PLAN.md").read_bytes()).hexdigest()):
            raise ValueError("Technische Eingangskriterien verfehlt")
    seeds=(7261020,7267071) if tech else range(94651000,94651016)
    opponents=("solution92",) if tech else ("solution92","kaggle3","v16")
    out=out or HERE/(phase+".json")
    if out.exists():
        raise FileExistsError(f"Ausgabe besteht: {out}. Zur Reproduktion --out in neuem Verzeichnis nutzen.")
    progress = out.with_suffix(".progress.jsonl")
    if progress.exists() and not resume:
        raise FileExistsError(f"Gesicherte Teilergebnisse vorhanden: {progress}")
    check=technical_reference()
    env=LuxAIS3GymEnv(numpy_output=True)
    rows=[json.loads(line) for line in progress.read_text().splitlines()] if resume else []
    expected_keys = [(s,p,o,a) for s in seeds for p in ("player_0","player_1") for o in opponents
                     for a in (("scout",) if o=="v16" else ("v16","scout"))]
    completed=[(r["seed"],r["side"],r["opponent"],r["arm"]) for r in rows]
    if completed != expected_keys[:len(completed)] or any(r["steps"]!=303 for r in rows):
        raise ValueError("Teilarchiv passt nicht zum geplanten Panel")
    completed=set(completed)
    for seed in seeds:
        for side in ("player_0","player_1"):
            other="player_1" if side=="player_0" else "player_0"
            for opp in opponents:
                for tag in (("scout",) if opp=="v16" else ("v16","scout")):
                    if (seed,side,opp,tag) in completed:
                        continue
                    me=MeasuredScout(side,tag=="scout")
                    enemy=Scout(other,False) if opp=="v16" else make_opponent(opp,other)
                    row=play_game(env,me,enemy,seed,side,False)
                    core={k:row[k] for k in KEEP}
                    if row["steps"]!=303 or getattr(me.base,"caught_errors",0) or getattr(me.base._imitation,"caught_errors",0):
                        raise ValueError("Partie technisch unvollständig")
                    if opp=="v16" and (enemy.base.caught_errors or getattr(enemy.base._imitation,"caught_errors",0)):
                        raise ValueError("Fehler im direkten V16-Gegner")
                    if tech and tag=="v16" and core!=check[seed,side]:
                        raise ValueError(f"Repro {seed} {side}: {core} vs {check[seed,side]}")
                    rows.append(dict(seed=seed,side=side,opponent=opp,arm=tag,**core,
                                     start=me.start,uid=me.uid,reason=me.reason,changes=me.changes,
                                     pair_turn=me.pair_turn,known_at_third=me.known_at_third,confirmed_far_goal=me.confirmed_far_goal))
                    with progress.open("a") as log:
                        log.write(json.dumps(rows[-1],separators=(",",":"))+"\n")
                        log.flush()
                        os.fsync(log.fileno())
                    print(phase,tag,opp,seed,side,"Änderungen",len(me.changes),"Sichtung",me.pair_turn,"Felder",me.known_at_third,"Matches",row["our_wins"],flush=True)
    artifact={"v16_sha256":DIGEST,"rules_sha256":hashlib.sha256((HERE/"PLAN.md").read_bytes()).hexdigest(),
              "source_sha256":hashlib.sha256((HERE/"kandidat.py").read_bytes()).hexdigest(),"phase":phase,"rows":rows}
    if tech:
        artifact["weiter"]=passes(rows)
    temporary = out.with_suffix(".tmp")
    temporary.write_text(json.dumps(artifact,indent=2)+"\n")
    temporary.replace(out)
    if [json.loads(line) for line in progress.read_text().splitlines()] != rows:
        raise ValueError("Abweichende Teilergebnisse")
    progress.unlink()


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("phase",choices=("technik","frisch"))
    ap.add_argument("--out",type=Path)
    ap.add_argument("--resume",action="store_true")
    args=ap.parse_args()
    run(args.phase,args.out,args.resume)
