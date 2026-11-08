"""Two synthetic offline callback checks; no agents, games or models constructed."""
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import artillery_training_exposure as A


def agent():
    return SimpleNamespace(training=False,cfg=SimpleNamespace(art_min_hits=3),
        belief=SimpleNamespace(point_tiles=np.zeros((2,2),bool)),param_est=A.UnavailableEstimator())


def test_training_counter_never_replaces_archived_eval_or_recomputes_it():
    a=agent();rows=[];flags=[];ctx={'x':np.ones(2)};sap=(1,2,2)
    def original(self,ctx,uid,sap):
        flags.append(self.training)
        assert self.training is True
        return False
    assert A.observe_training(a,original,ctx,7,sap,archived_eval=True,step=19,append=rows.append) is True
    assert flags==[True] and a.training is False
    assert rows[0]['eval_verdict'] is True and rows[0]['training_verdict'] is False
    assert (rows[0]['step'],rows[0]['uid'])==(19,7)
    assert rows[0]['eval_dropoff'] is None and rows[0]['training_min_hits']==3
    assert rows[0]['before']==rows[0]['after']


def test_counter_exception_restores_training_and_unchanged_context_state():
    a=agent();rows=[];flags=[];ctx={'x':np.ones(2)};sap=(0,1,3)
    def original(self,ctx,uid,sap):
        flags.append(self.training)
        raise RuntimeError('countercall failed')
    before=A.state_hashes(a,ctx,sap)
    with pytest.raises(RuntimeError,match='countercall failed'):
        A.observe_training(a,original,ctx,2,sap,archived_eval=False,step=5,append=rows.append)
    assert flags==[True] and a.training is False and A.state_hashes(a,ctx,sap)==before
    assert rows==[]
