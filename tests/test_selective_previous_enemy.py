import numpy as np
import pytest
import torch

from agents.sherlock.imitation_net import ImitationNet
from scripts import collect_combat_advice as collect, imitate, selective_dagger as d
from scripts import selective_advice_agent as live


def test_archive_full_planes_gap_match_change_and_separate_seat(tmp_path):
    step = np.array([1, 2, 4, 100, 102, 103], dtype=np.int16)
    rng = np.random.default_rng(4)
    raw = rng.integers(0, 128, size=(len(step),16,24,24), dtype=np.int8)
    rows = dict(step=np.arange(len(step)),pos=np.zeros((6,2)),feats=np.zeros((6,79)),
                mask=np.ones((6,6),bool),act=np.arange(6),sdx=np.zeros(6),sdy=np.zeros(6),base_act=np.arange(6))
    file = tmp_path / "card.npz"
    np.savez_compressed(file, planes=raw, global_step=step, **rows)
    rec = dict(path=file, sha256=collect.file_sha(file))
    original, original_rows, _ = d.mapped_part([rec,rec],tmp_path/"r2.int8")
    expanded, expanded_rows, _ = d.mapped_part([rec,rec],tmp_path/"new.int8",previous_enemy=True)
    np.testing.assert_array_equal(expanded[:,:16], original)
    for key in original_rows:
        np.testing.assert_array_equal(expanded_rows[key], original_rows[key])
    expected = np.zeros((6,24,24),np.int8)
    expected[1] = raw[0,10]
    expected[5] = raw[4,10]
    for start in (0, 6):
        np.testing.assert_array_equal(expanded[start:start+6,16], expected)


def test_online_stores_public_board_before_a_skipped_or_negative_only_turn(monkeypatch):
    actor = object.__new__(live.SelectiveAdviceAgent)
    actor.previous_enemy = True
    actor.training = False
    actor._previous_frame = None
    board = np.zeros((16,24,24),np.float32)
    board[10,7,9] = .75
    first = actor._input_board(board, 1, 1)
    assert first.shape == (17,24,24) and not first[16].any()
    current = np.zeros_like(board)
    second = actor._input_board(current, 2, 2)
    np.testing.assert_array_equal(second[:16], current)
    assert second[16,7,9] == np.float32(95/127) and second[16].sum() == second[16,7,9]
    actor._decide = lambda obs: ({"ally_ene":[-1]}, [0], {}, {}, {})
    base = np.zeros((1,3), int)
    assert actor._advise(3, {"steps":3,"match_steps":3}, base) is base
    assert actor._previous_frame is None
    assert not actor._input_board(board, 4, 4)[16].any()
    assert not actor._input_board(board, 6, 6)[16].any()
    assert actor._advise(101, {"steps":101,"match_steps":0}, base) is base
    assert not actor._input_board(board, 102, 1)[16].any()
    monkeypatch.setattr(live.Agent_x, "_reset_episode_state", lambda self: None)
    actor._reset_episode_state()
    assert actor._previous_frame is None


def test_real_advice_path_feeds_each_complete_board_once_before_choosing(monkeypatch):
    actor = object.__new__(live.SelectiveAdviceAgent)
    actor.previous_enemy, actor.training, actor.mode = True, False, "movement"
    actor.selective_counts, actor._previous_frame = {}, None
    boards = []
    class Recorder:
        def forward_all(self, planes, idx, pos, feats):
            boards.append(planes[0].clone())
            # A flat action distribution never permits an override.
            return torch.zeros((1,6)), None, None

    actor.members = [Recorder()]
    ctx = dict(ally_ene=np.array([80]), ally_pos=np.array([[7,9]]), sap_cost=30)
    actor._decide = lambda obs: (ctx,[0],{0:np.zeros(79,np.float32)},{0:np.ones(6,bool)}, {})
    current = np.zeros((16,24,24),np.float32)
    current[10,7,9] = .5  # Already canonical, also for seat one.
    monkeypatch.setattr(live, "map_planes", lambda _: current)
    monkeypatch.setattr(live, "substitute", lambda actor,obs,base,advice,mode,counts: base)
    base = np.zeros((1,3),int)
    for step in (1,2):
        actor._advise(step,{"steps":step,"match_steps":step},base)
        current[10].fill(0)
    assert len(boards) == 2 and not torch.count_nonzero(boards[0][16])
    assert not torch.count_nonzero(boards[1][10])
    assert boards[1][16,7,9] == np.float32(64/127)


