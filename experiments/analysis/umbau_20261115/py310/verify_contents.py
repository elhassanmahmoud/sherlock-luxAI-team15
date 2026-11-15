"""Check both trained source checkpoints byte-for-byte per tensor against the packed and zipped hybrid."""
import argparse
import hashlib
import io
import json
from collections.abc import Mapping
from pathlib import Path
import zipfile

import torch

parser = argparse.ArgumentParser(description=__doc__)
for argument in ("v14", "student", "packed", "zip"):
    parser.add_argument("--" + argument, type=Path, required=True)
args = parser.parse_args()
v14, student, packed, zip_path = args.v14, args.student, args.packed, args.zip


def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path, expected=None):
    data = path.read_bytes()
    if expected and sha(data) != expected:
        raise ValueError(f"Wrong source: {path}")
    return torch.load(io.BytesIO(data), map_location="cpu", weights_only=False)

def identical(a, b, label, count):
    if type(a) is not type(b):
        raise ValueError(f"Type differs: {label}")
    if isinstance(a, torch.Tensor):
        if (a.shape != b.shape or a.dtype != b.dtype or not torch.equal(
                a.detach().contiguous().reshape(-1).view(torch.uint8),
                b.detach().contiguous().reshape(-1).view(torch.uint8))):
            raise ValueError(f"Tensor bytes differ: {label}")
        count[0] += 1
        count[1] += a.numel() * a.element_size()
    elif isinstance(a, Mapping):
        if set(a) != set(b):
            raise ValueError(f"Keys differ: {label}")
        for key in a:
            identical(a[key], b[key], f"{label}.{key}", count)
    elif isinstance(a, (tuple,list)):
        if len(a) != len(b):
            raise ValueError(f"Lengths differ: {label}")
        for i,(x,y) in enumerate(zip(a,b)):
            identical(x,y,f"{label}.{i}",count)
    elif a != b:
        raise ValueError(f"Value differs: {label}")

V14 = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
STUDENT = "0e8b280cb2173c4efd0d0c94e38119bf2f570dd5af06f52e1b5a7c9743ad7b7f"
ref = {"v14_ckpt":read(v14,V14), "student_ckpt": read(student,STUDENT)}
with zipfile.ZipFile(zip_path) as z:
    raw=z.read("Gruppe15/agent.pth")
    zipped=torch.load(io.BytesIO(raw),map_location="cpu",weights_only=False)
    yaml=z.read("Gruppe15/agents.yaml").decode()
    if ("IMPORT_PATH: 'Gruppe15.main.Agent_x'" not in yaml
            or any(f"LOAD_PATH_P{n}: 'Gruppe15/agent.pth'" not in yaml for n in (0,1))):
        raise ValueError(f"Wrong course declaration: {yaml}")
control = read(packed)
summaries = {}
for label, obj in (("packed",control),("zip",zipped)):
    expected = {"kind":"hybrid","mode":"mixed","combat_radius":5,
                "student_overrides":{"imit_stay_bias":1.5,"imit_unstack":True}}
    if any(obj[k] != v for k,v in expected.items()):
        raise ValueError(f"Wrong hybrid mode or overrides in {label}")
    summaries[label] = {}
    for name, reference in ref.items():
        counts=[0,0]
        identical(reference,obj[name],name,counts)
        summaries[label][name]={"tensors":counts[0],"tensor_bytes":counts[1]}
    cfg = dict(ref["v14_ckpt"]["cfg"])
    if label=="zip":
        cfg["frozen"]=True
    if obj["cfg"] != cfg:
        raise ValueError(f"Unexpected agent configuration: {label}")
print(json.dumps(dict(v14_sha256=V14,student_sha256=STUDENT,packed_sha256=sha(packed.read_bytes()),
                      published_pack_sha256="28933a3b7810037b0af37b9ccfbf261c7c9b2b1353c8e0e8ef3b25e2c77cae45",
                      zip_sha256=sha(zip_path.read_bytes()),zip_weights_sha256=sha(raw),
                      actual_contents=summaries),indent=2))
