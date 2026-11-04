"""Archive completed immutable evidence; do not copy replay buffers or init models."""
from pathlib import Path
import datetime,gzip,hashlib,json,shutil
root=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
tmp=Path('/tmp/sherlock-a2-anchor-20261104');out=root/'experiments/analysis/a2_anchor_20261104'
assert json.loads((tmp/'learning_completion_audit.json').read_text())['status']=='passed'
assert json.loads((out/'diagnostic/state.json').read_text())['status']=='complete'
entries=[]
def digest(b):return hashlib.sha256(b).hexdigest()
def copy(p,dest,compress=False):
 assert p.is_file(),p
 assert not dest.exists(),dest
 dest.parent.mkdir(parents=True,exist_ok=True)
 raw=p.read_bytes();encoded=gzip.compress(raw,compresslevel=6,mtime=0) if compress else raw
 dest.write_bytes(encoded)
 assert (gzip.decompress(dest.read_bytes()) if compress else dest.read_bytes())==raw
 entries.append(dict(source=str(p),archive=str(dest.relative_to(root)),source_sha256=digest(raw),archive_sha256=digest(encoded),compression='gzip' if compress else None))
for p in sorted((root/'experiments/runs/20261104_a2_anchor').rglob('*')):
 if not p.is_file():continue
 if p.suffix not in ('.json','.jsonl','.csv','.log','.txt','.u32'):continue
 rel=p.relative_to(root/'experiments/runs/20261104_a2_anchor');dest=out/'training'/rel
 compress=p.suffix in ('.jsonl','.u32')
 if compress:dest=dest.with_name(dest.name+'.gz')
 copy(p,dest,compress)
for name in ['training_admission.json','learning_startup_audit.json','learning_completion_audit.json','learning_completion_auditor.py','learning_completion_audit.md','learning_completion_audit.failed_attempt1.json','learning_completion_auditor.failed_attempt1.py','prepare_diagnostic.py','preparation_report.md','diagnostic_protocol.json','diagnostic_runtime_admission.json','candidate_provenance.json','role_manifest.json','planned_comparison.json','panel_seeds.json','direct_seeds.json','run_diagnostic.py','run_guarded.py','audit_results.py','diagnostic_review.json','diagnostic_review.md','reviewer_notes.md','archive_completed.py','admit_seed26.py','crosscheck_diagnostic.py','root_crosscheck.json','retention_after_independent.json','retention_independent_audit.py','retention_after_independent_audit.py','seed26_admission.json','seed25_control_guard.json','seed25_control_guard.log','seed25_anchor_guard.json','seed25_anchor_guard.log','seed26_control_guard.json','seed26_control_guard.log','seed26_anchor_guard.json','seed26_anchor_guard.log','full_tests_guard.json','full_tests_guard.log','full_tests_fixed_guard.json','full_tests_fixed_guard.log']:
 p=tmp/name
 if p.exists():copy(p,out/'completion'/name)
for p in sorted((tmp/'retention_after').rglob('*')):
 if p.is_file():copy(p,out/'retention_after'/p.relative_to(tmp/'retention_after'))
sdd=root/'.superpowers/sdd/2026-11-04-a2-teacher-anchor'
for p in sorted(sdd.rglob('*')):
 if p.is_file():copy(p,out/'review'/p.relative_to(sdd))
# Preserve exact CSV and JSON bytes despite the user's core.autocrlf=input.
(out/'.gitattributes').write_text('* -text\n')
(out/'completion_archive_manifest.json').write_text(json.dumps(dict(status='copied_and_byte_verified',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=entries,local_replay_buffers_excluded=True),indent=2)+'\n')
print(json.dumps(dict(files=len(entries),original_bytes=sum(Path(r['source']).stat().st_size for r in entries),archive_bytes=sum((root/r['archive']).stat().st_size for r in entries))))
