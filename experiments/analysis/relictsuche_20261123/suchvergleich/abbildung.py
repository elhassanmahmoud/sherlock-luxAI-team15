"""Rebuild the low-visibility search comparison from complete paired game archives, one row per model."""
import gzip
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PANELS=(
    ("Gelernte Suchrichtung","vergleich/discovery/partien.jsonl.gz","route"),
    ("Geschätzter Reliktort","vergleich/discovery/partien.jsonl.gz","ziel"),
    ("Gelernter Routenwert","vergleich/discovery/partien.jsonl.gz","wert"),
    ("Suche nach Wartezügen","standsuche/duelle/discovery/partien.jsonl.gz","stand"),
    ("Suche nach erster Gutschrift","punktsicht/partien.jsonl.gz","punktsicht"),
    ("Flottensicht","flottenblick/bestaetigung/partien.jsonl.gz","flotte"),
    ("Suche bei spätem Start","spaetsuche/panel/partien.jsonl.gz","late"),
    ("Flottensicht mit Kontextwahl","kontextsuche/duelle.jsonl.gz","select"),
    ("Reliktort und Flottensicht","ortundflotte/duelle_karten.jsonl.gz","scout"),
)


def summarize(path,arm):
    with gzip.open(path,"rt") as stream:packed=[json.loads(line) for line in stream]
    all_rows=[r for block in packed for r in block.get("views",[block])]
    rows={(r["seed"],r["team"],r["id"],r["opponent"]):r for r in all_rows}
    seeds=sorted({r["seed"] for r in all_rows})
    v=[]
    for seed in seeds:
        for t in (0,1):
            original,actual,direct=[rows[seed,t,a,o] for a,o in (("reference","solution92"),(arm,"solution92"),(arm,"v16"))]
            assert all(r["sensor"]==1 and r["steps"]==303 for r in (original,actual,direct))
            v.append([original["sight"]-actual["sight"],direct["win"]*100,actual["win"],original["win"]])
    nmaps=len(seeds)
    v=np.asarray(v,float).reshape(nmaps,2,4)
    unit=v.mean(1)
    idx=np.random.default_rng(231123).integers(0,nmaps,(20000,nmaps))
    bounds=np.quantile(unit[idx].mean(1),[.025,.975],axis=0)
    return dict(cards=nmaps,sight=unit[:,0].mean(),direct=unit[:,1].mean(),bounds=bounds[:,:2].T.tolist(),
                solution=int(v[:,:,2].sum()),ref=int(v[:,:,3].sum()))


def render():
    series=[]
    for title,name,arm in PANELS:
        f=ROOT/name
        if f.exists():series.append((title,summarize(f,arm)))
    fig=plt.figure(figsize=(12.6,3.35+.48*len(series)),facecolor="white")
    layout=fig.add_gridspec(1,4,width_ratios=(2.9,2.6,2.6,2.0),left=.035,right=.976,top=.75,bottom=.22,wspace=.18)
    axs=[fig.add_subplot(layout[0,i]) for i in range(4)]
    color="#124c54"
    for ax in axs:
        ax.set_ylim(len(series)-.5,-.5);ax.set_yticks([])
        for y in np.arange(.5,len(series),1):ax.axhline(y,color="#edf0f0",lw=1,zorder=0)
        for edge in ax.spines.values():edge.set_visible(False)
        ax.tick_params(axis="x",labelsize=9,length=0,pad=5,color="#465963")
    axs[0].set_xlim(0,1);axs[0].set_xticks([]);axs[3].set_xlim(0,1);axs[3].set_xticks([])
    for ax,x0 in zip(axs[1:3],(0,50),strict=True):ax.axvline(x0,color="#8b979a",lw=1.2,ls="--")
    axs[1].set_xlim(-12,10);axs[1].set_xticks([-10,-5,0,5,10]);axs[1].set_xlabel("Züge früher",fontsize=10)
    axs[2].set_xlim(20,70);axs[2].set_xticks([20,30,40,50,60,70]);axs[2].set_xlabel("Siegquote (%)",fontsize=10)
    for ax,t in zip(axs,("Suchansatz","Erstes Relikt gegen Solution","Direkt gegen V16","Siege gegen Solution"),strict=True):
        ax.set_title(t,loc="left",fontsize=11,fontweight="bold",color=color,pad=15)
    for i,(name,r) in enumerate(series):
        axs[0].text(.01,i,name,va="center",fontsize=11,color="#1d2e32")
        for ax,mean,(lo,hi) in zip(axs[1:3],(r["sight"],r["direct"]),r["bounds"],strict=True):
            ax.plot([lo,hi],[i,i],color=color,lw=2.4,solid_capstyle="round")
            ax.scatter([mean],[i],facecolor=color,edgecolor="white",s=50,linewidth=.8,zorder=3)
        n=r["cards"]*2
        axs[3].text(.02,i,f'{r["solution"]}/{n}    ·    V16 {r["ref"]}/{n}',va="center",fontsize=10.5,color="#1d2e32")
    fig.text(.035,.92,"Wie viel bringt die Suchrichtung eines freien Schiffs?",fontsize=21,weight="bold",color="#153239")
    fig.text(.035,.86,"Geringe Sichtweite · ganze Partien · dieselben Karten und Startseiten für Kandidat und V16",fontsize=12,color="#456168")
    fig.text(.035,.077,"Punkt = Mittelwert, Linie = 95-%-Intervall beim Ziehen ganzer Karten. Verschiedene Testpanels haben eigene Karten.",fontsize=10,color="#465963")
    fig.text(.035,.037,"Für die Flottensicht sind die 120 unabhängigen Bestätigungskarten dargestellt. Ein positiver Zeitwert bedeutet einen früheren Fund.",fontsize=10,color="#465963")
    fig.savefig(HERE/"suchvergleich.png",dpi=160,facecolor="white")
    plt.close(fig)


if __name__=="__main__":render()