def test_only_new_filter_weights_start_at_zero_and_they_can_learn():
    torch.manual_seed(2711)
    old = ImitationNet(79, ch=4, blocks=1, hidden=8)
    original_rng = torch.get_rng_state()
    torch.manual_seed(2711)
    new = ImitationNet(79, ch=4, blocks=1, hidden=8)
    imitate.add_previous_enemy_input(new)
    assert torch.equal(torch.get_rng_state(), original_rng)
    for key, value in new.state_dict().items():
        if key == "stem.0.weight":
            assert not torch.count_nonzero(value[:,16])
            value = value[:,:16]
        assert torch.equal(value,old.state_dict()[key])
    assert new.arch["in_ch"] == new.stem[0].in_channels == 17
    x = torch.ones(1,17,5,5)
    idx,pos,features = torch.zeros(1,dtype=torch.long), torch.tensor([[2,3]]), torch.zeros((1,79))
    for before, after in zip(old.forward_all(x[:,:16],idx,pos,features), new.forward_all(x,idx,pos,features)):
        torch.testing.assert_close(after,before,rtol=1e-5,atol=1e-6)
    new.stem[0](x).sum().backward()
    assert torch.count_nonzero(new.stem[0].weight.grad[:,16]) > 0


def test_history_checkpoint_is_distinct_and_cannot_masquerade_as_16_channel_student(tmp_path):
    net = ImitationNet(79,ch=4,blocks=1,hidden=8,in_ch=17)
    path = tmp_path/"candidate.pth"
    ckpt = dict(kind=live.HISTORY_KIND,arch=net.arch,policy=net.state_dict(),sap_own_tile=True)
    torch.save(ckpt,path)
    heads, own = live.load_heads(path)
    assert own and heads[0].arch["in_ch"] == 17
    torch.save({**ckpt,"kind":"imitation"},path)
    with pytest.raises(ValueError,match="Kartenebenen"):
        live.load_heads(path)


def test_changed_input_hash_rejected_even_with_same_map_numbers(tmp_path):
    path = tmp_path/"r2.pth"
    train = dict(inputs={"original": {"train":[{"seed":4,"sha256":"a"*64}]}}, parent_sha256="b"*64)
    ckpt = dict(kind="imitation",epochs=5,sap_own_tile=True,arch=dict(in_ch=16,ch=32,blocks=3,
                hidden=128,feat_dim=79,n_actions=6,sap_head=True,detach_value=True),
                selective_training=train)
    torch.save(ckpt,path)
    assert d.require_r2_inputs(path,train) == collect.file_sha(path)
    different = {**train,"inputs":{"original":{"train":[{"seed":4,"sha256":"c"*64}]}}}
    with pytest.raises(ValueError,match="R2"):
        d.require_r2_inputs(path,different)


@pytest.mark.parametrize("flags,soft,history", [
    ([], False, None),
    (["--distill-movement"], True, None),
    (["--previous-enemy-r2", "r2.pth"], False, "r2.pth"),
])
def test_classic_soft_and_history_cli_routes(monkeypatch,flags,soft,history):
    import sys
    from pathlib import Path
    args = ["train","--parent","parent.pth","--out","new.pth",
            "--original-data","original","--mixed-data","mixed"]
    seen = []
    monkeypatch.setattr(d,"train_mixed",seen.append)
    monkeypatch.setattr(sys,"argv",["selective_dagger",*args,*flags])
    d.main()
    assert seen[0].distill_movement is soft
    assert seen[0].previous_enemy_r2 == (Path(history) if history else None)


def test_mixed_soft_and_history_options_are_rejected_before_work(tmp_path,monkeypatch):
    import sys
    from types import SimpleNamespace
    a = SimpleNamespace(previous_enemy_r2=tmp_path/"r2.pth",distill_movement=True)
    with pytest.raises(ValueError,match="separate experiments"):
        d.train_mixed(a)
    with pytest.raises(ValueError,match="separate experiments"):
        d.mapped_part([],tmp_path/"unused",distill_movement=True,previous_enemy=True)
    args = ["train","--parent","parent.pth","--out","new.pth","--original-data","original",
            "--mixed-data","mixed","--distill-movement","--previous-enemy-r2","r2.pth"]
    monkeypatch.setattr(sys,"argv",["selective_dagger",*args])
    monkeypatch.setattr(d,"train_mixed",lambda a: pytest.fail("Mixed training dispatched"))
    with pytest.raises(SystemExit) as error:
        d.main()
    assert error.value.code == 2
