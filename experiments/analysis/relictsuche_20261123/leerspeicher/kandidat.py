"""Reuse the shipped V16's conservative zero-history mode from the first match transition on low sight."""
from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import PACKAGE
from scripts.r3_package import r3_package_agent


def switch(b):
    b.keep_dead=True
    b.keep_dead_fast=False


class ZeroMemory:
    def __init__(self,base):
        self.base=base
        self.switched=False

    def __getattr__(self,key):
        return getattr(self.base,key)

    def new_game(self,player=None):
        self.base.new_game(player)
        b=self.base._imitation.belief
        b.keep_dead=False
        b.keep_dead_fast=True
        self.switched=False

    def act(self,step,obs):
        if not self.switched and step==101 and int(self.base.env_cfg["unit_sensor_range"])==1:
            switch(self.base._imitation.belief)
            self.switched=True
        return self.base.act(step,obs)


def create(side):
    return ZeroMemory(r3_package_agent(side,PACKAGE))
