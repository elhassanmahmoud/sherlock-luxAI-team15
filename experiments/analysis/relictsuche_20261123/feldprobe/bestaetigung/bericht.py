"""Second implementation of held-out metrics plus a report including individual reversals and regions."""
import argparse
from collections import Counter
import csv
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent


def check(x,context):
    if not x:raise ValueError(context)


def number(x,signed=False):
    return format(float(x),"+.3f" if signed else ".3f").replace("-","−").replace(".",",")


def main(stage):
    d=HERE/("sicht1" if stage=="confirm" else "allgemein")
    study=json.loads((d/"manifest.json").read_bytes())
    result=json.loads((d/"ergebnis.json").read_bytes())
    prior=json.loads((d/"nachpruefung.json").read_bytes())
    with gzip.open(d/"partien.jsonl.gz","rt") as f:
        games=[json.loads(s) for s in f]
    seeds=study["cards"]
    arms=(("reference","solution92"),("probe","solution92"),("probe","v16"))
    get={(r["seed"],r["team"],r["arm"],r["opponent"]):r for r in games}
    check(len(get)==len(games)==len(seeds)*6,"Incomplete grid")
    c=Counter()
    act=Counter()
    play_by_region=Counter()
    map_region={}
    byseat={}
    differences=[]
    statuses={"neu":[],"weg":[]}
    mv=[]
    active_by={}
    for seed in seeds:
        vals=[]
        for team in range(2):
            ref,probe,duel=[get[seed,team,k,o] for k,o in arms]
            check(ref["sensor"]==probe["sensor"]==duel["sensor"],"Reset parameter")
            for r in (ref,probe,duel):
                m=r["matches"]
                tally=sum(x["win"] for x in m)
                check(r["win"]==int(tally>=2) and r["source"]==study["identity"] and
                      all([sum(row[t] for row in r["profile"][j*101:(j+1)*101]) for t in (0,1)]==m[j]["points"] for j in range(3))
                      and r["caught_errors"]==[0,0] and r["actions_checked"]==[303,303],"Raw result or final score")
                arm=r["arm"]+"_"+r["opponent"]
                c[arm]+=r["win"]
                byseat[arm,team]=byseat.get((arm,team),0)+r["win"]
                for i,m1 in enumerate(m):c[arm,i]+=m1["win"]
                if r["arm"]=="probe":
                    check(r["commands_vs_original"]==4848,"Missing original command checks")
                if r["sensor"]!=1:
                    check(r["event"] is None,"Scout changed with normal vision")
                if r["event"]:
                    e=r["event"]
                    d0=(sum(e["xy"])-23)*(1 if team==0 else -1)
                    z="eigene" if d0<0 else ("Achse" if d0==0 else "gegnerische")
                    a=r["opponent"]
                    play_by_region[a,z,"count"]+=1
                    play_by_region[a,z,"arrived"]+=int(e["arrived"])
                    play_by_region[a,z,"scored"]+=int(e["scored"])
                    play_by_region[a,z,"own"]+=r["profile"][e["t"]][0]
                    act[a,"match",e["t"]//101+1]+=1
                    active_by.setdefault(a,set()).add(seed)
                    map_region[a,seed,team]=z
            gain=0
            if probe["event"]:
                e=probe["event"]; t=e["t"]
                check(e["prefix"]==ref["prefix"][str(t)] and e["current"]==ref["current"][str(t)] and probe["profile"][:t]==ref["profile"][:t],
                      "Predecision actions and points differ")
                gain=probe["profile"][t][0]-ref["profile"][t][0]
                play_by_region["solution92",map_region["solution92",seed,team],"gain"]+=gain
                act["solution92","benefit",int(np.sign(gain))]+=1
            else:
                check(probe["hash"]==ref["hash"] and probe["matches"]==ref["matches"] and probe["profile"]==ref["profile"],"Inactive parity")
            delta=probe["win"]-ref["win"]
            if delta:statuses["neu" if delta>0 else "weg"].append(f"{seed} P{team}")
            vals.append((gain,delta,duel["win"]))
            mv.append((team,ref,probe,duel))
        differences.append(np.mean(vals,axis=0))
    x=np.asarray(differences)
    draws=np.random.default_rng(231123).integers(0,len(seeds),size=(20000,len(seeds)))
    estimates=x.mean(0);ci=np.percentile(x[draws].mean(1),[2.5,97.5],axis=0)
    for j,name in enumerate(("immediate_own_gain","solution_difference","direct_rate")):
        m=result[name]
        check(abs(m["mean"]-estimates[j])<1e-11 and np.allclose(m["ci95"],ci[:,j],atol=1e-11,rtol=0),name)
    if stage=="confirm":
        conditions=[bool(active_by.get("solution92") and active_by.get("v16")),ci[0,0]>0,estimates[1]>=0,estimates[2]>=.5,estimates[1]>0 or estimates[2]>.5]
        names=("observed_both","own_immediate_lower_positive","solution_no_fewer","direct_at_least_half","strict_whole_improvement")
        labels=("Auswertbare Eingriffe bei beiden Gegnern","Untere Grenze des sofortigen Punktegewinns über null",
                "Mindestens die V16-Gesamtsiegzahl gegen Solution","Mindestens die Hälfte der direkten Gesamtsiege",
                "Zusätzlicher Gesamtsieg gegen Solution oder direkter Vorsprung")
        passed=all(conditions)
    else:
        conditions=[ci[0,1]>0,estimates[2]>=.5,ci[0,2]>=.45,ci[0,2]>.5,ci[0,1]>=-.01]
        names=("route_a_solution_lower_positive","route_a_direct_mean","route_a_direct_lower","route_b_direct_lower","route_b_solution_lower")
        labels=("Weg A, untere Grenze Solution-Gesamtsieggewinn über null","Weg A, mindestens 50 Prozent direkte Siege",
                "Weg A, untere Grenze direkter Siege mindestens 45 Prozent","Weg B, untere Grenze direkter Siege über 50 Prozent",
                "Weg B, untere Grenze Solution-Gesamtsieggewinn mindestens −1 Prozentpunkt")
        passed=all(conditions[:3]) or all(conditions[3:])
    check(result["gates"]==dict(zip(names,conditions,strict=True)) and result["passed"]==prior["passed"]==passed,"Independent decision")
    for arm,raw in result["groups"].items():
        check(raw["wins"]==c[arm] and raw["matches"]==[c[arm,i] for i in range(3)],"Group totals")
    archive_hash=sha256((d/"partien.jsonl.gz").read_bytes()).hexdigest()
    paired_hash=sha256((d/"sitze.csv").read_bytes()).hexdigest()
    check(archive_hash==prior["archive_sha256"] and paired_hash==prior["paired_sha256"],"Stored hashes")
    n=len(seeds);tot=2*n
    title="Unabhängige Sicht-1-Bestätigung" if stage=="confirm" else "Allgemeine Leistungsprüfung"
    lines=[f"# {title} {'bestanden' if passed else 'verfehlt'}","",
          f"Auf {n} neuen Karten mit beiden Startseiten wurden {len(games)} vollständige Spiele ausgetragen. "
          f"Gegen Solution gewann die Feldprobe {c['probe_solution92']} von {tot}, Original-V16 gewann {c['reference_solution92']}. "
          f"Direkt gegen Original-V16 gewann die Feldprobe {c['probe_v16']} von {tot} Spielen.", "",
          "## Gesamtsiege und unmittelbare Wirkung","",
          "| Kennzahl | Wert | 95-Prozent-Kartenintervall |","|---|---:|---:|"]
    for j,label,scale in ((0,"Eigene zusätzliche Gutschrift auf dem geänderten Zug pro Sitz",1),(1,"Gepaarter Gesamtsieggewinn gegen Solution, Prozentpunkte",100),
                          (2,"Direkte Siegquote gegen V16, Prozent",100)):
        lines.append(f"| {label} | {number(estimates[j]*scale)} | [{number(ci[0,j]*scale)}; {number(ci[1,j]*scale)}] |")
    lines += ["",f"Bei den auswertbaren Solution-Eingriffen verteilten sich die unmittelbaren Gutschriften auf {act['solution92','benefit',1]} Verbesserungen, "
              f"{act['solution92','benefit',0]} Gleichstände und {act['solution92','benefit',-1]} {'Rückgang' if act['solution92','benefit',-1]==1 else 'Rückgänge'}. "
              f"Die gesamte unmittelbare Zusatzgutschrift betrug {int(round(estimates[0]*tot)):+d}. "
              "Zum direkten Gegner lässt sich die tatsächliche Ankunft und Gutschrift beim geänderten Zug ausweisen. "
              "Die gepaarte kausale Zusatzgutschrift stammt aus der separaten Original-V16-Kontrolle gegen Solution.", "",
              "| Agent und Gegner | Siege P0 | Siege P1 | Match 1 | Match 2 | Match 3 |","|---|---:|---:|---:|---:|---:|"]
    for arm,title2 in (("reference_solution92","V16 gegen Solution"),("probe_solution92","Feldprobe gegen Solution"),("probe_v16","Feldprobe gegen V16")):
        lines.append(f"| {title2} | {byseat[arm,0]}/{n} | {byseat[arm,1]}/{n} | {c[arm,0]} | {c[arm,1]} | {c[arm,2]} |")
    lines+=["","## Eingriffe nach tatsächlichem Zielfeld","",
            "| Gegner | Kartenhälfte | Eingriffe | Angekommen | Davon Punktefeld | Eigene Gutschriften auf diesen Zügen insgesamt | Davon zusätzliche Punkte gegen die gepaarte Referenz |",
            "|---|---|---:|---:|---:|---:|---:|"]
    for o in ("solution92","v16"):
        for z in ("eigene","Achse","gegnerische"):
            a=play_by_region
            opponent_name = "Solution" if o=="solution92" else "Original-V16"
            lines.append(f"| {opponent_name} | {z} | {a[o,z,'count']} | {a[o,z,'arrived']} | {a[o,z,'scored']} | {a[o,z,'own']} | {a[o,z,'gain'] if o=='solution92' else '–'} |")
    lines+=[""]
    for o in ("solution92","v16"):
        ms=[act[o,"match",i] for i in (1,2,3)]
        opponent_name = "Solution" if o=="solution92" else "Original-V16"
        lines.append(f"- Gegen {opponent_name} gab es Änderungen auf {len(active_by.get(o,set()))} Karten, davon über beide Sitze {ms[0]}, {ms[1]} und {ms[2]} Eingriffe in Match 1, 2 und 3.")
    lines+=["","## Geänderte ganze Spiele gegen Solution","",
            "- Zusätzliche Gesamtsiege — "+(", ".join(statuses["neu"]) or "keine")+".",
            "- Verlorene Gesamtsiege — "+(", ".join(statuses["weg"]) or "keine")+".",
            "","## Entscheidung und Daten",""]
    for label,ok in zip(labels,conditions,strict=True):
        lines.append(f"- {label} — {'erfüllt' if ok else 'verfehlt'}.")
    if stage=="confirm":
        lines+=["","Die vorab festgelegte allgemeine Prüfung ist eröffnet." if passed else "Mit der verfehlten Bestätigung endet die Reihe. Die ungefilterte Prüfung entfällt gemäß Plan."]
    normal=[r for r in games if r["sensor"]!=1 and r["arm"]=="probe"]
    if stage=="general":
        lines+=["",f"Bei Sensorreichweite größer eins spielten {len(normal)} Kandidatenpartien vollständig originalgleich. "
                f"Der Monitor verglich darin {sum(r['commands_vs_original'] for r in normal)} tatsächlich eingereichte Einheitenbefehle mit V16. "
                "Auf allen solchen Solution-Sitzen waren vollständige Befehlsprüfsumme, Punkteverlauf und Ergebnisse identisch."]
    lines+=["",f"Die tatsächlichen Seeds liegen zwischen {seeds[0]} und {seeds[-1]}. Die Nachrechnung prüfte alle {len(games)*3} Matchendstände aus den 303 Punkteänderungen jeder Partie, "
            "die ursprünglichen Befehlsvorschläge aller 16 Einheiten und alle aktuellen Gegnerbefehle am gepaarten Eingriff. Alle vorherigen Befehlsprüfsummen und Punkteschritte stimmten mit der Referenz überein. "
            f"Die Intervalle ziehen 20.000-mal vollständige Karten mit beiden Sitzen. Das Roharchiv in `partien.jsonl.gz` hat SHA-256 `{archive_hash}`. "
            f"Sämtliche gepaarten Sitze stehen in `sitze.csv` (SHA-256 `{paired_hash}`), alle Eingriffe in `eingriffe.csv`.",""]
    (d/"ERGEBNIS.md").write_text("\n".join(lines))
    proof=dict(passed=bool(passed),recomputed_gates={k:bool(v) for k,v in zip(names,conditions,strict=True)},
               games=len(games),independent_end_scores=len(games)*3,all_original_proposals_checked=sum(r["commands_vs_original"] for r in games),
               untouched_normal_proposals=sum(r["commands_vs_original"] for r in normal),positive_seat_changes=statuses["neu"],
               negative_seat_changes=statuses["weg"],archive_sha256=archive_hash)
    (d/"zweitpruefung.json").write_text(json.dumps(proof,indent=2)+"\n")
    print(stage,passed,estimates.tolist(),ci.tolist(),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("stage",choices=("confirm","general"))
    main(p.parse_args().stage)
