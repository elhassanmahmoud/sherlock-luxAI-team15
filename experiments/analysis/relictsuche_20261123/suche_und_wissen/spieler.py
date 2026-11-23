"""Retain the learned opening route and feed exact scoring information to its V16 continuation."""
from experiments.analysis.relictsuche_20261123.punktgrenzen.politik import AreaKnowledge
from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import PACKAGE,Scout
from scripts.r3_package import r3_package_agent


def make_player(side,arm):
    base=r3_package_agent(side,PACKAGE)
    if arm in ("wissen","beide"):base=AreaKnowledge(base)
    if arm in ("suche","beide"):base=Scout(base)
    return base
