"""Post-step diagnostics. Known fields and ship measurements use only the player's public information."""
import numpy as np

from scripts.scoring import match_points_after_step
from scripts.solution_passive import finish_match


SECTIONS = ("boundary_0", "1-33", "34-66", "67-100")


def counters():
    return dict(steps=0, active_unit_samples=0, active_energy_sum=0, mask_losses=0,
                newly_negative=0, detectable_slot_reuses=0, known_occupied_cell_steps=0)


def summary(values):
    steps, units = values["steps"], values["active_unit_samples"]
    return dict(**values, mean_active_units=units / steps, mean_team_active_energy=values["active_energy_sum"] / steps,
                mean_energy_per_active_unit=values["active_energy_sum"] / units if units else None,
                plausible_uid_departures=values["mask_losses"] + values["newly_negative"] + values["detectable_slot_reuses"])


def ships(obs, team):
    mask = np.asarray(obs["units_mask"][team], dtype=bool)
    energy = np.asarray(obs["units"]["energy"][team]).reshape(-1)
    return mask, energy, np.asarray(obs["units"]["position"][team]), mask & (energy >= 0)


def known_occupied(known, pos, active):
    return {tuple(map(int, xy)) for xy in pos[active] if known[tuple(xy)]}


class Observation:
    def __init__(self, team: int):
        if team not in (0, 1):
            raise ValueError("Expected team 0 or 1")
        self.team = team
        self.steps = 0
        self.last_known = None
        self.matches = [dict(match=i + 1, first_confirmed=None, first_known_occupied_before=None,
                             first_known_occupied_after=None, first_known_held_through_action=None,
                             first_own_point_gain=None, final=None, sections={s: counters() for s in SECTIONS})
                        for i in range(3)]

    def record(self, before, after, info, known_world):
        t, m = int(before["steps"]), int(before["match_steps"])
        if (t != self.steps or not 0 <= t < 303 or m != t % 101 or int(after["steps"]) != t + 1
                or int(after["match_steps"]) != (m + 1) % 101):
            raise ValueError(f"Unexpected course transition at {t}/{m}")
        row = self.matches[t // 101]
        section = SECTIONS[0 if m == 0 else 1 if m <= 33 else 2 if m <= 66 else 3]
        stats = row["sections"][section]
        known = np.asarray(known_world, dtype=bool)
        _, _, bpos, was_active = ships(before, self.team)
        mask, energy, apos, active = ships(after, self.team)
        if not m:
            # At action zero the engine removes the previous match's remaining units before moving anyone.
            was_active = np.zeros_like(was_active)
            prior = 0 if self.last_known is None else int((self.last_known & known).sum())
            row["opening_known_cells"] = int(known.sum())
            row["opening_previously_known_cells"] = prior
        pre = known_occupied(known, bpos, was_active)
        post = known_occupied(known, apos, active)
        for key, fields in (("first_known_occupied_before", pre), ("first_known_occupied_after", post),
                            ("first_known_held_through_action", pre & post)):
            if row[key] is None and fields:
                row[key] = dict(global_step=t, match_step=m, world_cells=[list(xy) for xy in sorted(fields)])
        if row["first_confirmed"] is None and known.any():
            row["first_confirmed"] = dict(global_step=t, match_step=m, known_cell_count=int(known.sum()),
                                          inherited_from_previous_match=bool(m == 0 and row["opening_previously_known_cells"]))
        self.last_known = known.copy()

        spawn = (0, 0) if self.team == 0 else tuple(np.asarray(known.shape) - 1)
        # Non-adjacent return to spawn cannot be an ordinary move; same/adjacent slot reuse is unobservable.
        reused = was_active & active & np.all(apos == spawn, axis=1) & (np.abs(apos - bpos).sum(axis=1) > 1)
        stats["steps"] += 1
        stats["active_unit_samples"] += int(active.sum())
        stats["active_energy_sum"] += int(energy[active].sum(dtype=np.int64))
        stats["mask_losses"] += int((was_active & ~mask).sum())
        stats["newly_negative"] += int((was_active & mask & ~active).sum())
        stats["detectable_slot_reuses"] += int(reused.sum())
        stats["known_occupied_cell_steps"] += len(post)

        points = match_points_after_step(before, after, info)
        gain = points - np.asarray(before["team_points"], dtype=np.int64)
        if np.any(gain < 0):
            raise ValueError(f"Negative score gain at {t}")
        if gain[self.team] and row["first_own_point_gain"] is None:
            row["first_own_point_gain"] = dict(global_step=t, match_step=m, gain=int(gain[self.team]),
                                               source="external_final_score" if m == 100 else "public_score")
        if m == 100:
            # External scoring only. Hidden terminal energies may include still-masked negative ships.
            state = info["final_state"]
            raw = np.asarray(state.units.energy)[..., 0]
            team_energy = np.where(np.asarray(state.units_mask, bool), raw, 0).sum(axis=1, dtype=np.int64).tolist()
            final = finish_match(before["team_wins"], after["team_wins"], points.tolist(), team_energy)
            row["final"] = dict(**final, team_points=points.tolist(), own_won=final["winner"] == self.team)
        self.steps += 1

    def report(self):
        if self.steps != 303:
            raise ValueError(f"Expected a complete game; received {self.steps} transitions")
        matches = []
        for row in self.matches:
            sections = row["sections"]
            total = {key: sum(v[key] for v in sections.values()) for key in counters()}
            matches.append(dict(row, sections={s: summary(v) for s, v in sections.items()}, summary=summary(total)))
        return dict(team=self.team, steps=self.steps, team_points_total=[sum(r["final"]["team_points"][t]
                    for r in matches) for t in (0, 1)], matches=matches,
                    measurement="Action steps and world coordinates; active own ships and energy sampled after each step. "
                                "Occupancy uses own public positions and the agent's pre-action confirmed map. "
                                "Terminal scoring and tiebreak energy use final_state for external measurement only.")
