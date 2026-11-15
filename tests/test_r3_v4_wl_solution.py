from hashlib import sha256

import numpy as np
import pytest

from scripts import r3_v4_wl_solution as study


def test_signed_world_stream_matches_both_native_hashes_and_boundaries():
    a = np.zeros(study.SHAPE,dtype="<i2")
    a[201,1,8] = [5,-2,3]
    a[202,0,7] = [2,0,0]
    stream = study.WorldStream(None)
    stream.frames = [frame.tobytes() for frame in a]
    row = {"orders":stream.pack()}
    for length,name in ((202,"prefix_sha256"),(303,"commands_sha256")):
        row[name] = {side:sha256(a[:length,i].astype("<i8").tobytes()).hexdigest()
                     for i,side in enumerate(study.wl.SEATS)}
    study.verify_orders(row)
    row["prefix_sha256"]["player_1"] = row["prefix_sha256"]["player_0"]
    with pytest.raises(ValueError,match="hash"):
        study.verify_orders(row)


def test_registered_panel_filter_is_exhaustive_without_winner_selection():
    keys = [(i,s,"solution92") for i in range(184) for s in study.wl.SEATS]
    def archived(w):
        return dict(panel="archive",expected=dict(result=int(w>=2),wins=w,losses=3-w,points=2,opp_points=1,steps=303))
    cases = {k:archived(w) for k,w in zip(keys,[1]*4+[2]*42+[3]*322)}
    assert set(study.selected(cases)) == set(keys[:46])
    cases[keys[-1]] = archived(2)
    with pytest.raises(ValueError,match="368"):
        study.selected(cases)
