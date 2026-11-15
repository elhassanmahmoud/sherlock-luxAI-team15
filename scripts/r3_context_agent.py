"""An offline-trained context table may retain V14's movement before ordinary R3 bookkeeping."""
import json
from pathlib import Path

import numpy as np

from agents.sherlock import geometry as geo
from scripts.collect_combat_advice import file_sha
from scripts.combat_teacher_counterfactual import live_ids, native_order
from scripts.r3_context_table import CELLS, PROTOCOL_SHA, R3_SHA, cell_indices
from scripts.selective_advice_agent import SelectiveAdviceAgent


def screened_advice(actor, obs, base, advice, features, masks, lookup):
    if int(obs["match_steps"]) == 0:
        return advice
    team = actor.team_id
    positions = np.asarray(obs["units"]["position"])[team]
    energy = np.asarray(obs["units"]["energy"])[team].reshape(-1)
    tiles = np.asarray(obs["map_features"]["tile_type"])
    ids = [u for u in live_ids(obs,team) if base[u,0] != advice[u,0] and base[u,0] < geo.SAP
           and advice[u,0] < geo.SAP and native_order(advice[u],positions[u],energy[u],actor.env_cfg,tiles)]
    if not ids:
        return advice
    first, second = base[ids,0], advice[ids,0]
    if actor.belief.mirrored:
        first, second = geo.MIRROR_DIR[first], geo.MIRROR_DIR[second]
    eligible = np.fromiter((masks[u][a] and masks[u][b] for u,a,b in zip(ids,first,second)), dtype=bool)
    ids = np.asarray(ids)[eligible]
    if not len(ids):
        return advice
    cells = cell_indices(np.stack([features[u] for u in ids]), first[eligible], second[eligible])
    retain = ids[lookup[cells]]
    actor.selective_counts["context_choices"] += len(ids)
    actor.selective_counts["context_v14"] += len(retain)
    chosen = advice.copy()
    chosen[retain] = base[retain]
    return chosen


class ContextMovementAgent(SelectiveAdviceAgent):
    def __init__(self, *args, advice_path, table, **kwargs):
        if kwargs.get("mode") != "movement" or file_sha(Path(advice_path)) != R3_SHA:
            raise ValueError("Context selector requires the original movement R3 checkpoint")
        value = json.loads(Path(table).read_bytes())
        flags = value["use_v14"]
        if (value.get("kind") != "r3_public_context_v1" or value.get("r3_sha256") != R3_SHA
                or value.get("protocol_sha256") != PROTOCOL_SHA or len(flags) != CELLS
                or any(type(x) is not bool for x in flags)):
            raise ValueError("Invalid trained R3 context table")
        super().__init__(*args, advice_path=advice_path, **kwargs)
        self.context_table = np.asarray(flags, dtype=bool)

    def _finish_advice(self, obs, base, advice):
        # The original R3 then applies its ordinary native-order check and records the actual issued world order.
        _, _, features, masks, _ = self._decide(obs)
        selected = screened_advice(self, obs, base, advice, features, masks, self.context_table)
        return super()._finish_advice(obs, base, selected)
