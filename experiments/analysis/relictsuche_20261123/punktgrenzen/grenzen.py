"""Additional score bounds from visible opponents and fully discovered active relic regions."""
import numpy as np
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import CANONICAL, Evidence, MIRROR, PAIR, indices, subtract, weights


def field_zone(position):
    x,y=position
    mask=0
    for i in range(max(0,x-2),min(24,x+3)):
        for j in range(max(0,y-2),min(24,y+3)):
            mask|=1<<PAIR[24*i+j]
    return mask


class PublicBounds(Evidence):
    def __init__(self,opponents=True,geometry=True):
        super().__init__()
        self.opponents=opponents
        self.geometry=geometry
        self.seen_pairs={}
        self.zone_bits=0
        self.previous_rival=0
        self.enemy_caps={}

    def observe(self,row):
        t=row["step"]
        ms=row["ms"]
        level=t//101
        for idx,coords in row["relics"]:
            pair=idx%3
            assert 0<=pair<=level
            x,y=map(int,coords)
            assert 0<=x<24 and 0<=y<24
            canonical=PAIR[x*24+y]
            if pair in self.seen_pairs:
                assert self.seen_pairs[pair]==canonical
            else:
                self.seen_pairs[pair]=canonical
                self.zone_bits|=field_zone((x,y))
        past_epoch=self.epoch
        old_positive=self.positive
        super().observe(row)
        if self.epoch!=past_epoch or ms==0:
            self.enemy_caps.clear()
        delta=row["rival_points"]-self.previous_rival
        self.previous_rival=row["rival_points"]
        if ms:
            assert 0<=delta<=16
            if self.geometry and len(self.seen_pairs)==level+1:
                self.negative |= CANONICAL & ~self.zone_bits
                if self.positive & self.negative:
                    raise ValueError("Confirmed point outside complete public relic regions")
            if self.opponents:
                enemy=weights(row["rivals"])
                # Visible fighters can be a strict subset, so only an upper bound is justified.
                if enemy[0].bit_count()+enemy[1].bit_count()>delta:
                    prev=self.enemy_caps.get(enemy)
                    if prev is None or delta<prev[0]:
                        self.enemy_caps[enemy]=(delta,t)
                        a,b=enemy
                        self.add_bound((0,0,a,b),-delta,None,t)
                        for own,(lower,lo) in self.lower.items():
                            if own[0]&a:
                                self.add_bound(subtract(own,enemy),lower-delta,lo,t)
                own=weights(row["occupied"])
                floor=self.lower.get(own)
                if floor:
                    for enemy,(cap,hi) in self.enemy_caps.items():
                        if own[0]&enemy[0]:
                            self.add_bound(subtract(own,enemy),floor[0]-cap,floor[1],hi)
            self.propagate(t)
        return list(indices(self.positive&~old_positive))


def public_row(t,team,pos,energy,alive,points,relic_mask,relics):
    def occupied(side):
        live=np.asarray(alive[side],bool)&(np.asarray(energy[side]).reshape(-1)>=0)
        return sorted({24*int(x)+int(y) for x,y in np.asarray(pos[side])[live]})
    epoch=t//101
    return dict(step=t,ms=t%101,points=int(points[team]),occupied=occupied(team),
                epoch_seen=bool(np.asarray(relic_mask)[[epoch,epoch+3]].any()),
                rival_points=int(points[1-team]),rivals=occupied(1-team),
                relics=[(int(i),tuple(relics[i])) for i in np.flatnonzero(relic_mask)])
