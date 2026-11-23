"""Feste Priorität mit einer einzigen V16-Auswertung und einer verbindlichen Endaktion."""
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
MIDDLE=STUDY.parent/"mitte2"
sys.path.insert(0,str(STUDY))
from kandidat import SignalScout
sys.path.insert(0,str(MIDDLE))
from mitte import Middle, Policy, model, g, sha, MODEL_SHA, PACKAGE, V16, SOURCE_SHA, SOURCE


class ExistingCommand:
    """Bietet dem originalen Mitte2-Code genau den bereits ermittelten V16-Befehl."""
    def __init__(self, base):
        self.original=base
        self.step=-1
        self.obs=None
        self.command=None
        self.used=False

    def __getattr__(self,name):
        return getattr(self.original,name)

    def act(self,step,obs):
        if self.used or step!=self.step or obs is not self.obs:
            raise ValueError("Doppelte Anfrage oder abweichende Originalbeobachtung")
        self.used=True
        return self.command


class SharedMiddle(Middle):
    def __init__(self, loader,side,net):
        # Policy.__init__ installiert genau die zwei originalen passiven Logit-Hooks.
        # Die Entscheidung bleibt die unveränderte Methode Middle.act.
        Policy.__init__(self,loader,net)
        self.team=int(side[-1]);self.apply=True
        self.event=self.original=None
        self.behind_steps=self.options_steps=0


class Combination:
    def __init__(self,side,net,arm):
        self.arm=arm
        self.scout=SignalScout(side,arm in ("signal","beide"))
        self.base=self.scout.base
        self.fixed=ExistingCommand(self.base)
        self.middle=SharedMiddle(self.fixed,side,net)
        self.with_middle=arm in ("mitte","beide")
        original=self.scout.v16_act
        def capture(step,obs):
            if step!=self.calls or self.incoming is not obs:raise ValueError("Original wurde doppelt oder mit falscher Sicht aufgerufen")
            self.calls+=1
            self.native=original(step,obs)
            return self.native
        self.scout.v16_act=capture

    def __getattr__(self,name):
        return getattr(self.scout,name)

    def new_game(self,side):
        self.scout.new_game(side)
        self.calls=0
        self.native=None
        self.incoming=None
        self.events=[]

    def act(self,step,obs):
        self.incoming=obs
        n=len(self.scout.changes)
        command=self.scout.act(step,obs)
        self.incoming=None
        if self.calls!=step+1:raise ValueError("V16-Entscheidung fehlt")
        has_scout=len(self.scout.changes)>n
        chooser=None
        if has_scout:
            chooser="signal"
        elif self.with_middle:
            self.fixed.step,self.fixed.obs,self.fixed.command,self.fixed.used=step,obs,self.native,False
            old=self.middle.changed
            command=self.middle.act(step,obs)
            if not self.fixed.used or self.fixed.command is not self.native:
                raise ValueError("Nicht die Ursprungsvorhersage verwendet")
            if self.middle.changed>old:chooser="mitte"
        changed=np.flatnonzero(np.any(command!=self.native,axis=1))
        if len(changed)!=int(chooser is not None):
            raise ValueError("Falsche Zahl tatsächlich übernommener Befehle")
        if chooser is not None:
            u=int(changed[0]);world=int(command[u,0]);inner=self.base._imitation
            canon=int(g.mirror_dir(world) if inner.belief.mirrored else world)
            ids=np.asarray(inner.last_fz[1])
            row=np.flatnonzero(ids==u)
            if (len(row)!=1 or not inner.last_fz[3][int(row[0]),canon] or not 0<=world<=4 or
                    inner._prev_actions.get(u)!=canon or u in inner._sap_hits or not np.array_equal(command[u],[world,0,0])):
                raise ValueError("Maskierung, Richtungsübertragung oder Aktionsgeschichte weicht ab")
            # Ein umgelenkter Suchschritt kann die zuletzt gespeicherten Originalbefehle
            # des Parameterschätzers berichtigen. Bei inaktivem Schätzer ist dies ein No-op.
            inner.param_est.record_played_actions(command)
            if inner.param_est._prev is not None and not np.array_equal(inner.param_est._prev["act"],command):
                raise ValueError("Parameterschätzer hat den falschen Befehl gespeichert")
            self.events.append(dict(step=step,uid=u,module=chooser,previous=int(self.native[u,0]),world=world))
        return command
