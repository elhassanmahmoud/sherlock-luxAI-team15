"""Check the actual simulator against archived decisions and the parallel game claim independently."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import fcntl

from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.abschlusspruefung import vergleich as v
from scripts.experiment import limit_threads


def main():
    limit_threads()
    with TemporaryDirectory() as d:
        p=Path(d)/"game.json"
        with p.with_suffix(".lock").open("ab") as a:
            fcntl.flock(a,fcntl.LOCK_EX)
            v.play_if_available(p,"sample",lambda:1/0)
            assert not p.exists()
        v.play_if_available(p,"sample",lambda:{"source":"sample","value":1})
        v.play_if_available(p,"sample",lambda:1/0)
        assert json.loads(p.read_bytes())=={"source":"sample","value":1}
    original=json.loads((v.HERE/"vergleichstechnik_v2.json").read_text())["development"]
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for known in original:
            actual=v.run(env,tuple(known['key']),"known")
            assert actual["digest"]==known["hash"] and actual["matches"]==known["matches"]
    finally:env.close()
    v.write_once(v.HERE/"vergleichstechnik_parallel.json",dict(program=v.sha(v.HERE/"vergleich.py"),known_cases=original,concurrent_claim=True))


if __name__=="__main__":main()
