"""Exact positive-score likelihood for first-pair location and scoring tiles from a team's public history."""
from collections import Counter
from functools import lru_cache
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
COORD = np.asarray([(x, y) for x in range(24) for y in range(24) if x+y < 24], dtype=np.int16)
MID = COORD[:, 0]*24+COORD[:, 1]
OTHER = (23-COORD[:, 1])*24+23-COORD[:, 0]
BITS = tuple(1 << i for i in range(25))
ALL = sum(BITS)
RATES = json.loads((HERE.parent/"zielschaetzer/ort.json").read_bytes())
PRIOR = np.asarray(RATES["counts"], float)+.5
PRIOR /= PRIOR.sum()
P = float(RATES["point_bit_density"])
POW0 = np.asarray([(1.-P)**n for n in range(26)])
POW1 = np.asarray([P**n for n in range(26)])
WORLD = np.zeros((len(COORD), 576), dtype=np.int32)
COVERS = np.full((len(COORD), 25), 576, dtype=np.int16)
for i, c in enumerate(COORD.tolist()):
    for j, (dx,dy) in enumerate((x,y) for x in range(-2,3) for y in range(-2,3)):
        x, y = c[0]+dx, c[1]+dy
        if 0 <= x < 24 and 0 <= y < 24:
            COVERS[i, j] = x*24+y
            WORLD[i, x*24+y] |= 1 << j
            WORLD[i, (23-y)*24+23-x] |= 1 << j


POPCOUNT = np.asarray([i.bit_count() for i in range(256)], dtype=np.int16)


def count_bits(values):
    octets = np.ascontiguousarray(values, dtype=np.uint32).view(np.uint8).reshape(-1, 4)
    return POPCOUNT[octets].sum(axis=1)


def unique_counts(items):
    return sorted({(tuple(sorted(row)), int(g)) for row, g in items})


def infer_bits(equations, prior_zero, targets):
    """Enumerate only undetermined constrained bits; all remaining Bernoulli bits are integrated analytically."""
    mass = 0.
    cells = np.zeros(len(targets))
    targets = np.asarray(targets,np.int32)
    def recurse(yes, no):
        nonlocal mass
        while True:
            forced_yes = forced_no = 0
            unresolved = []
            for terms, needed in equations:
                residual = []
                for term in terms:
                    if term & yes:
                        needed -= 1
                    elif term & ~no:
                        residual.append(term & ~no)
                if needed < 0 or needed > len(residual):
                    return
                if needed == 0:
                    for term in residual:
                        forced_no |= term
                else:
                    if needed == len(residual):
                        for term in residual:
                            if term & (term-1) == 0:
                                forced_yes |= term
                    unresolved.append(residual)
            if forced_yes & forced_no or forced_yes & no or forced_no & yes:
                return
            if not (forced_yes | forced_no):
                break
            yes |= forced_yes
            no |= forced_no
        if unresolved:
            terms = min(unresolved,key=len)
            # Choose the bit occurring in most remaining terms to prune both branches.
            relevant = set()
            for term in terms:
                while term:
                    bit = term & -term
                    relevant.add(bit)
                    term ^= bit
            freq = {bit:sum(bool(mask & bit) for term in unresolved for mask in term) for bit in relevant}
            bit = max(sorted(freq),key=freq.get)
            recurse(yes|bit,no)
            recurse(yes,no|bit)
            return
        w = POW1[int(yes).bit_count()]*POW0[int(no).bit_count()]
        free = targets & ~(no|yes)
        marginal = np.where((targets & yes) != 0, 1., 1.-POW0[count_bits(free)])
        mass += w
        cells[:] += w*marginal
    recurse(0,int(prior_zero))
    return mass, cells


@lru_cache(maxsize=300)
def model_cells(i):
    world = WORLD[i]
    covered = np.flatnonzero(world)
    targets, inverse = np.unique(world[covered],return_inverse=True)
    return covered, targets, inverse


def occupied(data, team, step):
    live = data["units_mask"][step,team] & (data["energy"][step,team] >= 0)
    pos = data["position"][step,team,live]
    return np.unique(pos[:,0]*24+pos[:,1]).astype(np.int16)


class ScoreEvidence:
    """Construct from unprivileged arrays only, then extend chronologically after the first positive score."""
    def __init__(self, data, team, first):
        self.data, self.team, self.first = data, team, first
        self.seen = np.zeros(576,np.int16)
        previously = np.zeros(577,np.int16)
        for t in range(1,first):
            self.seen[np.asarray(data["sensor_mask"][t]).ravel()] = t
            idx = occupied(data,team,t)
            x,y = np.divmod(idx,24)
            previously[idx] = t
            previously[(23-y)*24+23-x] = t
        self.negative = previously[COVERS]
        self.groups = []
        self.equations = []
        self.step = first-1

    def extend(self, t):
        if t != self.step+1 or self.data["relic_nodes_mask"][:t+1].any():
            raise ValueError("Posterior outside its chronology")
        self.step = t
        self.seen[self.data["sensor_mask"][t].ravel()] = t
        current = occupied(self.data,self.team,t)
        gain = int(self.data["team_points"][t,self.team]-self.data["team_points"][t-1,self.team])
        if not self.equations and gain <= 0:
            raise ValueError("No first positive clue")
        self.equations.append((current,gain))
        if self.groups:
            return
        # Spawn observation 1..50. First positive constrains activation at or before first.
        for i in range(len(COORD)):
            result = {}
            last = self.negative[i]
            for s in range(1,min(self.first,50)+1):
                selected = np.flatnonzero(last >= s)
                mask = int(np.bitwise_or.reduce(np.asarray(BITS,np.int64)[selected],initial=0))
                result.setdefault(mask,[]).append(s)
            self.groups.append(result)

    def estimate(self):
        locations = np.zeros(300)
        cells = np.zeros(576)
        locations0 = np.zeros(300)
        cells0 = np.zeros(576)
        seen = np.maximum(self.seen[MID],self.seen[OTHER])
        for i,c in enumerate(COORD):
            if seen[i] >= min(self.first,50):
                continue
            patch, targets, map_to_targets = model_cells(i)
            terms = []
            feasible = True
            for pos,g in self.equations:
                masks = WORLD[i,pos]
                masks = masks[masks > 0]
                if len(masks) < g:
                    feasible = False
                    break
                terms.append((masks.tolist(),g))
            equations = unique_counts(terms) if feasible else []
            full = np.zeros(len(targets))
            weak = np.zeros(len(targets))
            for forced, times in self.groups[i].items():
                n = len(times)-int(np.searchsorted(times, seen[i], side="right"))
                if not n:
                    continue
                weight = PRIOR[i]*n/50
                # Reference sees the same interval with no relic and no points before the first gain.
                proposal = POW0[forced.bit_count()]*weight
                locations0[i] += proposal
                bits_open = count_bits(targets & ~forced)
                weak += proposal*(1-POW0[bits_open])
                if feasible:
                    density, score_bits = infer_bits(equations, forced, targets)
                    locations[i] += weight*density
                    full += weight*score_bits
            cells[patch] += full[map_to_targets]
            cells0[patch] += weak[map_to_targets]
        z = float(locations.sum())
        z0 = float(locations0.sum())
        if not z or not z0:
            raise ValueError("No first-pair location can account for the public scores")
        return locations/z, cells/z, locations0/z0, cells0/z0
