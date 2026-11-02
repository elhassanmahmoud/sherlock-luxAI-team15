"""Fernspiel-Server: andere Teams spielen gegen Sherlock, ohne Code oder Gewichte zu bekommen.

Der Server laedt genau das Battle-Paket ``Gruppe15.zip`` (eingefrorene Abgabe) in einen
temporaeren Ordner und beantwortet pro Spielschritt eine Beobachtung mit Sherlocks Aktionen.
Das andere Team bekommt nur ``Sherlock_Fernspiel.zip`` mit einem Stellvertreter-Agenten
(scripts/sherlock_remote_stub.py), Adresse und Zugangsschluessel.

Start mit oeffentlicher Adresse (cloudflared, Mac bleibt wach, Zip wird neu gebaut):

    .venv/bin/python -m scripts.sherlock_server --tunnel

Nur lokal (Test): ``.venv/bin/python -m scripts.sherlock_server --port 8765``

Sicherheit: nur JSON (kein pickle), Schluessel im Header, Groessen- und Sitzungsgrenzen,
Fehlermeldungen ohne Traceback an den Client. Der Server schreibt keine Gewichte.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Optional

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BATTLE_ZIP = ROOT / "Gruppe15.zip"
TOKEN_FILE = ROOT / ".fernspiel_token"
STUB_SRC = Path(__file__).resolve().with_name("sherlock_remote_stub.py")
CLIENT_ZIP = ROOT / "Sherlock_Fernspiel.zip"
CLIENT_PKG = "Sherlock15"

DTYPES = {"bool", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64",
          "float16", "float32", "float64"}
MAX_BODY = 4 * 1024 * 1024
MAX_SESSIONS = 8
IDLE_SECONDS = 30 * 60
MAX_DEPTH = 12


class BadRequest(ValueError):
    pass


def decode(x, depth: int = 0):
    """Gegenstueck zu sherlock_remote_stub.encode; erlaubt nur einfache Datentypen."""
    if depth > MAX_DEPTH:
        raise BadRequest("zu tief verschachtelt")
    if isinstance(x, dict):
        if "__nd__" in x:
            dt = x.get("dtype")
            if dt not in DTYPES:
                raise BadRequest("Datentyp nicht erlaubt")
            try:
                a = np.array(x["__nd__"], dtype=dt)
            except (TypeError, ValueError, OverflowError):
                raise BadRequest("ungueltiges Array") from None
            return a[()] if x.get("scalar") else a
        return {str(k): decode(v, depth + 1) for k, v in x.items()}
    if isinstance(x, list):
        return [decode(v, depth + 1) for v in x]
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    raise BadRequest("Typ nicht erlaubt")


# --------------------------------------------------------------------- Agent laden
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def battle_agent_factory(zip_path: Path = BATTLE_ZIP) -> Callable[[str], object]:
    """Battle-Zip in einen temporaeren Ordner entpacken und Agent_x daraus importieren."""
    if not zip_path.exists():
        raise SystemExit(f"{zip_path} fehlt: zuerst python -m scripts.build_submission --battle")
    tmp = Path(tempfile.mkdtemp(prefix="sherlock_fernspiel_"))
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if name.startswith("/") or ".." in Path(name).parts or not name.startswith("Gruppe15/"):
                raise SystemExit(f"unerwarteter Eintrag in {zip_path}: {name}")
        z.extractall(tmp)
    sys.path.insert(0, str(tmp))
    from Gruppe15.main import Agent_x  # noqa: E402  (genau der Code aus der Zip)

    weights = tmp / "Gruppe15" / "agent.pth"
    print(f"[Fernspiel] Battle-Zip {zip_path.name} sha256 {sha256(zip_path)[:16]}..., "
          f"agent.pth sha256 {sha256(weights)[:16]}...", flush=True)

    def make(player: str):
        agent = Agent_x(player, agent_path=str(weights))  # wie der Kurs-Runner
        agent.set_to_eval_mode()
        if not getattr(agent.cfg, "frozen", False):
            raise SystemExit("Battle-Zip ist nicht eingefroren (cfg.frozen=False)")
        return agent

    return make


# --------------------------------------------------------------------- Sitzungen
class Sessions:
    def __init__(self, factory: Callable[[str], object], max_sessions: int = MAX_SESSIONS,
                 idle_seconds: float = IDLE_SECONDS):
        self.factory = factory
        self.max_sessions = max_sessions
        self.idle_seconds = idle_seconds
        self.items: dict = {}
        self.lock = threading.Lock()
        self.games = 0

    def new(self, player: str) -> str:
        if player not in ("player_0", "player_1"):
            raise BadRequest("player muss player_0 oder player_1 sein")
        agent = self.factory(player)
        sid = secrets.token_hex(12)
        with self.lock:
            now = time.time()
            for k in [k for k, v in self.items.items() if now - v["last"] > self.idle_seconds]:
                del self.items[k]
            while len(self.items) >= self.max_sessions:
                del self.items[min(self.items, key=lambda k: self.items[k]["last"])]
            self.items[sid] = {"agent": agent, "last": now, "lock": threading.Lock(),
                               "step": None, "actions": None}
            self.games += 1
        return sid

    def get(self, sid) -> dict:
        with self.lock:
            s = self.items.get(sid) if isinstance(sid, str) else None
            if s is None:
                raise KeyError("unbekanntes Spiel")
            s["last"] = time.time()
            return s


def make_handler(sessions: Sessions, token: str, quiet: bool = False):
    class Handler(BaseHTTPRequestHandler):
        server_version = "Sherlock"
        sys_version = ""

        def log_message(self, fmt, *args):
            pass

        def _send(self, code: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self._send(200, {"ok": True})
            else:
                self._send(404, {"error": "nicht gefunden"})

        def do_POST(self):
            if not hmac.compare_digest(self.headers.get("X-Sherlock-Token", ""), token):
                return self._send(403, {"error": "falscher Schluessel"})
            try:
                n = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                n = -1
            if n <= 0 or n > MAX_BODY:
                return self._send(413, {"error": "Anfrage zu gross oder leer"})
            try:
                body = json.loads(self.rfile.read(n).decode("utf-8"))
                if not isinstance(body, dict):
                    raise BadRequest("JSON-Objekt erwartet")
                return self._send(200, self._route(body))
            except (BadRequest, json.JSONDecodeError, UnicodeDecodeError) as e:
                return self._send(400, {"error": str(e)})
            except KeyError as e:
                return self._send(404, {"error": str(e).strip("'")})
            except Exception:
                traceback.print_exc()  # nur lokal, nie an den Client
                return self._send(500, {"error": "interner Fehler"})

        def _route(self, body: dict) -> dict:
            if self.path == "/new":
                sid = sessions.new(body.get("player"))
                if not quiet:
                    print(f"[Fernspiel] Spiel {sessions.games} gestartet ({body.get('player')}), "
                          f"{time.strftime('%H:%M:%S')}", flush=True)
                return {"session": sid}
            s = sessions.get(body.get("session"))
            if self.path == "/env_cfg":
                cfg = decode(body.get("env_cfg"))
                if not isinstance(cfg, dict):
                    raise BadRequest("env_cfg muss ein Objekt sein")
                with s["lock"]:
                    s["agent"].set_env_cfg(cfg)
                return {"ok": True}
            if self.path == "/act":
                step = body.get("step")
                if not isinstance(step, int):
                    raise BadRequest("step fehlt")
                obs = decode(body.get("obs"))
                if not isinstance(obs, dict):
                    raise BadRequest("obs muss ein Objekt sein")
                with s["lock"]:
                    if s["step"] == step and s["actions"] is not None:  # Wiederholung nach Netzfehler
                        return {"actions": s["actions"]}
                    actions = np.asarray(s["agent"].act(step=step, obs=obs)).astype(int).tolist()
                    s["step"], s["actions"] = step, actions
                return {"actions": actions}
            raise KeyError("unbekannter Pfad")

    return Handler


# --------------------------------------------------------------------- Zip fuer das andere Team
def load_token() -> str:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    tok = secrets.token_urlsafe(24)
    TOKEN_FILE.write_text(tok + "\n")
    os.chmod(TOKEN_FILE, 0o600)
    return tok


README = """Sherlock (Team 15) - Fernspiel-Gegner

