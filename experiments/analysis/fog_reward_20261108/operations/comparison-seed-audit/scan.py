#!/usr/bin/env python3
"""Read-only local seed audit. Writes reports only to --out (default /tmp).
No repository imports, model loading, games, tests, or repository mutations.
CSV and JSONL records are parsed, including gzip. Exact stored bytes deduplicate.
All JSON is parsed for seed identifiers, intervals, and target-number mentions.
"""
import argparse, collections, csv, datetime, gzip, hashlib, io, json, os, re, subprocess, time
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--out',default='/tmp/sherlock-fog-comparison-seed-audit');args=parser.parse_args()
OUT=Path(args.out);OUT.mkdir(parents=True,exist_ok=True)
T=time.monotonic();NOW=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
RANGES={'fog_selection':[7700000,7700019], 'fog_direct_selection':[7700100,7700119], 'fog_confirmation':[7701000,7701039], 'fog_direct_confirmation':[7701100,7701139]}
WT=subprocess.check_output(['git','-C','/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15','worktree','list','--porcelain'],text=True)
ROOTS=[x[9:] for x in WT.splitlines() if x.startswith('worktree ')]
HEADS={r:subprocess.check_output(['git','-C',r,'rev-parse','HEAD'],text=True).strip() for r in ROOTS}
SKIP={'.git','.venv','venv','node_modules','__pycache__'};EXTS=['.csv.gz','.jsonl.gz','.json.gz','.csv','.jsonl','.json']
counts=collections.Counter();errors=[];mutations=[];seen={};files=[];gaps=[];invalid=[];actual_hits=[];json_hits=[];interval_hits=[];json_strings=[];seed_schema=collections.Counter();observed=set();interval_count=0;intervals=[];named_json=[]

def stat(p):
 s=os.stat(p);return {'size':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns,'inode':s.st_ino,'device':s.st_dev}
def inventory():
 out={}
 for root in ROOTS:
  for b,ds,fs in os.walk(root,followlinks=False):
   ds[:]=sorted(d for d in ds if d not in SKIP)
   if not set(os.path.relpath(b,root).split(os.sep)) & {'experiments','logs','replays'}:continue
   for f in sorted(fs):
    ext=next((x for x in EXTS if f.lower().endswith(x)),None)
    if ext:
     p=os.path.join(b,f)
     try:out[p]={'ext':ext,'stat':stat(p),'symlink':os.path.islink(p)}
     except Exception as e:errors.append({'path':p,'stage':'inventory','error':repr(e)})
 return out

def num(v):
 if isinstance(v,bool):return None
 if isinstance(v,int):return v
 if isinstance(v,float):return int(v) if v.is_integer() else None
 if isinstance(v,str) and re.fullmatch(r'[+-]?\d+(?:\.0+)?',v.strip()):return int(v.strip().split('.')[0])
 return None

def targets(n):return [k for k,(lo,hi) in RANGES.items() if lo<=n<=hi]
def overlap(a,b):return {k:[max(a,lo),min(b,hi)] for k,(lo,hi) in RANGES.items() if a<=hi and lo<=b}
def seedkey(k):return 'seed' in str(k).lower() and '/' not in str(k)
def seed_identity(k):
 k=str(k).lower();return seedkey(k) and not any(t in k for t in ['count','columns','fields','rows','unique','invalid','file','sha','audit','collision','bootstrap','random','run_seed','min_seed','max_seed','first_seed','last_seed','range','interval','start','end','stop','limit','block'])

def add_seed(v,p,loc,kind,record):
 vals=v if isinstance(v,list) else [v]
 for j,val in enumerate(vals):
  n=num(val);where=loc+(f'[{j}]' if isinstance(v,list) else '')
  if n is None:
   if val is not None and val!='':invalid.append({'path':p,'record':record,'field':where,'value':repr(val)[:160],'kind':kind})
   else:counts[kind+'_blank_seed_values']+=1
  else:
   counts[kind+'_seed_values']+=1
   if kind in {'csv','jsonl'}:observed.add(n)
   hit=targets(n)
   if hit:(actual_hits if kind in {'csv','jsonl'} else json_hits).append({'path':p,'record':record,'field':where,'seed':n,'ranges':hit,'kind':kind})

