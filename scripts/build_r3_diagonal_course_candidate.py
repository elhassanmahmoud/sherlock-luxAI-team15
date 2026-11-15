"""Build a separate course candidate from the verified R3 package and its fixed adviser source."""
import argparse
import ast
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

STANDARD_ZIP = "8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d"
DIAGONAL_ZIP = "feaf20aa7058ad856634cd8a5a2daf56bfc6da4f6be296cff6d98fc55eefac25"
AFTER_LOSS_SOURCE = "734108bcbb2caac1c8b545e4b0690436afaf8f99537ea3732454f3acd2d0132f"
DIAGONAL_SOURCE = "13758f9a8566e587322ea3f8ab12920feb34a8bd1864ee50cb35b478ce564194"
TURN_SOURCE = "1c300c6ad4cf2f92107c804c29e20414d86c5a2d3faa66ae5feb8100450e6e7b"


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


def course_entry(source, module="r3_diagonal", actor="DiagonalAgent"):
    # Both research constructors check a file hash. Give them the original R3 bytes on disk.
    changes = (("from io import BytesIO\n", ""),
               ("from .r3_adviser import SelectiveAdviceAgent", f"from .{module} import {actor}"),
               ("            actor = SelectiveAdviceAgent(", '            r3 = Path(tmp) / "r3.pth"\n'
                f'            r3.write_bytes(bundle["r3"])\n            actor = {actor}('),
               ('advice_path=BytesIO(bundle["r3"])', "advice_path=r3"))
    for original, replacement in changes:
        if source.count(original) != 1:
            raise ValueError("The verified R3 course entry no longer matches")
        source = source.replace(original, replacement)
    return source


def build(base, out, *, after_loss=False, turn_advice=False):
    if out.suffix.lower() != ".zip" or out.name.casefold() in {"gruppe15.zip", "agent.zip"} or out.exists():
        raise ValueError("Choose a new, separate candidate .zip path")
    if after_loss and turn_advice:
        raise ValueError("Select exactly one candidate")
    if (after_loss or turn_advice) and not any(word in out.stem.casefold() for word in ("kandidat", "candidate")):
        raise ValueError("Name the separate candidate explicitly")
    module, actor = "r3_diagonal", "DiagonalAgent"
    if after_loss:
        source = checked_bytes(Path(__file__).with_name("r3_diag_after_loss.py"), AFTER_LOSS_SOURCE).decode()
        policy = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef) and node.name == "AfterLossAgent")
        addition = ast.get_source_segment(source, policy)
    elif turn_advice:
        source = checked_bytes(Path(__file__).with_name("r3_turn_advice.py"), TURN_SOURCE).decode()
        module, actor = "r3_turn_advice", "TurnAdviceAgent"
        # All non-import lines are the actual research source, including legality, feedback and counters.
        packed_adviser = (source.replace("from agents.sherlock", "from .v14")
                          .replace("from scripts.combat_teacher_counterfactual", "from .orders")
                          .replace("from scripts.selective_advice_agent", "from .r3_adviser"))
    else:
        source = checked_bytes(Path(__file__).with_name("r3_diagonal.py"), DIAGONAL_SOURCE).decode()
        packed_adviser = course_diagonal(source)
    module_path = f"sherlock/{module}.py"
    original = checked_bytes(base, DIAGONAL_ZIP if after_loss else STANDARD_ZIP)
    out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=out.parent) as tmp, ZipFile(BytesIO(original)) as src:
        staged = Path(tmp) / "diagonal.zip"
        with ZipFile(staged, "x") as dst:
            for name in sorted(set(src.namelist()) | {module_path}):
                if name == module_path:
                    if after_loss:
                        data = src.read(name) + ("\n\n" + addition + "\n").encode()
                    else:
                        data = packed_adviser.encode()
                elif name == "sherlock/main.py":
                    if after_loss:
                        entry = src.read(name)
                        if entry.count(b"DiagonalAgent") != 2:
                            raise ValueError("Unexpected verified two-view import or constructor")
                        data = entry.replace(b"DiagonalAgent", b"AfterLossAgent")
                    else:
                        data = course_entry(src.read(name).decode(), module, actor).encode()
                else:
                    data = src.read(name)
                info = ZipInfo(name)
                info.external_attr = 0o100644 << 16
                dst.writestr(info, data, compress_type=ZIP_DEFLATED)
        os.link(staged, out)
    return sha256(out.read_bytes()).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--after-loss", action="store_true", help="Use the verified diagonal ZIP as input")
    modes.add_argument("--turn-advice", action="store_true", help="Use single-view R3 for extra changes of direction")
    parser.add_argument("--base", type=Path, required=True, help="Verified R3 course ZIP, or the diagonal ZIP with --after-loss")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.base, args.out, after_loss=args.after_loss, turn_advice=args.turn_advice), args.out)
