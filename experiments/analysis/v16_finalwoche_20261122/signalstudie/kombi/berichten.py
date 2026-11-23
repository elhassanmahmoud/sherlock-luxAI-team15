"""Baut den lesbaren Bericht ausschließlich aus der vollständigen, geprüften Frischserie."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def de(number):
    return f"{number:.2f}".replace(".",",")


def main():
    folder=HERE/"frisch"
    result=json.loads((folder/"ergebnis.json").read_bytes())
    raw=[r for lane in (0,1) for r in map(json.loads,(folder/f"worker_{lane}.jsonl").read_text().splitlines())]
    if len(raw)!=720 or result["n"]!=len(raw):
        raise ValueError("Erst nach vollständiger unabhängiger Auswertung")
    got=result["results"]
    sol=got["solution92"];ka=got["kaggle3"];duel=got["v16"]
    s,k,h=sol["total"],ka["total"],duel["total"]
    guaranteed=sol['ci95'][0]>0
    ksafe=k['combined']>=k['base']
    dsafe=h['wins']>=40
    if result["gate"]!=bool(guaranteed and ksafe and dsafe):
        raise ValueError("Unstimmige vorab festgelegte Entscheidung")
    status=("Die feste Leistungsschwelle ist erreicht. Der Kandidat kann zum gesonderten Kurs- und Pakettest gehen."
            if result["gate"] else "Die feste Leistungsschwelle ist verfehlt. V16 bleibt die freigegebene Abgabe.")
    lines=[
        "# Kombination auf 80 neuen Karten",
        "",
        f"Die Kombination aus signalgesteuertem Kundschafter und Mitte2-Berater gewann **{s['combined']}/160 gegen Solution**. "
        f"Original-V16 gewann **{s['base']}/160**. Die Siegquotendifferenz (Kombination minus V16) beträgt {de(100*sol['diff'])} Prozentpunkte. "
        f"Das 95-%-Intervall über ganze Karten reicht von **{de(100*sol['ci95'][0])} bis {de(100*sol['ci95'][1])} Prozentpunkten**. "
        f"Gegen den Kaggle-Dritten steht es {k['combined']} zu {k['base']} Siegen aus je 160 Spielen. "
        f"Im direkten Vergleich gewann die Kombination {h['wins']}/80. **{status}**",
        "",
        "| Gegner / Startseite | Original-V16 | Kombination | Zusätzliche / verlorene Siege | Matchsiege V16 → Kombination | Veränderte Sitze |",
        "|---|---:|---:|---:|---:|---:|"]
    for title,out in (("Solution",sol),("Kaggle-Dritter",ka)):
        for label,t in [("beide",out["total"]),("P0",out["by_side"]["player_0"]),("P1",out["by_side"]["player_1"])]:
            lines.append(f"| {title} · {label} | {t['base']}/{t['sides']} | {t['combined']}/{t['sides']} | "
                         f"{t['added']} / {t['lost']} | {t['reference_matches']} → {t['combined_matches']} | {t['affected']} |")
    lines += ["","## Tatsächlich gespielte Befehle","",
              "Die folgenden Kategorien zählen ganze Sitze nach den tatsächlich geänderten Befehlen. "
              "Treffen beide Module im selben Spiel eine abweichende Entscheidung, beziehen sie sich auf verschiedene Züge.",
              "","| Gegner | kein Eingriff | nur Mitte2 | nur Kundschafter | beide | geänderte Befehle gesamt |",
              "|---|---:|---:|---:|---:|---:|"]
    for label,t in (("Solution",s),("Kaggle-Dritter",k)):
        m=t['modules']
        lines.append(f"| {label} | {m.get('kein',0)} | {m.get('mitte',0)} | {m.get('signal',0)} | {m.get('mitte+signal',0)} | {t['changed_actions']} |")
    lines+=["",
            f"Im Direktduell änderte die Kombination auf {h['affected']} von 80 Sitzen mindestens einen Befehl. "
            f"Sie gewann {h['affected_wins']} dieser veränderten Sitze und {h['quiet_wins']} der übrigen {80-h['affected']}. "
            f"P0 gewann {duel['by_side']['player_0']['wins']}/40, P1 {duel['by_side']['player_1']['wins']}/40. "
            f"Auf {duel['unchanged_maps']} der 40 Karten blieben beide Sitze unverändert, auf {duel['both_active']} griff die Kombination auf beiden Sitzen ein. "
            f"Bei {len(duel['inferred_control'])} weiteren Karten gibt der unveränderte Gegensitz eine direkte Referenz für die Wirkung auf den anderen Sitz.",
            "","## Entscheidung und Herkunft","",
            f"Für die positive Entscheidung waren alle drei Bedingungen gemeinsam festgelegt. "
            f"Die untere Grenze für zusätzliche Solution-Siege ist {'strikt positiv' if guaranteed else 'nicht strikt positiv'}. "
            f"Die Bedingung für mindestens so viele ganze Kaggle-Siege wie V16 ist {'erfüllt' if ksafe else 'verfehlt'}, "
            f"die Grenze von 40/80 Direktspielen ist {'erfüllt' if dsafe else 'verfehlt'}.",
            "",
            "Die elf vorher ausgewählten älteren Siegwechselsitze, ihre 44 Wiederholungen und vier technische Kontrollen zählen getrennt. "
            "Das neue Panel umfasst 80 zuvor reservierte, ungefilterte Kartenseeds, beide Startseiten, komplette Spiele und Originalgegner. "
            "Das Intervall zieht jeweils beide Sitze einer Karte zusammen (20.000 Wiederholungen, fester Seed 231786). "
            "Alle drei Matches, beide Punktesummen und der vollständige Entscheidungszähler wurden je Spiel geprüft. "
            "Bei identischen externen Befehlen waren die Endresultate beider Programme identisch.",
            "",
            "[Vorfestlegung](PLAN.md) · [Welche bekannten Rettungen kombinierbar waren](ARCHIV.md) · "
            "[Zahlen, Seiten und einzelne Siegwechsel](frisch/ergebnis.json) · [Rohdaten Teil A](frisch/worker_0.jsonl) · [Rohdaten Teil B](frisch/worker_1.jsonl)",
            "",
            "Aus dem Repo mit der Kurs-Python-Umgebung:",
            "",
            "```sh",
            "d=experiments/analysis/v16_finalwoche_20261122/signalstudie/kombi",
            'python "$d/auswerten.py" frisch',
            'python "$d/berichten.py"',
            "```",""]
    defeated=[r for r in raw if r["opponent"]=="solution92" and r["arm"]=="beide" and not r["game_win"]]
    loss_maps=sorted({r["seed"] for r in defeated})
    old_lost_first=sum(r["match_winners"][0]!=int(r["side"][-1]) for r in defeated)
    no_change=sum(not r["events"] for r in defeated)
    external_flip_maps=sorted({r["seed"] for r in ka["flips"]})
    map_note=("Beide Startseiten liegen auf derselben Karte" if len(external_flip_maps)==1 and len(ka["flips"])==2
              else "Die betroffenen Karten sind")
    direct_flips=[r for r in duel["inferred_control"] if (r["baseline_matches"]>=2)!=(r["candidate_matches"]>=2)]
    notes=["## Wo die noch offenen Niederlagen liegen","",
        f"Die {len(defeated)} Solution-Niederlagen der Kombination lagen auf {len(loss_maps)} Karten ({', '.join(map(str,loss_maps))}). "
        f"In {old_lost_first} dieser Sitze war Match 1 verloren, in {no_change} änderte keines der beiden Module einen Befehl. "
        "Mitte2 setzt voraus, dass Sherlock das erste Match gewonnen hat. Für die weitere Entwicklung bietet sich deshalb eine getrennte Untersuchung verlorener Auftaktmatches und ihrer Aufholchancen an.",
        "",
        f"Gegen Kaggle änderte sich der Spielsieger auf {len(ka['flips'])} Startseiten. {map_note} "
        f"({', '.join(map(str,external_flip_maps)) or 'keine'}). Das gepaarte Intervall für den Kaggle-Unterschied beträgt "
        f"{de(100*ka['ci95'][0])} bis {de(100*ka['ci95'][1])} Prozentpunkte. "
        f"In den direkten Spielen mit einem unveränderten Gegensitz kippten {len(direct_flips)} ganze Ergebnisse. "
        + " ".join(f"Auf {r['seed']}/P{r['side'][-1]} ging die Matchbilanz von {r['baseline_matches']}:{3-r['baseline_matches']} auf {r['candidate_matches']}:{3-r['candidate_matches']} zurück." for r in direct_flips),
        ""]
    before=lines.index("## Entscheidung und Herkunft")
    lines[before:before]=notes
    (HERE/"ERGEBNIS.md").write_text("\n".join(lines))


if __name__=="__main__":
    main()
