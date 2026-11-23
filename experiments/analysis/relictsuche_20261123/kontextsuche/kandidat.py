"""Retain the already verified accept/veto action streams and use only the eleven public inputs."""
from functools import lru_cache
import json
from pathlib import Path
from weakref import ref

from experiments.analysis.relictsuche_20261123.netzvertrauen.kandidat import ScoutVote
from experiments.analysis.relictsuche_20261123.netzvertrauen.lernen import predict
from experiments.analysis.relictsuche_20261123.netzvertrauen.stimmen import BASE

HERE=Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def specification():
    result=json.loads((HERE/"modell.json").read_text())
    assert tuple(result["features"])==BASE and len(result["model"]["beta"])==len(BASE)
    return result


class PublicGate:
    """ScoutVote queries the boolean exactly once, after recording the first alternative's public features."""
    def __init__(self,actor):
        self.actor=ref(actor)

    def __bool__(self):
        who=self.actor()
        assert who is not None and who.decision is None and who.at is not None
        spec=specification()
        return predict(who.features,spec["model"])>=spec["threshold"]


def create(side):
    actor=ScoutVote(side)
    actor.forced=PublicGate(actor)
    return actor
