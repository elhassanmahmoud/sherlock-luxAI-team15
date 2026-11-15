"""Build the fixed diagonal candidate using only the previously verified R3 package and Python source."""
import argparse
import ast
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

STANDARD_ZIP = "8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d"
DIAGONAL_SOURCE = "13758f9a8566e587322ea3f8ab12920feb34a8bd1864ee50cb35b478ce564194"


def checked_bytes(path, expected):
    data = path.read_bytes()
    if sha256(data).hexdigest() != expected:
        raise ValueError(f"Different registered input: {path}")
    return data


def course_diagonal(source):
    # Preserve each expression and the live policy classes verbatim, without the research collector imports.
    wanted = ("R3", "ACTIONS", "swap_feature", "FEATURES", "TwoViews", "digest", "DiagonalAgent")
    blocks = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        else:
            name = getattr(node, "name", None)
        if name in wanted:
            blocks[name] = ast.get_source_segment(source, node)
    imports = ("from hashlib import sha256\nfrom pathlib import Path\n"
               "from .v14.features import FEATURE_NAMES\nfrom .r3_adviser import SelectiveAdviceAgent\n")
    return "\n\n".join([imports, *(blocks[name] for name in wanted)]) + "\n"


def course_entry(source):
    # The original diagonal constructor checks the hash of a file, so give it the exact R3 bytes on disk.
    changes = (("from io import BytesIO\n", ""),
               ("from .r3_adviser import SelectiveAdviceAgent", "from .r3_diagonal import DiagonalAgent"),
               ("            actor = SelectiveAdviceAgent(", '            r3 = Path(tmp) / "r3.pth"\n'
                '            r3.write_bytes(bundle["r3"])\n            actor = DiagonalAgent('),
               ('advice_path=BytesIO(bundle["r3"])', "advice_path=r3"))
    for original, replacement in changes:
        if source.count(original) != 1:
            raise ValueError("The verified R3 course entry no longer matches")
        source = source.replace(original, replacement)
    return source


def build(base, out):
    if out.suffix.lower() != ".zip" or out.name.casefold() in {"gruppe15.zip", "agent.zip"} or out.exists():
        raise ValueError("Choose a new, separate candidate .zip path")
    source = checked_bytes(Path(__file__).with_name("r3_diagonal.py"), DIAGONAL_SOURCE).decode()
    original = checked_bytes(base, STANDARD_ZIP)
    out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=out.parent) as tmp, ZipFile(BytesIO(original)) as src:
        staged = Path(tmp) / "diagonal.zip"
        with ZipFile(staged, "x") as dst:
            for name in sorted([*src.namelist(), "sherlock/r3_diagonal.py"]):
                if name == "sherlock/r3_diagonal.py":
                    data = course_diagonal(source).encode()
                elif name == "sherlock/main.py":
                    data = course_entry(src.read(name).decode()).encode()
                else:
                    data = src.read(name)
                info = ZipInfo(name)
                info.external_attr = 0o100644 << 16
                dst.writestr(info, data, compress_type=ZIP_DEFLATED)
        os.link(staged, out)
    return sha256(out.read_bytes()).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True, help="Verified single-view R3 course ZIP")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.base, args.out), args.out)
