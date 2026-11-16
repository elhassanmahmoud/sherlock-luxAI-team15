"""Das freigegebene R3-Finalpaket (agent.zip) als Spieler in Messungen laden (16.11.2026).

Moayeds R3 liegt als eigenständiges Kurspaket vor (Ordner `sherlock/` mit eigener V14-Kopie,
`experiments/releases/20261116_r3_finale/agent.zip`). Für Vergleiche mit neuen Kandidaten wird
genau dieses Paket entpackt und über seinen eigenen `sherlock.main.Agent_x` gespielt, ohne den
Code oder die Gewichte anzufassen. In `scripts.par_eval` heißt der Gegner `r3zip:PFAD`.

Pro Prozess kann nur ein Paket geladen werden, weil sein Modulname `sherlock` global ist.
"""
from __future__ import annotations

import atexit
import shutil
import sys
import tempfile
import zipfile
from hashlib import sha256
from importlib import import_module
from pathlib import Path

PREFIX = "r3zip:"
_LOADED: dict[str, tuple[Path, object]] = {}


def is_spec(name: str) -> bool:
    return isinstance(name, str) and name.startswith(PREFIX)


def zip_sha256(zip_path: str | Path) -> str:
    return sha256(Path(zip_path).read_bytes()).hexdigest()


def _module_for(zip_path: Path):
    key = str(zip_path)
    if key in _LOADED:
        return _LOADED[key]
    if _LOADED:
        raise RuntimeError("Pro Prozess kann nur ein R3-Paket geladen werden (Modul `sherlock`)")
    if "sherlock" in sys.modules:
        raise RuntimeError("Ein anderes Modul `sherlock` ist bereits geladen")
    tmp = Path(tempfile.mkdtemp(prefix="r3pkg_"))
    atexit.register(shutil.rmtree, tmp, True)
    with zipfile.ZipFile(zip_path) as z:
        for member in z.namelist():  # nur relative Pfade innerhalb des Pakets
            if member.startswith("/") or ".." in Path(member).parts:
                raise ValueError(f"Unsicherer Pfad im Paket: {member}")
        z.extractall(tmp)
    sys.path.insert(0, str(tmp))
    module = import_module("sherlock.main")
    if Path(module.__file__).resolve() != (tmp / "sherlock" / "main.py").resolve():
        raise RuntimeError("Falsches Modul `sherlock.main` geladen")
    _LOADED[key] = (tmp, module)
    return _LOADED[key]


def r3_package_agent(player: str, zip_path: str | Path):
    """Spieler aus dem Kurspaket, im Bewertungsmodus (wie im Kurs-Runner mit train=False)."""
    path = Path(zip_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    tmp, module = _module_for(path)
    agent = module.Agent_x(player, agent_path=str(tmp / "sherlock" / "weights" / "agent.pth"))
    agent.set_to_eval_mode()
    return agent
