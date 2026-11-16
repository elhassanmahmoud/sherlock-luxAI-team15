"""On-disk arrays for ordinary imitation learning. One compressed game is expanded at a time."""
from contextlib import ExitStack
from pathlib import Path

import numpy as np
import torch


def store_partition(files, folder, prepare_labels, extra_feats=None):
    """Same file and step order as concat_games; calculate the regular action/target masks per game.

    extra_feats (16.11.2026): optional function of the open archive returning float16 columns that are
    appended to the 79 unit features (e.g. the previous own move, scripts/imitate.py prev_move_columns)."""
    if not files:
        raise ValueError("Need at least one game in each data split")
    folder = Path(folder)
    folder.mkdir()
    # Raw boards and features dominate disk usage. Integer/bool columns remain compact on the CPU.
    types = dict(planes=np.int8, step=np.int64, pos=np.int8, feats=np.float16, mask=bool, act=np.int8,
                 sdx=np.int8, sdy=np.int8, rng=np.int32, sap_label=bool, admitted=bool, tgt=np.int32)
    shapes = {}
    board_count = row_count = 0
    with ExitStack() as stack:
        sinks = {k:stack.enter_context((folder/k).open("xb")) for k in types}
        for path in files:
            with np.load(path,allow_pickle=False) as z:
                board = z["planes"]
                keys = ("step","pos","feats","mask","act","sdx","sdy")
                raw = {k:z[k] for k in keys}
                if extra_feats is not None:
                    raw["feats"] = np.concatenate([raw["feats"], extra_feats(z)], axis=1).astype(np.float16)
            n = len(raw["step"])
            if (not n or not len(board) or np.any(raw["step"][1:] < raw["step"][:-1])
                    or raw["step"].min() < 0 or raw["step"].max() >= len(board)):
                raise ValueError(f"Invalid or unsorted frame indices in {path}")
            if (board.dtype != np.int8 or raw["feats"].dtype != np.float16 or raw["mask"].dtype != np.bool_):
                raise ValueError(f"Unexpected archive encoding in {path}")
            rows = {k:torch.from_numpy(v) for k,v in raw.items()}
            prepare_labels(rows, *board.shape[-2:])
            # Store original compact feature bits and coordinates. prepare_labels mutates the SAP mask,
            # and supplies the exact same target, legal-action and admission values as the ordinary trainer.
            values = dict(planes=board, **raw)
            values["step"] = raw["step"].astype(np.int64) + board_count
            for k in ("mask","rng","sap_label","admitted","tgt"):
                values[k] = rows[k].numpy()
            for k, arr in values.items():
                shape = tuple(arr.shape[1:])
                if shape != shapes.setdefault(k,shape) or (k != "planes" and len(arr) != n):
                    raise ValueError(f"Inconsistent array shape in {path}: {k}")
                arr.astype(types[k],copy=False).tofile(sinks[k])
            board_count += len(board)
            row_count += n
    def mapping(k, length):
        return np.memmap(folder/k,mode="r+",dtype=types[k],shape=(length,*shapes[k]))
    return mapping("planes",board_count), {k:mapping(k,row_count) for k in types if k != "planes"}
