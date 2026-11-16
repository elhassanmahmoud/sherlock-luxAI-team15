"""Pair the locked agent with archived native R3 and V15 on the entire specified block."""
import json
import sys

from bericht import rows, group, compare
from duelle import HERE, POLICY_STUDY, archive_schedule, spiele

sys.path.insert(0, str(POLICY_STUDY / "diagnose"))
from replay import originals


def assess():
    _, refs = originals(spiele.ROOT)
    data = rows(HERE / "archiv", archive_schedule())
    current = group(data, "unit", "solution")
    result = dict(unit=sum(current.values()), n=len(current))
    for who in ("r3", "v15"):
        reference = {key: refs[who][key][0] for key in current}
        result[who] = sum(reference.values())
        result["vs_" + who] = compare(current, reference)
    return result


if __name__ == "__main__":
    print(json.dumps(assess(), indent=2, sort_keys=True))