Sherlock spielt auf dem Rechner von Team 15. Dieser Ordner enthaelt keine Spiellogik,
nur einen Stellvertreter, der jede Beobachtung an Sherlock schickt und die Aktionen
zurueckgibt. Dafuer braucht der Rechner Internet.

1. Den Ordner {pkg} in die Projektwurzel legen (neben main.py und Paths.csv).
2. Zeile fuer Paths.csv (Gruppennummer frei waehlbar, hier 15):
   15;{pkg}.main.Agent_x;;
3. In main.py zum Beispiel run_agents(DEINE_GRUPPE, 15, train=False, games_to_play=5).
   Beim Start erscheint: [Sherlock-Fernspiel] verbunden als player_1

Hinweise:
- Benoetigt nur numpy und die Python-Standardbibliothek.
- Ein Spiel dauert wegen der Uebertragung etwa 30-90 Sekunden laenger als lokal.
- "Sherlock-Server nicht erreichbar": Team 15 Bescheid geben, der Server laeuft
  nicht oder die Adresse hat sich geaendert (dann gibt es eine neue verbindung.json).
- Bitte die Datei verbindung.json nicht weitergeben.
"""


def build_client_zip(url: str, token: str, out: Path = CLIENT_ZIP) -> Path:
    tmp = out.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{CLIENT_PKG}/__init__.py", "from .main import Agent_x  # noqa: F401\n")
        z.write(STUB_SRC, f"{CLIENT_PKG}/main.py")
        z.writestr(f"{CLIENT_PKG}/verbindung.json",
                   json.dumps({"url": url.rstrip("/"), "token": token}, indent=2) + "\n")
        z.writestr(f"{CLIENT_PKG}/LIESMICH.txt", README.format(pkg=CLIENT_PKG))
    tmp.replace(out)
    return out


def start_tunnel(port: int, timeout: float = 60.0):
    """cloudflared Quick Tunnel (ohne Konto); liefert Prozess und oeffentliche Adresse."""
    proc = subprocess.Popen(["cloudflared", "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{port}"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    pat = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
    found: list = []
    ready = threading.Event()

    def pump():
        for line in proc.stdout:  # weiterlesen, sonst blockiert cloudflared
            if not found:
                m = pat.search(line)
                if m:
                    found.append(m.group(0))
                    ready.set()

    threading.Thread(target=pump, daemon=True).start()
    if not ready.wait(timeout):
        proc.terminate()
        raise SystemExit("cloudflared hat keine Adresse geliefert")
    return proc, found[0]


def main(argv: Optional[list] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--tunnel", action="store_true", help="oeffentliche Adresse ueber cloudflared")
    ap.add_argument("--url", help="nur Zip bauen: diese Adresse eintragen und beenden")
    args = ap.parse_args(argv)

    token = load_token()
    if args.url:
        print(f"[Fernspiel] {build_client_zip(args.url, token)} gebaut")
        return

    factory = battle_agent_factory()
    factory("player_0")  # einmal laden: Fehler sofort sehen
    sessions = Sessions(factory)
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(sessions, token))
    print(f"[Fernspiel] Server laeuft lokal auf http://127.0.0.1:{args.port}", flush=True)

    helpers = []
    if args.tunnel:
        tunnel, url = start_tunnel(args.port)
        helpers.append(tunnel)
        if sys.platform == "darwin":  # Mac nicht einschlafen lassen, solange der Server laeuft
            helpers.append(subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())]))
        print(f"[Fernspiel] oeffentliche Adresse: {url}", flush=True)
        print(f"[Fernspiel] {build_client_zip(url, token)} neu gebaut -> an den Kollegen schicken", flush=True)
        print("[Fernspiel] Beenden mit Ctrl+C (danach funktioniert die Zip nicht mehr)", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        for p in helpers:
            p.terminate()
        print(f"\n[Fernspiel] beendet nach {sessions.games} Spielen", flush=True)


if __name__ == "__main__":
    main()
