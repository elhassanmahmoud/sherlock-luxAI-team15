"""Read-only shadow counters for existing executed SAPs; no Torch or decisions.

The helper is loaded from this proposal, never installed into the repository.
Only use with the baseline agent (sap_geometry disabled) to measure opportunity.
All damage/energy scores are observation proxies, not actual hit estimates.
"""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np


def _load_proposed_helper():
    path = Path(__file__).parent / "sap_geometry_helper.py"
    tree = ast.parse(path.read_text())
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == "better_sap_geometry")
    scope = {"np": np}
    module = ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
        helper,
    ], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), scope)
    return scope["better_sap_geometry"]


_HELPER = _load_proposed_helper()


def _score(ctx, uid, target, dropoff, point_tiles):
    x, y = ctx["ally_pos"][uid]
    tx, ty = int(x) + int(target[0]), int(y) + int(target[1])
    ec, energies = ctx["enemy_coords"], ctx["enemy_energies"]
    distances = np.maximum(np.abs(ec[:, 0] - tx), np.abs(ec[:, 1] - ty))
    score = float(energies[distances == 0].sum()
                  + dropoff * energies[distances == 1].sum())
    if point_tiles is not None and (distances == 0).any() and point_tiles[tx, ty]:
        score += 1000.0
    return score


def observe_sap_geometry(ctx, ids, sap_targets, actions, *,
                         mirrored=False, sap_pt_first=False, smart_sap=False,
                         dropoff=0.5, example_limit=3):
    """Return additive per-step counters; do not mutate inputs or agent state.

    ctx and sap_targets use canonical coordinates, as in _decide().
    actions is the actual returned (max_units, 3) action array, in world space.
    mirrored must match agent.belief.mirrored.

    A different actual target (e.g. smart_sap/fog_sap) is counted separately
    and excluded from the comparison, because the existing target was not used.
    smart_sap=True excludes every executed SAP: its later planner could
    overwrite any proposed target even when today's target happens to match.
    Any visible negative-energy enemy also excludes the entire context.
    _HELPER is evaluated only for an actual SAP with a matching existing target.
    """
    counters = {
        "executed_saps": 0,
        "executed_saps_without_existing_target": 0,
        "executed_saps_with_changed_target": 0,
        "executed_saps_with_negative_enemy_context": 0,
        "executed_saps_with_unsupported_override": 0,
        "eligible_executed_saps": 0,
        "strictly_better_proxy_centers": 0,
        "proxy_score_before_sum": 0.0,
        "proxy_score_after_sum": 0.0,
        "proxy_score_gain_sum": 0.0,
    }
    examples = []
    point_tiles = ctx["point_tiles"] if sap_pt_first else None
    for uid in ids:
        uid = int(uid)
        if int(actions[uid, 0]) != 5:
            continue
        counters["executed_saps"] += 1
        if smart_sap:
            counters["executed_saps_with_unsupported_override"] += 1
            continue
        current = sap_targets.get(uid)
        if current is None:
            counters["executed_saps_without_existing_target"] += 1
            continue
        dx, dy = int(actions[uid, 1]), int(actions[uid, 2])
        if mirrored:
            dx, dy = -dy, -dx  # mirror_delta is its own inverse
        if (dx, dy) != tuple(current[:2]):
            counters["executed_saps_with_changed_target"] += 1
            continue
        if np.any(ctx["enemy_energies"] < 0):
            counters["executed_saps_with_negative_enemy_context"] += 1
            continue
        counters["eligible_executed_saps"] += 1
        before = _score(ctx, uid, current, dropoff, point_tiles)
        alternative = _HELPER(ctx, uid, current, before, dropoff)
        after = _score(ctx, uid, alternative, dropoff, point_tiles)
        counters["proxy_score_before_sum"] += before
        counters["proxy_score_after_sum"] += after
        if after > before:
            counters["strictly_better_proxy_centers"] += 1
            counters["proxy_score_gain_sum"] += after - before
            if len(examples) < example_limit:
                examples.append({
                    "uid": uid,
                    "step": ctx.get("step"),
                    "match_idx": ctx.get("match_idx"),
                    "match_step": ctx.get("match_step"),
                    "old_delta_canonical": [int(current[0]), int(current[1])],
                    "new_delta_canonical": [int(alternative[0]), int(alternative[1])],
                    "proxy_score_before": before,
                    "proxy_score_after": after,
                })
    return {"counters": counters, "examples": examples}
