"""Independently verify and report archival first choices and exact original-game substitutions."""
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
FIELD=HERE.parent
WORK=Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/rueckweg")
ARCH={"auswahl":FIELD/"ganze_partien.jsonl.gz","bestaetigung":FIELD/"bestaetigung/sicht1/partien.jsonl.gz"}


def read(path):
    return [json.loads(l) for l in gzip.decompress(path.read_bytes()).splitlines()]


def check(x,label):
    if not x:raise ValueError(label)


def main():
    result=json.loads((HERE/"archivbilanz.json").read_bytes())
    prefixes=read(HERE/"archiv_praefixe.jsonl.gz")
    vectors=((0,0),(0,-1),(1,0),(0,1),(-1,0))
    for p in prefixes:
        a=p["event"];last=p["prior_position"];now=p["current_position"];dx,dy=vectors[p["last_command"]] if 0<=p["last_command"]<5 else (99,99)
        back=(p["last_alive"] and 1<=p["last_command"]<=4 and a["xy"]==last and [last[0]+dx,last[1]+dy]==now
              and list(vectors[a["d"]])==[-dx,-dy] and max(p["bounds"])==0)
        check(p["veto"]==back and p["prior_turns"]==a["t"],"Bad public decision")
    by={(p["phase"],p["seed"],p["team"],p["opponent"]):p for p in prefixes}
    details=list(csv.DictReader((HERE/"archiv_sitze.csv").open()))
    output={}
    direct_parity=0
    for study,path in ARCH.items():
        rr=read(path)
        raw={(r["seed"],r["team"],r["arm"],r["opponent"]):r for r in rr}
        part=[r for r in details if r["phase"]==study]
        counts=Counter()
        for s in sorted({r["seed"] for r in rr}):
            a,b=(raw[s,t,"probe","v16"] for t in (0,1))
            if a["event"] is None and b["event"] is None:
                check(a["hash"]==b["hash"] and a["win"]+b["win"]==1 and a["profile"]==[z[::-1] for z in b["profile"]],"Control seat reuse invalid")
                direct_parity+=1
        for line in part:
            s,t=int(line["seed"]),int(line["team"])
            for op in ("solution92","v16"):
                rec=raw[s,t,"probe",op];a=rec["event"]
                px=by.get((study,s,t,op))
                check((px is None)==(a is None),"Unexpected archived event")
                if not a:continue
                check(all(px["event"][k]==a[k] for k in px["event"]) and px["prefix"]==a["prefix"] and px["scored"]==a["scored"],"Incorrect historical first attempt")
                counts[op,"probes"]+=1
                counts[op,"success"]+=int(a["scored"])
                if not px["veto"]:continue
                counts[op,"veto"]+=1
                counts[op,"rejected_hit"]+=int(a["scored"])
                if op=="solution92":
                    ref=raw[s,t,"reference","solution92"]
                    i=a["t"]
                    delta=rec["profile"][i][0]-ref["profile"][i][0]
                    check(int(line["solution_verzicht"])==ref["win"] and int(line["immediate_simple"])==delta
                          and int(line["immediate_verzicht"])==0,"Wrong paired control")
                    counts[op,"lost_gains"]+=int(delta>0)
                    counts[op,"gains_avoided"]+=delta
                else:
                    opp=raw[s,1-t,"probe","v16"]
                    if opp["event"] is None: win=1-opp["win"]
                    else:
                        f=WORK/"control"/study/f"{s}.json"
                        g=json.loads(f.read_bytes())
                        check(g["prefix"][str(a["t"])]==a["prefix"],"Nonidentical direct control prefix")
                        win=g["win"] if g["team"]==t else 1-g["win"]
                    check(int(line["direct_verzicht"])==win,"Incorrect actual self-play score")
        output[study]=counts
    veto=[x for x in prefixes if x["veto"]]
    cards={x["seed"] for x in veto}
    sums={k:sum(int(r[k]) for r in details) for k in ("solution_verzicht","solution_simple","direct_verzicht","direct_simple","immediate_verzicht","immediate_simple")}
    gates=dict(two_other_cards=len(cards-{162800176})>=2,more_empty_than_scoring=sum(not x["scored"] for x in veto)>sum(x["scored"] for x in veto),
               immediate_preserved=sums["immediate_verzicht"]>=sums["immediate_simple"],solution_wins_preserved=sums["solution_verzicht"]>=sums["solution_simple"],
               direct_wins_preserved=sums["direct_verzicht"]>=sums["direct_simple"])
    check(result["gates"]==gates and result["passed"]==all(gates.values()),"Wrong qualification")
    heading="qualifiziert sich für den frischen Vergleich" if result["passed"] else "verfehlt die Archivkriterien"
    text=[f"# Der Rückweg-Vorbehalt {heading}","",
          f"Auf den beiden bereits ausgewerteten Vollspielarchiven betraf die vorab festgelegte Regel {len(veto)} der {len(prefixes)} ursprünglichen Eingriffe auf {len(cards)} verschiedenen Karten. "
          f"Darunter waren {sum(x['scored'] for x in veto)} tatsächlich punktende und {sum(not x['scored'] for x in veto)} nicht punktende Ankünfte. "
          "Die Anlasskarte 162800176 ist enthalten. Die folgenden Zahlen beschreiben bekannte Spiele, die nach dem Einzelfall zur Diagnose herangezogen wurden.", "",
          "| Archiv und Gegner | Proben der einfachen Regel | Tatsächlich punktend | Vom Vorbehalt verworfen | Davon punktend |",
          "|---|---:|---:|---:|---:|"]
    for study,name in (("auswahl","48 Auswahlkarten"),("bestaetigung","120 Bestätigungskarten")):
        q=output[study]
        for op,o in (("solution92","Solution"),("v16","V16")):
            text.append(f"| {name}, {o} | {q[op,'probes']} | {q[op,'success']} | {q[op,'veto']} | {q[op,'rejected_hit']} |")
    text += ["","| Archiv | V16-Siege gegen Solution | Einfache Probe → Vorbehalt gegen Solution | Einfache Probe → Vorbehalt direkt gegen V16 | Unmittelbare eigene Zusatzpunkte gegen Solution |",
             "|---|---:|---:|---:|---:|"]
    for st,name in (("auswahl","48 Auswahlkarten"),("bestaetigung","120 Bestätigungskarten")):
        d=result["stages"][st];g=d["groups"]
        text.append(f"| {name} | {g['v16_solution']}/{d['seats']} | {g['simple_solution']} → {g['verzicht_solution']} | "
                    f"{g['simple_direct']} → {g['verzicht_direct']} | {d['immediate_simple']:+d} → {d['immediate_verzicht']:+d} |")
    text+=["",f"Außer der Anlasskarte betraf der Vorbehalt {len(cards-{162800176})} weitere Karten. Auf den Solution-Sitzen wurden {sum(v['solution92','lost_gains'] for v in output.values())} ursprünglich gesteigerte Sofortgutschriften verworfen. "
           "Bei den direkten V16-Duellen wird das tatsächliche Erreichen eines Punktefeldes getrennt von einer kausalen Zusatzgutschrift betrachtet.",
           "","## Frühere öffentliche V16-Aufzeichnungen","",
           "| Material | Karten | Ursprüngliche erste Proben | Verworfen | Davon tatsächlich punktendes Ziel |","|---|---:|---:|---:|---:|"]
    for split,label in (("train","Vormals im Feldmodelltraining"),("valid","Vormals in der Feldmodellvalidierung")):
        d=result["earlier"][split]
        text.append(f"| {label} | {d['maps']} | {d['attempts']} | {d['veto']} | {d['veto_scoring_target']} |")
    text+=["","Die Vorschläge auf diesen 208 Karten wurden gegen die damals gespeicherten Erstentscheidungen und die vorangegangenen physischen Positionen und Bewegungen ausgewertet. "
           "Es handelt sich um öffentliche Original-V16-Verläufe und bereits früher verwendete Feldlabels. Sie liefern keine neue Ganzspielbestätigung.", "",
           "## Prüfung und Entscheidung",""]
    labels={"two_other_cards":"Mindestens zwei weitere Karten außer der Anlasskarte","more_empty_than_scoring":"Mehr leere als punktende Ankünfte unterdrückt",
            "immediate_preserved":"Summierte unmittelbare Gutschrift gegen Solution mindestens erhalten","solution_wins_preserved":"Ganze Siege gegen Solution mindestens erhalten",
            "direct_wins_preserved":"Ganze Siege gegen V16 mindestens erhalten"}
    for k,ok in gates.items():text.append(f"- {labels[k]} — {'erfüllt' if ok else 'verfehlt'}.")
    new=sum(d["direct_controls_new"] for d in result["stages"].values());old=sum(d["direct_controls_existing"] for d in result["stages"].values())
    text+=["",f"Für alle {len(prefixes)} ursprünglichen Erstentscheidungen wurden nur die notwendigen öffentlichen Präfixe bis vor den Befehl wiederholt. "
           "Frühere Befehlsprüfsummen, Punkte und konkrete Vorschläge stimmen überein. Ohne Vorbehalt wurde das ursprüngliche tatsächliche Ergebnis wiederverwendet. "
           f"Gegen Solution lieferten die archivierten Originalkontrollen den Ausgang bei Verzicht. Für die direkten Sitze wurden {new} zusätzliche V16-gegen-V16-Spiele karteneindeutig durchgeführt, "
           f"für {old} weitere betroffene Karten lag ein vollständiger unveränderter Originalverlauf bereits im Gegenplatz vor. Die {direct_parity} bestehenden direkten Duelle mit zwei inaktiven Probe-Sitzen stimmen in beiden Sitzorientierungen vollständig in den Befehlsprüfsummen überein.",
           "", "Die neue unabhängige 48-Karten-Prüfung ist eröffnet." if result["passed"] else "Der frische Vergleich entfällt gemäß dem vor der Fallauszählung festgelegten Plan.",
           "", "Einzelbefunde einschließlich jedes verworfenen Punktefeldes stehen in `archivbilanz.json`. `archiv_sitze.csv` enthält alle Sitze. "
           "`archiv_praefixe.jsonl.gz` enthält die letzten öffentlichen Aktionen, Positionen und Untergrenzen zu jedem ursprünglichen Eingriff.",""]
    (HERE/"ARCHIV.md").write_text("\n".join(text))
    proof=dict(passed=all(gates.values()),cases=len(prefixes),archived_seats=len(details),unmodified_direct_map_pairs=direct_parity,different_cards=len(cards),gates=gates,
               archival_result_sha256=hashlib.sha256((HERE/"archivbilanz.json").read_bytes()).hexdigest())
    (HERE/"archiv_nachpruefung.json").write_text(json.dumps(proof,indent=2)+"\n")
    print(json.dumps(proof))


if __name__=="__main__":main()