def inspect_json(o,p,loc='$',kind='json',record=None):
 global interval_count
 if isinstance(o,dict):
  low={str(k).lower():v for k,v in o.items()}
  context={k:v for k,v in low.items() if k in {'status','started','finished','started_at','finished_at','complete','phase','name','role','kind'} and not isinstance(v,(dict,list))}
  def interval(a,b,why,at):
   global interval_count
   if a is None or b is None or b<a:return
   interval_count+=1
   intervals.append({'path':p,'field':at,'start':a,'end_inclusive':b,'basis':why,'context':context})
   hit=overlap(a,b)
   if hit:interval_hits.append({'path':p,'field':at,'start':a,'end_inclusive':b,'overlap':hit,'basis':why,'context':context})
  for sk in ['first_seed','start_seed','seed_start','map_seed_start','train_seed_start','seed_base']:
   a=num(low.get(sk))
   if a is not None:
    for nk in ['n_maps','maps','num_maps','map_count','count','train_games','games']:
     n=num(low.get(nk))
     if n is not None and n>0:interval(a,a+n-1,sk+' + '+nk,loc+'.'+sk);break
    for ek in ['last_seed','end_seed','seed_end','seed_stop','stop_seed']:
     b=num(low.get(ek))
     if b is not None:interval(a,b,'explicit seed endpoints (conservative inclusive)',loc+'.'+sk)
  if num(low.get('start')) is not None:
   if num(low.get('stop_exclusive')) is not None:interval(num(low['start']),num(low['stop_exclusive'])-1,'start / stop_exclusive',loc)
   if num(low.get('end')) is not None and ('seed' in loc.lower() or 'range' in loc.lower()):interval(num(low['start']),num(low['end']),'seed-context start/end',loc)
  for k,v in o.items():
   kl=str(k).lower();at=loc+'.'+str(k)
   if seedkey(k):
    seed_schema[(kind,kl,type(v).__name__)]+=1
    if kind=='jsonl' and (not isinstance(v,dict)) and not any(s in kl for s in ['sha','file','columns','count']):add_seed(v,p,at,kind,record)
    elif kind=='json' and seed_identity(k) and not isinstance(v,dict):add_seed(v,p,at,kind,record)
   inspect_json(v,p,at,kind,record)
 elif isinstance(o,list):
  if kind=='json' and len(o)==2 and all(num(x) is not None for x in o) and any(t in loc.lower() for t in ['seed','range','interval','reserved','block']):
   a,b=map(num,o)
   if a<=b:
    interval_count+=1
    item={'path':p,'field':loc,'start':a,'end_inclusive':b,'basis':'two-number range candidate (conservative inclusive)','context':{}}
    intervals.append(item)
    if overlap(a,b):interval_hits.append({**item,'overlap':overlap(a,b)})
  for i,v in enumerate(o):inspect_json(v,p,loc+f'[{i}]',kind,record)
 elif kind=='json':
  n=num(o)
  if n is not None and targets(n):json_hits.append({'path':p,'record':record,'field':loc,'seed':n,'ranges':targets(n),'kind':'json_numeric_mention'})
  if isinstance(o,str):
   hits=sorted({int(s) for s in re.findall(r'(?<!\d)(?:770\d{4})(?!\d)',o) if targets(int(s))})
   if hits:
    classification='non_seed_hash_substring' if re.fullmatch(r'[0-9a-fA-F]{32,128}',o) else 'non_seed_timestamp_fraction' if re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+(?:Z|[+-]\d\d:\d\d)',o) else 'requires_review'
    json_strings.append({'path':p,'field':loc,'seeds':hits,'text':o[:1000],'classification':classification})

