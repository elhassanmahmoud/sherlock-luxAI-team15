"""Verify and reconstruct the exact evaluated native source tree from tracked Git blobs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MANIFEST = HERE / 'laufzeit.json'


def git(*args):
    return subprocess.check_output(['git','-C',str(REPO),*args])


def verify_runtime(runtime, manifest):
    for path,expected in manifest['sha256'].items():
        if sha256((runtime/path).read_bytes()).hexdigest()!=expected:
            raise ValueError(f'Unexpected native source or weight: {path}')
    actual={str(p.relative_to(runtime)) for p in (runtime/'r3_native').rglob('*.py')}
    if actual!={p for p in manifest['sha256'] if p.startswith('r3_native/')}:
        raise ValueError('Unexpected legacy policy source set')


def restore(target):
    manifest=json.loads(MANIFEST.read_bytes())
    target.mkdir(parents=True,exist_ok=False)
    for name,blob in manifest['git_blobs'].items():
        dest=target/name
        if not dest.resolve().is_relative_to(target.resolve()):
            raise ValueError(name)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(git('cat-file','blob',blob))
    subprocess.run([sys.executable,'-B','-m','scripts.r3_v4_parent_source','--repo',str(REPO)],cwd=target,check=True)
    verify_runtime(target,manifest)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('verify','restore'))
    p.add_argument('runtime',type=Path)
    args=p.parse_args()
    if args.mode=='restore':
        restore(args.runtime.resolve())
    else:
        verify_runtime(args.runtime,json.loads(MANIFEST.read_bytes()))
