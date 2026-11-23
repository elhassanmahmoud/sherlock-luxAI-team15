"""Render paired first-sighting summaries using counts, cumulative rates and censored times."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from auswerten import HERE,LABELS


def number(x,d=1):
    return f'{x:.{d}f}'.replace('.',',')


def percent(x,n):
    return f'{x}/{n} ({number(100*x/n)} %)'


def timing(r):
    return [percent(r['by40'],r['n']),percent(r['by70'],r['n']),percent(r['missed'],r['n']),number(r['median']),number(r['mean100'],2)]


def markdown_table(columns,rows):
    return '\n'.join('| '+' | '.join(row)+' |' for row in [columns,['---']*len(columns),*rows])


def write_report(records):
    head=('Reihe','Spieler','Bis Zug 40','Bis Zug 70','Ohne Fund im ersten Match','Median, Zug','Mittel bis Zug 100')
    aliases={'flotte40':'Flotte · 40','flotte120':'Flotte · 120','gemeinsam48':'Ort + Flotte · 48','suchwege40':'Suchwege · 40',
             'allgemein160':'Ort + Flotte · 160 alle','allgemein_sicht1':'Ort + Flotte · Sicht 1 im 160er-Test'}
    main=[];other=[];pairs=[];duels=[]
    for p in records:
        series=aliases[p['key']]
        for arm,v in p['values'].items():
            target=other if p['key']=='suchwege40' else main
            target.append([series,LABELS[arm],*timing(v['solution92'])])
            if arm=='reference':continue
            pairs.append([series,LABELS[arm],str(v['inactive']),number(v['inactive_both']['mean100'],2) if v['inactive_both'] else '–',str(v['active']),number(v['active_reference']['mean100'],2) if v['active_reference'] else '–',number(v['active_candidate']['mean100'],2) if v['active_candidate'] else '–'])
            duels.append([series,LABELS[arm],*timing(v['v16'])])
    pilot=next(r for r in records if r['key']=='gemeinsam48')['values'];c=pilot['scout'];ref=pilot['reference']['solution92'];ext=c['solution92']
    text=['# Wann sehen wir das erste Relikt?',
          'Im Pilot mit 48 Karten und Sichtweite eins brauchte **Ort und Flotte im Median 49,5 Züge**, Original-V16 50. Bis Zug 40 sah der Sucher das erste Relikt in 26 von 96 Spielen, V16 in 24. Bis Zug 70 lagen die Zahlen bei 83 und 87. Der Sucher erreichte in allen 96 Spielen noch vor Matchende einen Fund, V16 in 95. Beide Startplätze jeder Karte zählen je einmal.',
          'Als Fund zählt das erste Relikt in der öffentlichen Beobachtung des eigenen Teams. Das erste Match umfasst die Beobachtungen in den Zügen 0 bis 100. „Bis“ schließt den genannten Zug ein. Das begrenzte Mittel rechnet eine Partie ohne Fund mit 100 und lässt sie im Nenner. Das ursprüngliche Spielarchiv verwendet für einen ausgebliebenen Fund den technischen Wert 101. Bei der Gegenrechnung des ursprünglichen Pilotwerts bleibt dieser Wert erhalten.',
          '## Gegen denselben Gegner auf denselben Karten',
          markdown_table(head,main),
          'Die beiden Flottenblick-Reihen prüften denselben Spieler mit gelernter Flottenvorhersage. Die erste Reihe wählte sie aus, die folgenden 120 Karten prüften sie unabhängig. Der gemeinsame Orts- und Flottensucher ergänzt den Flottenblick um die gelernte Wahrscheinlichkeit des Reliktorts. Die historischen Reihen haben jeweils eigene Karten.',
          '![Anteil der Spiele mit bereits sichtbarem Relikt über die ersten 100 Züge](fundkurven.png)',
          '## Sitze mit tatsächlichem Eingriff',
          'Diese Aufteilung nutzt den ausgeführten Befehl. In den unveränderten Sitzen stimmten der vollständige gemeinsame Befehlsverlauf beider Spieler, Fundzug und Matchergebnisse überein. Die geänderten Sitze sind eine nachträgliche Auswahl. Der Sucher durfte bis zur ersten Sicht oder Gutschrift eingreifen. Frühe Funde können deshalb schon die Gelegenheit zum Eingriff beenden. Die zugehörigen Mittel beschreiben diese Sitze bei beiden Spielweisen.',
          markdown_table(('Reihe','Sucher','Unverändert','Gemeinsames Mittel','Geändert','V16 auf diesen Sitzen','Sucher auf diesen Sitzen'),pairs),
          '## Gegen Original-V16 im direkten Spiel',
          'Die Zeiten gehören zur Seite des jeweiligen Suchers im tatsächlichen Duell gegen V16. Für die Vergleiche mit einem V16-Kontrollsitz gegen denselben Gegner dient die erste Tabelle.',
          markdown_table(head,duels),
          '## Weitere historische Suchwege',
          'Die 40 Karten des früheren Vergleichs dreier Richtungsregeln bilden eine eigene Stichprobe. Alle drei Sucher teilen sich dieselben 80 V16-Kontrollsitze gegen Solution.',
          markdown_table(head,other),
          '## Gegenrechnung',
          f"Das bekannte 48er-Panel enthält genau 288 vollständige Partien. V16 gewann {ref['wins']}/96 gegen Solution, der gemeinsame Sucher {ext['wins']}/96 und direkt gegen V16 {c['v16']['wins']}/96. Gepaarte Fundzeiten aller Sitze einschließlich der technischen 101 ergeben 68 Züge Vorsprung, also 0,7083 pro Sitz. Die erste eigene Gutschrift rückte insgesamt um 143 Züge vor. Die Identität der ursprünglichen Serie, die Sitzzuordnung an beiden Kartenenden und alle fünf Summen wurden gegen das veröffentlichte Ergebnis geprüft. [Pilotbilanz](../ortundflotte/duelle.json)",
          'Die Daten pro Reihe enthalten die vollständigen Schwellenwerte von Zug 0 bis 100 sowie den SHA-256-Abdruck des gelesenen Spielarchivs. [Historische Gegenrechnung](historisch.json) · [Berechnung](auswerten.py)']
    if any(p['key']=='allgemein_sicht1' for p in records):
        general=next(p for p in records if p['key']=='allgemein_sicht1');ref=general['values']['reference']['solution92'];can=general['values']['ortundflotte']['solution92'];n=ref['n']
        model=general['values']['ortundflotte'];los=model['misses'];ci=model['paired_mean100_ci95']
        text.insert(2, f"**Die getrennte ungefilterte Prüfung enthielt {len(general['cards'])} Sicht-1-Karten mit {n} Sitzen je Spieler.** Bis Zug 40 fand Ort und Flotte {can['by40']}/{n} erste Relikte und V16 {ref['by40']}/{n}, bis Zug 70 waren es {can['by70']}/{n} und {ref['by70']}/{n}. Ohne Fund blieben {can['missed']} bzw. {ref['missed']} Sitze. Das begrenzte Mittel betrug {number(can['mean100'],2)} bzw. {number(ref['mean100'],2)} Züge. Der mittlere Vorteil des Suchers von {number(model['paired_mean100_gain'],2)} Zügen hat bei 20.000 gepaarten Ziehungen ganzer Karten ein 95-%-Intervall von {number(ci[0],2)} bis {number(ci[1],2)} Zügen. [Gegenrechnung des fertigen Gesamtarchivs](mit_gesamt.json)")
        if los:
            nwon=sum(m['candidate_win'] for m in los); rescues=sum(m['candidate_win']>m['original_win'] for m in los); earned=sum(m['candidate_credit']<=100 for m in los)
            text.insert(3,f"Die {len(los)} Spiele ohne Fund verteilen sich auf {len(set(m['seed'] for m in los))} Karten. In {earned} dieser Spiele sammelte der Sucher im ersten Match trotzdem Punkte. Er gewann {nwon} dieser ganzen Spiele, davon {rescues} auf Sitzen, die V16 verlor. Sicht misst das Entdecken des Reliktknotens. Ein Schiff kann früher zufällig auf einem zugehörigen Punktefeld stehen. Die Fundzeiten und ihre eigenen Unsicherheiten ergänzen die vorab festgelegte Gesamtentscheidung. [Ergebnis der Gesamtprüfung](../abschlusspruefung/ergebnis.json)")
    (HERE/'ERGEBNIS.md').write_text('\n\n'.join(text)+'\n')


def chart(records):
    select=[p for p in records if p['key'] in ('flotte40','flotte120','gemeinsam48','allgemein_sicht1')]
    if len(select)==4:
        fig,axes=plt.subplots(2,2,sharey=True,figsize=(9.8,6.2))
    else:
        fig,axes=plt.subplots(1,len(select),sharey=True,figsize=(4.15*len(select),3.05))
    axes=np.ravel(axes)
    for ax,p in zip(axes,select):
        candidates=[k for k in p['values'] if k!='reference'];cand=candidates[0];n=len(p['cards'])
        for key,color,ls,lw,label in [('reference','#283b53','--',1.8,'V16'),(cand,'#b74721','-',2.1,'Sucher')]:
            x=p['values'][key]['solution92'];ax.step(range(101),np.array(x['curve'])*100/x['n'],where='post',color=color,linestyle=ls,linewidth=lw,label=label)
        for turn in (40,70):ax.axvline(turn,color='#b9c0c5',linestyle=':',linewidth=.9,zorder=-2)
        label='Flottenblick' if cand=='flotte' else 'Ort und Flotte';scope=' · Sicht 1 im Gesamttest' if p['key']=='allgemein_sicht1' else ''
        ax.set_title(f'{label} · {n} Karten'+scope,fontsize=9.5,loc='left');ax.set_xlabel('Zug im ersten Match',fontsize=9)
        ax.set_xlim(0,100);ax.set_ylim(0,101);ax.set_xticks([0,20,40,70,100]);ax.set_yticks([0,25,50,75,100]);ax.tick_params(labelsize=8)
        ax.grid(axis='y',color='#dce1e4',lw=.6);ax.spines[['right','top']].set_visible(False)
    axes[0].set_ylabel('Anteil mit erstem Fund (%)',fontsize=9)
    if len(select)==4:axes[2].set_ylabel('Anteil mit erstem Fund (%)',fontsize=9)
    axes[0].legend(loc='upper left',fontsize=8,frameon=False)
    fig.tight_layout();fig.savefig(HERE/'fundkurven.png',dpi=140,bbox_inches='tight');plt.close(fig)


if __name__=='__main__':
    path=HERE/'mit_gesamt.json'
    source=json.loads((path if path.exists() else HERE/'historisch.json').read_text());write_report(source);chart(source)