started=NOW();initial=inventory();print('inventory',len(initial),'paths',flush=True)
for idx,(p,meta) in enumerate(sorted(initial.items())):
 ext=meta['ext'];kind='csv' if '.csv' in ext else 'jsonl' if '.jsonl' in ext else 'json'
 counts[ext+'_paths']+=1;counts['stored_bytes']+=meta['stat']['size']
 entry={'path':p,'kind':kind,**meta};files.append(entry)
 try:
  raw=Path(p).read_bytes();digest=hashlib.sha256(raw).hexdigest();entry['sha256']=digest
  if stat(p)!=meta['stat']:mutations.append({'path':p,'stage':'after_read'})
  key=(kind,digest)
  if key in seen:
   counts[kind+'_exact_byte_duplicates']+=1;entry['duplicate_of']=seen[key];continue
  seen[key]=p;counts[kind+'_unique_scanned']+=1
  data=gzip.decompress(raw) if ext.endswith('.gz') else raw
  text=data.decode('utf-8-sig');entry['decoded_bytes']=len(data)
  if kind=='csv':
   reader=csv.reader(io.StringIO(text,newline=''));header=next(reader,[]);seedcols=[(i,k) for i,k in enumerate(header) if seedkey(k)];entry['header']=header;entry['seed_columns']=[k for _,k in seedcols];rows=0;seedrows=0
   for line,row in enumerate(reader,2):
    rows+=1
    if seedcols:seedrows+=1
    for i,k in seedcols:
     if i>=len(row):invalid.append({'path':p,'record':line,'field':k,'error':'short row missing seed column'})
     else:add_seed(row[i],p,k,kind,line)
   counts['csv_rows']+=rows;counts['csv_rows_with_seed_column']+=seedrows;entry['rows']=rows
   if not seedcols:gaps.append({'path':p,'kind':kind,'reason':'missing_seed_column','rows':rows,'header':header})
  elif kind=='jsonl':
   lines=0;seedrecords=0
   for line,s in enumerate(text.splitlines(),1):
    if not s.strip():continue
    lines+=1;before=counts['jsonl_seed_values']
    try:inspect_json(json.loads(s),p,kind=kind,record=line)
    except Exception as e:errors.append({'path':p,'stage':'jsonl_record','record':line,'error':repr(e)})
    if counts['jsonl_seed_values']>before:seedrecords+=1
   entry['records']=lines;entry['records_with_numeric_seed']=seedrecords;counts['jsonl_records']+=lines;counts['jsonl_records_without_numeric_seed']+=lines-seedrecords
   if seedrecords==0:gaps.append({'path':p,'kind':kind,'reason':'no_numeric_seed_fields','records':lines})
  else:
   obj=json.loads(text);inspect_json(obj,p,kind=kind)
   if isinstance(obj,dict) and any(t in Path(p).name.lower() for t in ['manifest','state','plan','freeze','reservation']):named_json.append({'path':p,'sha256':digest,'top_level_keys':list(obj),'status_fields':{k:v for k,v in obj.items() if k in {'status','started','finished','started_at','finished_at','complete','phase','name','role','kind','created_at','predeclared_at'} and not isinstance(v,(dict,list))}})
  if idx%1000==0:print('processed',idx,'/',len(initial),flush=True)
 except Exception as e:errors.append({'path':p,'stage':'read_or_parse','error':repr(e)})
final=inventory()
for p,m in initial.items():
 if p not in final:mutations.append({'path':p,'stage':'removed_during_scan'})
 elif m['stat']!=final[p]['stat']:mutations.append({'path':p,'stage':'changed_during_scan','before':m['stat'],'after':final[p]['stat']})
for p in set(final)-set(initial):mutations.append({'path':p,'stage':'added_during_scan'})
heads_after={r:subprocess.check_output(['git','-C',r,'rev-parse','HEAD'],text=True).strip() for r in ROOTS}
for r in ROOTS:
 if HEADS[r]!=heads_after[r]:mutations.append({'path':r,'stage':'HEAD_changed','before':HEADS[r],'after':heads_after[r]})
