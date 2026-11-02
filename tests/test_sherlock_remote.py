"""Fernspiel: Stellvertreter (scripts/sherlock_remote_stub.py) und Server (scripts/sherlock_server.py)."""

import json
import threading
import urllib.error
import urllib.request
import zipfile
from http.server import ThreadingHTTPServer

import numpy as np
import pytest

from scripts import sherlock_remote_stub as stub
from scripts import sherlock_server as srv


def _obs():
    return {
        "units": {"position": np.arange(64, dtype=np.int16).reshape(2, 16, 2),
                  "energy": np.linspace(-1, 400, 32).astype(np.int32).reshape(2, 16)},
        "units_mask": np.zeros((2, 16), dtype=bool),
        "sensor_mask": np.ones((24, 24), dtype=bool),
        "map_features": {"energy": np.random.default_rng(0).normal(size=(24, 24)).astype(np.float32),
                         "tile_type": np.full((24, 24), -1, dtype=np.int8)},
        "relic_nodes": np.full((6, 2), -1, dtype=np.int64),
        "team_points": np.array([3, 7], dtype=np.int32),
        "steps": np.int32(17),
        "match_steps": 17,
        "nan": np.array([np.nan, np.inf], dtype=np.float64),
    }


def _same(a, b):
    if isinstance(a, dict):
        assert set(a) == set(b)
        for k in a:
            _same(a[k], b[k])
    elif isinstance(a, (np.ndarray, np.generic)):
        assert type(a) is type(b) and a.dtype == b.dtype and np.shape(a) == np.shape(b)
        assert np.array_equal(a, b, equal_nan=True)
    else:
        assert a == b and type(a) is type(b)


def test_encode_decode_is_lossless_through_json():
    obs = _obs()
    _same(obs, srv.decode(json.loads(json.dumps(stub.encode(obs)))))


@pytest.mark.parametrize("bad", [{"__nd__": [1], "dtype": "object"}, {"__nd__": [[1], [1, 2]], "dtype": "int64"},
                                 {"__nd__": ["x"], "dtype": "float32"}])
def test_decode_rejects_unsafe_or_broken_arrays(bad):
    with pytest.raises(srv.BadRequest):
        srv.decode({"a": bad})


class _Dummy:
    def __init__(self, player):
        self.player, self.calls, self.cfg = player, 0, None

    def set_env_cfg(self, cfg):
        self.cfg = cfg

    def act(self, step, obs):
        self.calls += 1
        return np.full((int(self.cfg["max_units"]), 3), int(obs["units"]["position"][0, 0, 1]) + step)


@pytest.fixture
def server(monkeypatch):
    made = []

    def factory(player):
        made.append(_Dummy(player))
        return made[-1]

    sessions = srv.Sessions(factory, max_sessions=2)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.make_handler(sessions, "geheim", quiet=True))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}"
    monkeypatch.setenv("SHERLOCK_URL", url)
    monkeypatch.setenv("SHERLOCK_TOKEN", "geheim")
    yield url, sessions, made
    httpd.shutdown()
    httpd.server_close()


def test_stub_plays_through_server_and_repeated_step_is_answered_from_cache(server):
    url, sessions, made = server
    a = stub.Agent_x("player_1", agent_path=None)
    assert a.name  # der Kurs-Runner schreibt den Namen ins Replay
    a.set_env_cfg({"max_units": np.int32(16), "map_width": 24})
    act = a.act(5, _obs())
    assert act.shape == (16, 3) and act.dtype.kind == "i" and (act == 1 + 5).all()
    assert made[0].player == "player_1" and isinstance(made[0].cfg["max_units"], np.int32)
    a._post("/act", {"session": a.session, "step": 5, "obs": stub.encode(_obs())})  # Wiederholung
    assert made[0].calls == 1
    a.act(6, _obs())
    assert made[0].calls == 2 and a.failures == 0


def test_wrong_token_and_oversize_body_are_rejected(server, monkeypatch):
    url, _, made = server
    monkeypatch.setenv("SHERLOCK_TOKEN", "falsch")
    with pytest.raises(RuntimeError, match="nicht erreichbar"):
        stub.Agent_x("player_0")
    assert made == []
    req = urllib.request.Request(url + "/new", data=b"x", method="POST",
                                 headers={"X-Sherlock-Token": "geheim", "Content-Length": str(srv.MAX_BODY + 1)})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req, timeout=10)
    assert e.value.code == 413


def test_unknown_or_evicted_session_falls_back_to_stay(server):
    _, sessions, _ = server
    a = stub.Agent_x("player_0")
    a.set_env_cfg({"max_units": 16})
    stub.Agent_x("player_0")
    stub.Agent_x("player_1")  # max_sessions=2: die aelteste Sitzung (a) faellt weg
    assert len(sessions.items) == 2
    act = a.act(3, _obs())
    assert (act == 0).all() and act.shape == (16, 3) and a.failures == 1


def test_client_zip_contains_only_stub_and_connection(tmp_path):
    out = srv.build_client_zip("https://beispiel.trycloudflare.com/", "tok123", tmp_path / "f.zip")
    with zipfile.ZipFile(out) as z:
        names = sorted(z.namelist())
        assert names == sorted(f"{srv.CLIENT_PKG}/{n}" for n in
                               ("__init__.py", "main.py", "verbindung.json", "LIESMICH.txt"))
        assert json.loads(z.read(f"{srv.CLIENT_PKG}/verbindung.json")) == {
            "url": "https://beispiel.trycloudflare.com", "token": "tok123"}
        main = z.read(f"{srv.CLIENT_PKG}/main.py").decode()
    assert "import torch" not in main and "belief" not in main.lower()
