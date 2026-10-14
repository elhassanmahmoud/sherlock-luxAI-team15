"""Reject output paths that would write into the released weights."""
from pathlib import Path


def checked_output(path: Path, protected_dir: Path) -> Path:
    """Check both the written path and its filesystem target, including aliases."""
    path = Path(path).expanduser().absolute()
    protected_dir = Path(protected_dir).absolute()
    resolved = path.resolve()
    if (path.is_relative_to(protected_dir)
            or resolved.is_relative_to(protected_dir.resolve())):
        raise ValueError(f"Abgabe-Gewichte sind geschuetzt; anderes Ausgabeziel waehlen: {path}")
    # resolve() preserves case on case-insensitive filesystems (e.g. macOS).
    if protected_dir.exists():
        for ancestor in (resolved, *resolved.parents):
            if ancestor.exists() and ancestor.samefile(protected_dir):
                raise ValueError(f"Ausgabe liegt im geschuetzten Abgabe-Ordner: {path}")
    if path.is_symlink():
        raise ValueError(f"Ausgabeziel darf kein symbolischer Link sein: {path}")
    if path.is_file():
        for weight in protected_dir.rglob("*"):
            if weight.is_file() and path.samefile(weight):
                raise ValueError(f"Ausgabeziel verweist auf geschuetzte Abgabe-Gewichte: {path}")
    return resolved
