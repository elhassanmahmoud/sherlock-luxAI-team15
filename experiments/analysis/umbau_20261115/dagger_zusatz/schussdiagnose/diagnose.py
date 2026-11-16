"""Run the original archived v4 action decoder on the selected DAgger inputs, one board at a time."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import sys
from unittest.mock import patch

for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[name] = "1"

HERE = Path(__file__).resolve().parent
INDEX = "fd46ae863eb6a99a2876480f13eb0ec61fcdcb52da78711f82b93f2d2648e94e"
FREEZE = "adeb0c096fc025f8ced1abbbff55b2f2d651147b48d4161f8708de07b6055521"
SAMPLE = "cb7fee3485c1276b24563b5503f92cf54f2e32cb63d34736ee660d3d955030a9"
PROTOCOL = "bdbc249aeb9831b8f83eaf2144da3f361ac983e20d6cd16f46b955ec2bd34290"
WEIGHTS = "experiments/candidates/umbau_20261115/student_v4.pth"

def insist(test, detail):
    if not test:
        raise ValueError(detail)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def checked(path, pin):
    insist(sha(path) == pin, f"Hash mismatch {path}")
    return json.loads(path.read_bytes())

def memory_mib():
    n = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return n / (1024**2 if sys.platform == "darwin" else 1024)

def memory_check():
    insist(memory_mib() < 800, "Stopping at conservative RSS limit")

def main(args):
    freeze = checked(args.source/"freeze.json", FREEZE)
    idx = checked(args.data/"index-400.json", INDEX)
    protocol = checked(args.data/"protocol.json", PROTOCOL)
    sample = checked(HERE/"sample.json", SAMPLE)["keys"]
    weights = args.source/WEIGHTS
    insist(sha(weights) == freeze["files"][WEIGHTS] == protocol["model"], "Wrong checkpoint")
    insist(protocol["freeze_sha256"] == FREEZE and idx["protocol_sha256"] == PROTOCOL, "Wrong source chain")
    registry = {(r["seed"],r["side"],r["opponent"]):r for r in idx["files"]}
    roster = [tuple(r) for r in protocol["roster"]]
    insist(len(roster)==len(registry)==400 and set(roster)==set(registry), "Incomplete index")
    selected = sorted(k for op in ("v14","kaggle3","solution92") for k in sorted(k for k in registry if k[2]==op)[:5])
    insist(selected == [(r["seed"],r["side"],r["opponent"]) for r in sample], "Selection has changed")
    sources = {k:v for k,v in freeze["files"].items() if k.endswith(".py") and k.startswith(("agents/sherlock/","scripts/"))}
    for k,h in sources.items():
        insist(sha(args.source/k)==h, f"Frozen source differs: {k}")
    sys.path.insert(0, str(args.source))
    import numpy as np
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from agents.sherlock import imitation_agent
    from agents.sherlock.features import FEATURE_NAMES
    from agents.sherlock.imitation_net import masked_sap_logits
    from scripts.imitate import PLANE_SCALE, prepare_labels
    from scripts.optional_v4_dagger import check_npz, filename
    from scripts.par_eval import build_cfg

    actor = imitation_agent.ImitationAgent("player_0", agent_path=str(weights), train=False,
                                 cfg=build_cfg(str(weights),protocol["overrides"]))
    actor.set_to_eval_mode()
    flags = {k:getattr(actor.cfg,k) for k in ("imit_stay_bias","imit_unstack","imit_sap_bias","imit_cover","end_sap","focus_sap")}
    insist(flags==dict(imit_stay_bias=1.5,imit_unstack=True,imit_sap_bias=0.0,imit_cover=0.0,end_sap=0,focus_sap=False), "Different actor settings")
    insist(actor.has_sap_head and actor.sap_own_tile and not actor.extra_nets and not actor.sample and not actor.training, "Wrong student decoder")
    insist(PLANE_SCALE==127, "Wrong plane scale")
    owner_col = FEATURE_NAMES.index("redundant_here")
    stack_col = FEATURE_NAMES.index("allies_here")
    # Capture the existing forward's target map. The extra masked argmax scores the target head
    # even on a teacher shot where the action head would not fire; no second model forward.
    lastmap = []
    def capture(module, inputs, output):
        lastmap[:] = [output.detach()]
    handle = actor.net.sap.register_forward_hook(capture)
    by_opp = defaultdict(Counter)
    by_phase = defaultdict(lambda:defaultdict(Counter))
    cases = []

    with torch.inference_mode(), patch.object(imitation_agent,"featurize",lambda _actor, archive_inputs: archive_inputs):
        for ref in sample:
            key = (ref["seed"],ref["side"],ref["opponent"])
            name = filename(key)
            path = args.data/"records"/str(key[0])/name
            insist(ref["sha256"]==sha(path), "Individual game digest mismatch")
            receipt = check_npz(path,key,PROTOCOL)
            insist(receipt==registry[key]==json.loads((path.parent/"receipt.json").read_bytes()), "Receipt mismatch")
            with np.load(path,allow_pickle=False) as z:
                archive = {k:z[k] for k in z.files if k!="meta"}
                meta = json.loads(z["meta"].item())
            data = {k:torch.as_tensor(archive[k].copy()) for k in ("pos","act","sdx","sdy","mask","feats")}
            prepare_labels(data,24,24)
            actor.new_game(key[1])
            insist(actor.belief.mirrored == (key[1]=="player_1"), "World orientation mismatch")
            frames = np.flatnonzero(np.asarray(meta["live_masks"]))
            frame_index = {int(step):i for i,step in enumerate(frames)}
            bounds = np.searchsorted(archive["step"],np.arange(len(frames)+1))
            digest = hashlib.sha256()
            teacher_digest = hashlib.sha256()
            phases = defaultdict(Counter)
            confusion = np.zeros((6,6),dtype=np.int64)
            for step in range(303):
                phase = phases[str(step//101+1)]
                b = frame_index.get(step)
                if b is None:
                    world = actor.act(step,None)
                else:
                    sl = slice(bounds[b],bounds[b+1])
                    ids = archive["uid"][sl].astype(int)
                    pos = archive["pos"][sl].astype(np.int64)
                    feats = archive["feats"][sl].astype(np.float32)
                    # Owner feature denotes the original slot. Missing negative-energy IDs
                    # are not fabricated. Their possible influence is counted separately.
                    owners = {tuple(p):int(uid) for uid,p,f in zip(ids,pos,feats) if f[owner_col]==0}
                    ally_count = Counter(map(tuple,pos))
                    missing_peer = np.array([ally_count[tuple(p)] < round(4*f[stack_col]) or tuple(p) not in owners for p,f in zip(pos,feats)])
                    phase["rows_with_evidence_of_filtered_stack_peer"] += int(missing_peer.sum())
                    energy = np.zeros(16)
                    energy[ids] = np.rint(feats[:,2]*400)
                    costs = np.unique(np.rint(feats[:,7]*50))
                    ranges = np.unique(np.rint(feats[:,8]*7))
                    insist(len(costs)==len(ranges)==1, "Within-frame parameters disagree")
                    ctx = dict(ally_ene=energy,sap_cost=int(costs[0]),sap_range=int(ranges[0]),
                               first_on_tile=owners,H=24,match_step=step%101,max_match_steps=100)
                    planes = archive["planes"][b].astype(np.float32)/PLANE_SCALE
                    fz = (ctx,ids,feats,archive["mask"][sl],{},planes,pos)
                    world = actor.act(step,fz)
                    pred = np.array([imitation_agent.canonical_action(world[uid],actor.belief.mirrored) for uid in ids])
                    lbl = np.column_stack([archive[k][sl] for k in ("act","sdx","sdy")])
                    teacher_digest.update(np.ascontiguousarray(lbl,dtype="<i2").tobytes())
                    valid = data["admitted"][sl].numpy()
                    fired = pred[:,0]==5
                    called = data["sap_label"][sl].numpy()
                    exact = np.all(pred==lbl,axis=1)
                    np.add.at(confusion,(lbl[valid,0],pred[valid,0]),1)
                    phase.update({"rows":len(ids),"admitted":int(valid.sum()),"correct_class":int((valid & (pred[:,0]==lbl[:,0])).sum()),
                                  "exact_order":int((valid & exact).sum()),"teacher_sap":int(called.sum()),
                                  "sap_to_sap":int((called & fired).sum()),"sap_exact_target_and_fire":int((called & exact).sum()),
                                  "sap_to_stay":int((called & (pred[:,0]==0)).sum()),
                                  "sap_to_move":int((called & (pred[:,0]>=1) & (pred[:,0]<=4)).sum()),
                                  "false_sap_on_teacher_non_sap":int((valid & ~called & fired).sum())})
                    if called.any():
                        cp = torch.from_numpy(pos[called])
                        sm = torch.log_softmax(lastmap[0].flatten(),0).reshape(1,24,24)
                        scores = masked_sap_logits(sm,torch.zeros(len(cp),dtype=torch.long),cp,data["rng"][sl][called])
                        target = scores.argmax(1).numpy()
                        head_ok = target==data["tgt"][sl].numpy()[called]
                        phase["target_head_exact_on_teacher_sap"] += int(head_ok.sum())
                        insist(int((head_ok & fired[called]).sum())==int((exact & called).sum()), "SAP-target decoder divergence")
                digest.update(np.ascontiguousarray(world,dtype="<i2").tobytes())
                memory_check()
            counts = Counter()
            for m,c in phases.items():
                by_phase[key[2]][m].update(c)
                counts.update(c)
            insist(counts["rows"]==receipt["rows"] and counts["admitted"]==receipt["admitted"] and counts["teacher_sap"]==receipt["legal_sap"]==receipt["sap"], "Changed reference population")
            insist(teacher_digest.hexdigest()==meta["canonical_teacher_sha256"], "Teacher stream mismatch")
            by_opp[key[2]].update(counts)
            cases.append(dict(**ref,counts=counts,matches=phases,confusion_teacher_by_predicted=confusion.tolist(),
                              canonical_teacher_sha256=teacher_digest.hexdigest(),recorded_world_sha256=meta["played_sha256"],
                              reconstructed_world_sha256=digest.hexdigest(),whole_stream_equal=digest.hexdigest()==meta["played_sha256"]))
            print(f"{key[0]} {key[2]} {counts['teacher_sap']} legal teacher shots",flush=True)
    handle.remove()
    imported = {}
    for m in tuple(sys.modules.values()):
        f = getattr(m,"__file__",None)
        if f and Path(f).resolve().is_relative_to(args.source):
            path = Path(f).resolve().relative_to(args.source).as_posix()
            h=sha(args.source/path)
            insist(h==freeze["files"].get(path), f"Unbound imported source {path}")
            imported[path]=h
    result=dict(sample_sha256=SAMPLE,index_sha256=INDEX,protocol_sha256=PROTOCOL,freeze_sha256=FREEZE,
                model_sha256=sha(weights),source_commit=freeze["source"],auditor_sha256=sha(Path(__file__)),
                imported_source_sha256=imported,actor_flags=flags,torch_version=torch.__version__,
                numpy_version=np.__version__,python_version=platform.python_version(),
                rss_high_water_mib=round(memory_mib(),1),torch_threads=[torch.get_num_threads(),torch.get_num_interop_threads()],
                opponents=by_opp,by_opponent_and_match=by_phase,cases=cases)
    (args.out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(f"Peak RSS {memory_mib():.1f} MiB",flush=True)

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("source","data","out"):
        parser.add_argument("--"+name,required=True,type=lambda p: Path(p).resolve())
    main(parser.parse_args())
