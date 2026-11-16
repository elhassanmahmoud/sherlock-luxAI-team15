"""Exact two-sided sign randomization over complete map pairs (two starts each)."""
from collections import Counter


def sign_test(comparison):
    by_map = Counter()
    for seed, _ in comparison["gained"]:
        by_map[seed] += 1
    for seed, _ in comparison["lost"]:
        by_map[seed] -= 1
    nonzero = [v for v in by_map.values() if v]
    observed = abs(sum(nonzero))
    distribution = Counter({0: 1})
    for v in nonzero:
        both_signs = Counter()
        for total, count in distribution.items():
            both_signs[total + v] += count
            both_signs[total - v] += count
        distribution = both_signs
    extreme = sum(n for total, n in distribution.items() if abs(total) >= observed)
    return dict(informative_maps=len(nonzero), p_two_sided=extreme / 2**len(nonzero))


if __name__ == "__main__":
    import json
    from pathlib import Path

    here = Path(__file__).resolve().parent
    first = json.loads((here / "auswertung.json").read_bytes())["solution"]["vs_r3"]
    second = json.loads((here / "bestaetigung.json").read_bytes())["vs_r3"]
    print(json.dumps({"erstvergleich": sign_test(first), "zweiter_satz": sign_test(second)}, indent=2))
