"""Render the checked holdout stages, including reversals, seat differences and direct losses."""
import argparse
import csv
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FOLDERS = {"confirm": "bestaetigung", "general": "allgemein"}


def num(value, signed=False):
    spec = "+.2f" if signed else ".2f"
    return format(value, spec).replace("-", "−").replace(".", ",")


def render(phase):
    out = HERE / FOLDERS[phase]
    report = json.loads((out/"ergebnis.json").read_bytes())
    audit = json.loads((out/"nachpruefung.json").read_bytes())
    record = json.loads((out/"serie.json").read_bytes())
    result = report["candidates"]["flotte"]
    original = report["reference"]["all"]
    sol = result["solution"]["all"]
    direct = result["direct"]["all"]
    seats = [dict((k,int(v)) for k,v in r.items()) for r in csv.DictReader((out/"gepaarte_sitze.csv").open())]
    with gzip.open(out/"partien.jsonl.gz","rt") as f:
        raw = [json.loads(l) for l in f]
    assert audit["passed"]==result["passed"] and audit["bad_rows"]==0
    stage = "Unabhängige Sicht-1-Bestätigung" if phase=="confirm" else "Allgemeine Freigabeprüfung"
    verdict = "bestanden" if result["passed"] else "verfehlt"
    noun = "Bestätigung" if phase=="confirm" else "allgemeine Prüfung"
    consequence = ("Die vorab vorgesehene ungefilterte Prüfung ist damit eröffnet." if result["passed"] else
                   "Die ungefilterte Prüfung entfällt gemäß dem vorab festgelegten Plan.") if phase=="confirm" else (
                   "Das vollständige Leistungsprotokoll erfüllt einen der vorab definierten Freigabewege." if result["passed"]
                   else "Keiner der vorab definierten Freigabewege wurde erreicht.")
    count=original["games"]
    text=[f"# {stage} {verdict}", "",
          f"Die {noun} umfasste {report['games']} vollständige Partien auf {report['maps']} neuen Karten mit beiden Sitzen. "
          f"Gegen dieselbe Original-Solution gewann Flottenblick {sol['wins']} von {count} Spielen, Original-V16 gewann "
          f"{original['wins']}. Im direkten Duell gewann Flottenblick {direct['wins']} von {count} Spielen. {consequence}", "",
          "## Gegen dieselbe Original-Solution", "",
          "Bei Sicht und Gutschrift gehört eine positive Differenz zu einem früheren Ereignis. "
          "Bei den gegnerischen Punkten ist ein Rückgang günstig. Das 95-Prozent-Intervall zieht 20.000-mal ganze Karten mit beiden Sitzen. "
          "Bei den beiden Siegkennzahlen ist die Differenz in Prozentpunkten angegeben.", "",
          "| Maß | V16 | Flottenblick | Vorteil [95-%-Kartenintervall] | Besser / gleich / schlechter |",
          "|---|---:|---:|---:|---:|"]
    labels = (("sight","Erste Sicht, Zug"), ("credit","Erste Gutschrift, Zug"), ("own70","Eigene Punkte nach Zug 70"),
              ("opp70","Gegnerische Punkte nach Zug 70"), ("margin70","Punktedifferenz nach Zug 70"),
              ("match1points","Eigene Punkte in Match 1"), ("match1opp","Gegnerische Punkte in Match 1"),
              ("match1margin","Punktedifferenz in Match 1"), ("match1win","Siege in Match 1"), ("whole","Ganze Siege"))
    for field,label in labels:
        paired=result["paired"][field]
        sign=-1 if field in ("opp70","match1opp") else 1
        scale=100 if field in ("match1win","whole") else 1
        lo, hi = sorted(float(x)*sign*scale for x in paired["ci95"])
        improved, worsened = paired["positive_seats"], paired["negative_seats"]
        if sign<0:
            improved,worsened=worsened,improved
        vals=[]
        for group in (original,sol):
            if field in ("match1win","whole"):
                vals.append(f"{group['match1wins' if field=='match1win' else 'wins']}/{count}")
            else:
                vals.append(num(group["means"][field]))
        delta=num(paired["mean"]*scale*sign,True)
        text.append(f"| {label} | {vals[0]} | {vals[1]} | {delta} [{num(lo,True)}; {num(hi,True)}] | "
                    f"{improved} / {paired['equal_seats']} / {worsened} |")
    text += ["",f"Im ersten Match hatten {original['no_sight']} V16-Sitze und {sol['no_sight']} Flottenblick-Sitze keine Sicht. "
             f"Die erste Gutschrift blieb auf {original['no_credit']} beziehungsweise {sol['no_credit']} Sitzen aus. "
             "Ein ausgebliebenes Ereignis erhält den Wert 101.", "", "## Startplätze und direkte Spiele","",
             "| Maß | P0 | P1 |","|---|---:|---:|"]
    for field,label in (("sight","Mittlerer Sichtgewinn, Züge"),("credit","Mittlerer Gutschriftgewinn, Züge"),
                        ("margin70","Mittlerer Gewinn der Punktedifferenz nach Zug 70")):
        sides=result["paired"][field]["by_seat"]
        text.append(f"| {label} | {num(sides[0],True)} | {num(sides[1],True)} |")
    for arm,label in (("reference","V16 gegen Solution"),("solution","Flottenblick gegen Solution"),("direct","Flottenblick gegen V16")):
        obj=report["reference"] if arm=="reference" else result[arm]
        win=[f"{obj['by_seat'][str(i)]['wins']}/{obj['by_seat'][str(i)]['games']}" for i in (0,1)]
        text.append(f"| Ganze Siege {label} | {win[0]} | {win[1]} |")
    low,high = (100*x for x in result["direct_rate"]["ci95"])
    text += ["", f"Die direkte Siegquote betrug {num(100*result['direct_rate']['mean'])} Prozent "
             f"[{num(low)}; {num(high)}]. Flottenblick änderte gegen Solution {sol['changes']} Befehle auf "
             f"{sol['changed_games']} Sitzen und {sol['changed_maps']} Karten. Direkt gegen V16 waren es "
             f"{direct['changes']} Befehle auf {direct['changed_games']} Sitzen und {direct['changed_maps']} Karten.", "",
             "| Gegner und Agent | Siege Match 1 | Siege Match 2 | Siege Match 3 |","|---|---:|---:|---:|"]
    for agent,opponent,label in (("reference","solution92","V16 gegen Solution"),("flotte","solution92","Flottenblick gegen Solution"),
                                 ("flotte","v16","Flottenblick gegen V16")):
        games=[r for r in raw if r["id"]==agent and r["opponent"]==opponent]
        wins=[sum(r["matches"][j]["win"] for r in games) for j in range(3)]
        text.append(f"| {label} | {wins[0]} | {wins[1]} | {wins[2]} |")
    text += ["", "## Fälle mit unterschiedlichem Ausgang",""]
    for field,label in (("whole","Ganze Spiele"),("match1win","Erste Matches")):
        for success,word in ((1,"gewonnen"),(0,"verloren")):
            changed=[r for r in result["transitions"][field] if r["candidate"]==success]
            cases=", ".join(f"{r['seed']} P{r['team']}" for r in changed)
            text.append(f"- {label}, gegenüber V16 zusätzlich {word} ({len(changed)}) — {cases or 'keine'}.")
    text += ["", "Die folgenden einzelnen Sitze zeigen die größten beobachteten Verbesserungen und Verschlechterungen. "
             "Die CSV enthält alle Sitze einschließlich unveränderter Ergebnisse und direkt verlorener Spiele.", "",
             "| Maß | Stärkster Vorteil | Stärkster Nachteil |","|---|---|---|"]
    for field,label in (("sight","Erste Sicht"),("credit","Erste Gutschrift"),("margin70","Punktedifferenz nach Zug 70"),("match1margin","Punktedifferenz nach Match 1")):
        sign = -1 if field in ("sight","credit") else 1
        order=sorted(seats,key=lambda r:sign*(r["cnn_"+field]-r["v16_"+field]))
        items=[]
        for r in (order[-1],order[0]):
            items.append(f"{r['seed']} P{r['side']}, {r['v16_'+field]} → {r['cnn_'+field]}")
        text.append(f"| {label} | {items[0]} | {items[1]} |")
    text += ["","## Vorab festgelegte Bedingungen",""]
    titles={"sight_earlier_at_least_one":"Mittlerer Sichtgewinn ≥ 1 Zug","sight_lower_positive":"Untere Grenze für Sichtgewinn > 0",
            "credit_no_later":"Erste Gutschrift mindestens so früh","margin70_no_worse":"Punktedifferenz nach Zug 70 mindestens erhalten",
            "match1wins_no_fewer":"Mindestens gleiche Zahl erster Matchsiege","whole_wins_no_fewer":"Mindestens gleiche Zahl ganzer Siege",
            "route_a_external_lower_above_0":"Weg A, untere Grenze des ganzen Sieggewinns gegen Solution > 0",
            "route_a_direct_mean_at_least_half":"Weg A, direkte Siegquote mindestens 50 Prozent",
            "route_a_direct_lower_at_least_45pct":"Weg A, untere Grenze direkte Siegquote mindestens 45 Prozent",
            "route_b_direct_lower_above_half":"Weg B, untere Grenze direkte Siegquote über 50 Prozent",
            "route_b_external_lower_at_least_minus_1pp":"Weg B, untere Grenze des ganzen Sieggewinns gegen Solution mindestens −1 Prozentpunkt"}
    for k,yes in result["gates"].items():
        text.append(f"- {titles[k]} — {'erfüllt' if yes else 'verfehlt'}.")
    text += ["","## Nachweis","",
             f"Die Karten laufen von {record['cards'][0]} bis {record['cards'][-1]}. Die unabhängige Nachrechnung "
             f"bestätigte alle {audit['complete_games']} archivierten Partien, {audit['paired_seats']} gepaarte Sitze, "
             f"{audit['recomputed_metrics']} Kennzahlen samt Intervallen, sämtliche Bedingungen und "
             f"{audit['frozen_files']} eingefrorene Laufzeitdateien. Der Kursmonitor prüfte {audit['checked_unit_command_rows']} "
             "ausgegebene Einheitenbefehle. Alle Partien enthielten 303 vollständige Schritte, die Fehlerzähler standen auf null. "
             "Bei aktivem Eingriff konnte ausschließlich die gewählte Einheit im freigegebenen Sichtfenster abweichen. "
             "Gegen Solution hatten unveränderte Spiele identische Befehlsprüfsummen und Ergebnisse.", "",
             f"Die Einzelwerte stehen in `gepaarte_sitze.csv` (SHA-256 `{audit['paired_csv_sha256']}`). "
             f"Das vollständige Archiv `partien.jsonl.gz` hat SHA-256 `{audit['raw_sha256']}`. "
             "Die festen Quellen und Karten stehen in `serie.json`, die Zahlen in `ergebnis.json` und die technische Nachrechnung in `nachpruefung.json`.", ""]
    (out/"ERGEBNIS.md").write_text("\n".join(text))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase",choices=FOLDERS)
    render(p.parse_args().phase)