counts['unique_observed_csv_jsonl_seed_values']=len(observed);counts['json_interval_candidates_examined']=interval_count
counts['seedless_unique_csv_files']=sum(g['kind']=='csv' for g in gaps);counts['seedless_unique_jsonl_files']=sum(g['kind']=='jsonl' for g in gaps)
counts['invalid_seed_values']=len(invalid)
verdict='NO_OBSERVED_CONSUMPTION_OR_JSON_OVERLAP_WITH_REPORTED_SCHEMA_LIMITS' if not actual_hits+json_hits+interval_hits+[x for x in json_strings if x['classification']=='requires_review']+errors+mutations else 'REVIEW_REQUIRED'
report={'schema':'local_seed_freshness_v1','verdict':verdict,'started_utc':started,'finished_utc':NOW(),'duration_seconds':time.monotonic()-T,'ranges_inclusive':RANGES,'worktrees':ROOTS,'heads_before':HEADS,'heads_after':heads_after,'counts':dict(counts),'consumption_overlaps':actual_hits,'json_seed_or_numeric_mentions':json_hits,'json_interval_overlaps':interval_hits,'json_string_mentions':json_strings,'json_interval_candidates':intervals,'manifest_state_plan_freeze_reservation_records':named_json,'schema_gaps':gaps,'invalid_seed_values':invalid,'seed_field_schema':[{'kind':k[0],'field':k[1],'value_type':k[2],'count':v} for k,v in sorted(seed_schema.items())],'errors':errors,'mutations':mutations,'files':files,'limits':['Local registered worktrees only; undocumented trials or other machines are unknown.','Files without seed columns/fields do not prove non-consumption; reported explicitly.','JSON range candidates are conservative inclusive endpoints unless stop_exclusive is explicit; all candidates require adjudication before a freshness claim.','JSON seed metadata and numeric/string mentions are distinguished from actual CSV/JSONL consumption.','Only experiments/logs/replays directory trees scanned; .git/.venv/venv/node_modules/__pycache__ skipped; directory symlinks not followed.','Stored file bytes deduplicated by SHA-256 within format; compressed/uncompressed representations count separately if bytes differ.','No model, game, test, source changes, or repository writes made.']}
(OUT/'seed_freshness.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'short.md').write_text(f"# Local seed freshness audit\n\nVerdict: **{verdict}**.\n\nScanned all {len(ROOTS)} registered worktrees under experiments/logs/replays; SHA-256 deduplicated exact stored file bytes.\n\nFog comparison ranges (inclusive): selection 7700000–7700019; direct selection 7700100–7700119; confirmation 7701000–7701039; direct confirmation 7701100–7701139.\n\n- {counts['csv_unique_scanned']} unique CSV/CSV.gz files, {counts['csv_seed_values']:,} numeric seed values.\n- {counts['jsonl_unique_scanned']} unique JSONL/JSONL.gz files, {counts['jsonl_records']:,} records, {counts['jsonl_seed_values']:,} numeric seed values.\n- {counts['json_unique_scanned']} unique JSON/JSON.gz files, {interval_count:,} interval candidates examined.\n- Actual CSV/JSONL overlaps: {len(actual_hits)}; JSON numeric/seed mentions: {len(json_hits)}; JSON interval overlaps: {len(interval_hits)}; JSON string mentions: {len(json_strings)}, all explicitly classified in the report.\n- Missing numeric seed information: {counts['seedless_unique_csv_files']} unique CSV files, {counts['seedless_unique_jsonl_files']} unique JSONL files, {counts['jsonl_records_without_numeric_seed']:,} JSONL records. Full paths/schema are in seed_freshness.json.\n- Invalid nonblank seed values: {len(invalid)}; read/parse errors: {len(errors)}; mutations: {len(mutations)}.\n\nLocal evidence only. Undocumented trials, other machines, and seedless records remain unknown. No repository writes, model loading, tests, or games were performed.\n")
print(json.dumps({'verdict':verdict,'counts':dict(counts),'actual_hits':len(actual_hits),'json_hits':len(json_hits),'interval_hits':len(interval_hits),'string_hits':len(json_strings),'errors':len(errors),'mutations':len(mutations),'seconds':time.monotonic()-T},indent=2))
