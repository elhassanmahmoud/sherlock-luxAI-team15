"""Four direction-only public features and a loss-sensitive local handover rule."""
import numpy as np


STYLE_NAMES = ('direction_persistence', 'immediate_reversal', 'closing_on_our_fleet', 'nearby_parallel_motion')


def style(own, enemy, own_live, enemy_live):
    """Inputs are role-oriented public positions and observed living masks, covering M1 only."""
    assert own.shape == enemy.shape == (101, 16, 2)
    assert own_live.shape == enemy_live.shape == (101, 16)
    movement = np.diff(enemy.astype(int), axis=0)
    seen_both = enemy_live[:-1] & enemy_live[1:]
    moving = seen_both & (np.abs(movement).sum(2) == 1)
    two = moving[:-1] & moving[1:]
    persistent = two & np.all(movement[:-1] == movement[1:], axis=2)
    reversed_move = two & np.all(movement[:-1] == -movement[1:], axis=2)
    # Own positions remain fixed at the earlier observation.
    starts = np.abs(enemy[:-1, :, None] - own[:-1, None, :]).sum(3)
    finishes = np.abs(enemy[1:, :, None] - own[:-1, None, :]).sum(3)
    starts = np.where(own_live[:-1, None, :], starts, 999)
    finishes = np.where(own_live[:-1, None, :], finishes, 999)
    opponents_with_own = moving & own_live[:-1].any(1)[:, None]
    approach = opponents_with_own & (finishes.min(2) < starts.min(2))
    left, right = np.triu_indices(16, 1)
    neighbors = np.abs(enemy[:-1, left] - enemy[:-1, right]).sum(2) <= 4
    nearby_moving = neighbors & moving[:, left] & moving[:, right]
    together = nearby_moving & np.all(movement[:, left] == movement[:, right], axis=2)
    counts = [int(x.sum()) for x in (persistent, reversed_move, approach, together)]
    totals = [int(x.sum()) for x in (two, two, opponents_with_own, nearby_moving)]
    fractions = (np.asarray(counts) + 2 * np.array([.25, .25, .5, .25])) / (np.asarray(totals) + 2)
    return fractions.tolist(), dict(moving=int(moving.sum()), consecutive=totals[0], counts=counts, totals=totals)


def observable(stats):
    return stats['moving'] >= 6 and stats['consecutive'] >= 2


def fit(old, motion, targets):
    if len(targets) < 12:
        return None
    blocks = []
    for features in (old, motion):
        x = np.asarray(features, dtype=float)
        center = x.mean(axis=0)
        scale = np.maximum(.05, x.std(axis=0))
        blocks.append(dict(center=center.tolist(), scale=scale.tolist(),
                           z=np.clip((x-center)/scale, -3, 3).tolist()))
    return dict(blocks=blocks, targets=list(targets), neighbors=12, threshold=.05)


def predict(model, old, motion, extended):
    if model is None:
        return None
    distance = 0
    for block, value in zip(model['blocks'][:2 if extended else 1], (old, motion)):
        z = np.clip((np.asarray(value)-block['center'])/block['scale'], -3, 3)
        distance = distance + np.square(np.asarray(block['z'])-z).mean(1)
    distance = distance / (2 if extended else 1)
    k = model['neighbors']
    if len(distance) < k:
        return None
    last = np.partition(distance, k-1)[k-1]
    below = distance < last
    equal = distance == last
    weights = below + equal * ((k-int(below.sum()))/int(equal.sum()))
    assert abs(weights.sum()-k)<1e-10
    return float(weights @ np.asarray(model['targets']) / k)
