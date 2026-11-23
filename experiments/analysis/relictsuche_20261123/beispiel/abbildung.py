"""Plot the two reproduced trajectories of the sole flipped Solution seat, using the actual point stream."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent


def main():
    raw=json.loads((HERE/"verlaeufe.json").read_text())
    assert raw["seed"]==162640213 and raw["team"]==1
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.8),sharey=True)
    fig.subplots_adjust(top=.77,bottom=.23,left=.10,right=.97,wspace=.13)
    for i,ax in enumerate(axes):
        m=i+1
        ax.axhline(0,color="#829097",lw=.8)
        for arm,name,color in (("original","V16","#536570"),("all","V16 mit zusätzlichem Feldwissen","#007E79")):
            pts=np.asarray(raw["points"][arm][101*m:101*(m+1)])
            assert np.array_equal(pts[-1],raw["groups"][arm]["matches"][m]["points"])
            margin=pts[:,0]-pts[:,1]
            ax.plot(range(101),margin,label=name,color=color,lw=2.1)
            ax.scatter(100,margin[-1],s=17,color=color,zorder=3)
        if i==0:
            q=raw["groups"]["all"]["first_changed"]-101
            ax.axvline(q,color="#BE7347",lw=1.1,ls="--")
            ax.text(q+2,.97,"Erster anderer Befehl",va="top",fontsize=7.8,color="#83492C",transform=ax.get_xaxis_transform())
        ax.set(xlim=(0,103),xlabel="Zug im Match",title=f"Match {m+1}")
        ax.grid(axis="y",alpha=.14)
        ax.spines[["top","right"]].set_visible(False)
    axes[0].set_ylabel("Eigene Punkte minus Solution-Punkte")
    fig.suptitle("Wie eine zusätzliche Feldinformation das Spiel verändert",x=.10,ha="left",fontweight="bold",fontsize=14)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower center",ncol=2,frameon=False,fontsize=9)
    fig.savefig(HERE/"punktestand.png",dpi=160,metadata={"Software":"Matplotlib"})
    plt.close(fig)


if __name__=="__main__":
    main()
