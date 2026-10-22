"""Lokale Demo-Seite fuer Live-Spiele: Gegner und Seite waehlen, Spiel starten, Replay direkt ansehen.

    .venv/bin/python -m scripts.demo_server --open    # http://127.0.0.1:8615/
    (oder Doppelklick auf die App "Sherlock Demo" im Projektordner)

Jedes Spiel laeuft als eigener Prozess ueber `scripts.play_and_view` (unveraenderter Kurs-Runner,
train=False, keine Gewichte geschrieben). Seite und Replays werden nur lokal ausgeliefert
(127.0.0.1); der Verlauf liegt in `replays/demo_verlauf.jsonl`. Der Server endet ueber
"Demo beenden", Strg+C oder nach zwei Stunden ohne Anfrage.
"""
from __future__ import annotations

import argparse
import json
import socketserver
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
PAGE = Path(__file__).with_name("demo_page.html")
REPLAYS = ROOT / "replays"
PORT = 8615
IDLE_SECONDS = 2 * 60 * 60
GEGNER = ("solution", "default", "dqn")


def history_file() -> Path:
    return REPLAYS / "demo_verlauf.jsonl"


def play_game(gegner: str, seite: int, timeout: float = 300) -> dict:
    """Ein Spiel als eigener Prozess; liefert die JSON-Zusammenfassung von play_and_view."""
    cmd = [sys.executable, "-m", "scripts.play_and_view", "--no-open", "--json",
           "--gegner", gegner, "--seite", str(seite)]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith("{"):
            return json.loads(line)
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-8:]
    raise RuntimeError("\n".join(tail) or f"Abbruch mit Exit-Code {proc.returncode}")


def replay_file(url_path: str) -> Path | None:
    """Datei zu /replays/...html, nur innerhalb von REPLAYS."""
    if not url_path.startswith("/replays/"):
        return None
    f = (REPLAYS / unquote(url_path[len("/replays/"):])).resolve()
    if f.suffix == ".html" and f.is_file() and REPLAYS.resolve() in f.parents:
        return f
    return None


def history_entry(game: dict) -> dict:
    return {**game, "url": "/" + Path(game["html"]).as_posix()}


def append_history(entry: dict) -> None:
    REPLAYS.mkdir(exist_ok=True)
    with history_file().open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_history(limit: int = 12) -> dict:
    """Letzte Spiele (neueste zuerst, nur mit vorhandener Datei) und Bilanz von heute."""
    entries = []
    if history_file().is_file():
        for line in history_file().read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if replay_file(e.get("url", "")) is not None:
                entries.append(e)
    today = [e for e in entries if e.get("datum") == date.today().isoformat()]
    return {
        "games": entries[::-1][:limit],
        "heute": {"spiele": len(today), "siege": sum(e["ours"] > e["theirs"] for e in today)},
    }


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, player=play_game, page: Path = PAGE):
        super().__init__(address, Handler)
        self.player, self.page = player, page
        self.lock = threading.Lock()  # immer nur ein Spiel gleichzeitig
        self.last_request = time.monotonic()

    def server_bind(self) -> None:
        # wie HTTPServer.server_bind, aber ohne socket.getfqdn(): die Namensabfrage dauerte hier ~35 s
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


class Handler(BaseHTTPRequestHandler):
    server: DemoServer

    def log_message(self, fmt, *args) -> None:  # keine Zeile pro Anfrage
        pass

    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data: dict) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        self.server.last_request = time.monotonic()
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._send(200, self.server.page.read_bytes(), "text/html; charset=utf-8")
        if path == "/api/ping":
            return self._json(200, {"ok": True, "busy": self.server.lock.locked()})
        if path == "/api/history":
            return self._json(200, read_history())
        f = replay_file(path)
        if f is not None:
            return self._send(200, f.read_bytes(), "text/html; charset=utf-8")
        self._json(404, {"error": "Nicht gefunden"})

    def do_POST(self) -> None:
        self.server.last_request = time.monotonic()
        path = urlparse(self.path).path
        # Nur JSON: fremde Webseiten koennen so ohne CORS-Freigabe nichts ausloesen
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            return self._json(415, {"error": "JSON erwartet"})
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "Ungültige Anfrage"})
        if path == "/api/play":
            return self._play(data)
        if path == "/api/quit":
            self._json(200, {"ok": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        self._json(404, {"error": "Nicht gefunden"})

    def _play(self, data: dict) -> None:
        gegner, seite = data.get("gegner"), data.get("seite")
        if gegner not in GEGNER or seite not in (0, 1):
            return self._json(400, {"error": "Gegner oder Seite ungültig"})
        if not self.server.lock.acquire(blocking=False):
            return self._json(409, {"error": "Es läuft bereits ein Spiel"})
        try:
            game = self.server.player(gegner, seite)
        except Exception as e:  # Fehler an die Seite melden, Server laeuft weiter
            return self._json(500, {"error": str(e) or type(e).__name__})
        finally:
            self.server.lock.release()
        entry = history_entry(game)
        append_history(entry)
        self._json(200, entry)


def watchdog(server: DemoServer, idle: float) -> None:
    while True:
        time.sleep(30)
        if time.monotonic() - server.last_request > idle and not server.lock.locked():
            server.shutdown()
            return


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--open", action="store_true", help="Seite gleich im Browser oeffnen")
    args = ap.parse_args()
    try:
        server = DemoServer(("127.0.0.1", args.port))
    except OSError as e:
        sys.exit(f"Port {args.port} ist belegt ({e}). Läuft die Demo schon? http://127.0.0.1:{args.port}/")
    threading.Thread(target=watchdog, args=(server, IDLE_SECONDS), daemon=True).start()
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Sherlock-Demo läuft: {url} (beenden: 'Demo beenden' auf der Seite oder Strg+C)", flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
