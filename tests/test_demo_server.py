"""Demo-Seite vom 22.10.2026: Spiele per HTTP starten, Replays nur aus replays/ ausliefern."""
import json
import threading
import urllib.error
import urllib.request

import pytest

from scripts import demo_server


@pytest.fixture
def server(tmp_path, monkeypatch):
    replays = tmp_path / "replays"
    (replays / "15_vs_2").mkdir(parents=True)
    monkeypatch.setattr(demo_server, "REPLAYS", replays)
    calls = []

    def fake_player(gegner, seite):
        calls.append((gegner, seite))
        html = replays / "15_vs_2" / f"spiel_{len(calls)}.html"
        html.write_text("<html>replay</html>", encoding="utf-8")
        return {"gegner": gegner, "gegner_name": "Solution_92_Kaggle", "seite": seite, "sherlock": f"player_{seite}",
                "seed": 7, "ours": 2, "theirs": 1, "matches": [True, False, True],
                "html": f"replays/15_vs_2/{html.name}", "datum": "2026-10-22", "zeit": "15:00"}

    srv = demo_server.DemoServer(("127.0.0.1", 0), player=fake_player)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv, f"http://127.0.0.1:{srv.server_address[1]}", calls, replays
    srv.shutdown()
    srv.server_close()


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.read()


def _post(url, data, ctype="application/json"):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": ctype}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_page_and_ping(server):
    _, base, _, _ = server
    status, body = _get(base + "/")
    assert status == 200 and "Sherlock".encode() in body
    assert json.loads(_get(base + "/api/ping")[1]) == {"ok": True, "busy": False}


def test_play_records_history_and_serves_replay(server):
    _, base, calls, _ = server
    status, game = _post(base + "/api/play", {"gegner": "solution", "seite": 1})
    assert status == 200 and calls == [("solution", 1)]
    assert game["url"] == "/replays/15_vs_2/spiel_1.html"
    assert _get(base + game["url"]) == (200, b"<html>replay</html>")
    history = json.loads(_get(base + "/api/history")[1])
    assert [g["url"] for g in history["games"]] == [game["url"]]


def test_rejects_bad_requests_without_playing(server):
    srv, base, calls, _ = server
    assert _post(base + "/api/play", {"gegner": "rm -rf", "seite": 0})[0] == 400
    assert _post(base + "/api/play", {"gegner": "solution", "seite": 2})[0] == 400
    assert _post(base + "/api/play", {"gegner": "solution", "seite": 0}, ctype="text/plain")[0] == 415
    srv.lock.acquire()  # laufendes Spiel
    try:
        assert _post(base + "/api/play", {"gegner": "solution", "seite": 0})[0] == 409
    finally:
        srv.lock.release()
    assert calls == []


def test_replay_paths_stay_inside_replays(server, tmp_path):
    _, base, _, _ = server
    (tmp_path / "geheim.html").write_text("x")
    assert demo_server.replay_file("/replays/../geheim.html") is None
    assert demo_server.replay_file("/replays/%2e%2e/geheim.html") is None
    assert demo_server.replay_file("/README.md") is None
    with pytest.raises(urllib.error.HTTPError):
        _get(base + "/replays/../geheim.html")
