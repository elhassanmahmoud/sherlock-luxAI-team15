"""Sherlock (Team 15) als Fernspiel-Gegner fuer den Kurs-Runner.

Diese Datei enthaelt keine Spiellogik. Sie schickt in jedem Schritt die Beobachtung an den
Sherlock-Server von Team 15 und gibt die zurueckgeschickten Aktionen an den Runner weiter.
Adresse und Zugangsschluessel stehen in ``verbindung.json`` neben dieser Datei; die
Umgebungsvariablen SHERLOCK_URL und SHERLOCK_TOKEN haben Vorrang.

Benoetigt nur numpy und die Python-Standardbibliothek. Sherlock lernt hier nicht weiter;
update() und save_agent() tun deshalb nichts.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_TIMEOUT = 60
_RETRIES = 3


def _connection():
    conf = {}
    path = os.path.join(_HERE, "verbindung.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            conf = json.load(f)
    url = os.environ.get("SHERLOCK_URL") or conf.get("url")
    token = os.environ.get("SHERLOCK_TOKEN") or conf.get("token")
    if not url or not token:
        raise RuntimeError("Sherlock-Fernspiel: verbindung.json mit url und token fehlt")
    return url.rstrip("/"), token


def encode(x):
    """Beobachtung verlustfrei als JSON: Arrays behalten Form und Datentyp."""
    if isinstance(x, dict):
        return {str(k): encode(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [encode(v) for v in x]
    if isinstance(x, (bool, int, float, str)) or x is None:
        return x
    if isinstance(x, np.generic):
        return {"__nd__": x.item(), "dtype": x.dtype.name, "scalar": True}
    a = np.asarray(x)  # numpy- und jax-Arrays
    return {"__nd__": a.tolist(), "dtype": a.dtype.name}


class Agent_x:
    """Gleiche Schnittstelle wie ein normaler Kurs-Agent; gespielt wird auf dem Server."""

    def __init__(self, player, agent_path=None, **_ignored):
        self.player = player
        self.name = "Sherlock (Team 15)"  # der Kurs-Runner schreibt den Namen ins Replay
        self.env_cfg = None
        self.url, self.token = _connection()
        self.failures = 0
        try:
            self.session = self._post("/new", {"player": player})["session"]
        except Exception as e:
            raise RuntimeError(
                "Sherlock-Server nicht erreichbar (%s). Bitte Team 15 Bescheid geben." % e) from None
        print("[Sherlock-Fernspiel] verbunden als %s" % player)

    # ------------------------------------------------------------ runner API
    def set_env_cfg(self, env_cfg):
        self.env_cfg = env_cfg
        self._post("/env_cfg", {"session": self.session, "env_cfg": encode(env_cfg)})

    def set_to_eval_mode(self):
        pass

    def set_to_train_mode(self):
        pass

    def act(self, step, obs):
        try:
            r = self._post("/act", {"session": self.session, "step": int(step), "obs": encode(obs)})
            return np.asarray(r["actions"], dtype=int)
        except Exception as e:
            self.failures += 1
            print("[Sherlock-Fernspiel] Schritt %s ohne Antwort (%s), Units bleiben stehen" % (step, e),
                  file=sys.stderr)
            n = int((self.env_cfg or {}).get("max_units", 16))
            return np.zeros((n, 3), dtype=int)

    def update(self, *args, **kwargs):
        pass

    def save_agent(self, *args, **kwargs):
        pass

    # --------------------------------------------------------------- intern
    def _post(self, path, payload):
        data = json.dumps(payload).encode("utf-8")
        last = None
        for attempt in range(_RETRIES):
            req = urllib.request.Request(self.url + path, data=data, method="POST", headers={
                "Content-Type": "application/json",
                "User-Agent": "SherlockFernspiel/1.0",
                "X-Sherlock-Token": self.token,
            })
            try:
                with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code < 500:  # falscher Schluessel, unbekanntes Spiel: Wiederholen hilft nicht
                    raise RuntimeError("HTTP %d" % e.code) from None
                last = e
            except (urllib.error.URLError, OSError) as e:
                last = e
            time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(str(last))
