import ast, subprocess, json, threading, secrets, time, types, hashlib
from pathlib import Path
from http.server import BaseHTTPRequestHandler
R='/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15'
def show(ref,path): return subprocess.check_output(['git','show',f'{ref}:{path}'],cwd=R,text=True)
old=ast.parse(show('56bcc559^','agents/sherlock/main.py'))
new=ast.parse(show('56bcc559','agents/sherlock/main.py'))
helper=next(n for n in ast.walk(new) if isinstance(n,ast.FunctionDef) and n.name=='_rescue_for')
class Normalize(ast.NodeTransformer):
 def __init__(self): self.fn=''
 def visit_FunctionDef(self,n):
  if n.name=='_rescue_for': return None
  prev=self.fn;self.fn=n.name;n=self.generic_visit(n);self.fn=prev;return n
 def visit_AnnAssign(self,n):
  if isinstance(n.target,ast.Attribute) and n.target.attr in ('_relic_seen','_rescue_zones'): return None
  return self.generic_visit(n)
 def visit_Assign(self,n):
  if any(isinstance(t,ast.Attribute) and t.attr=='_rescue_zones' for t in n.targets): return None
  return self.generic_visit(n)
 def visit_If(self,n):
  if any(isinstance(x,ast.Attribute) and x.attr=='zone_rescue' for x in ast.walk(n.test)):return None
  return self.generic_visit(n)
 def visit_Call(self,n):
  if isinstance(n.func,ast.Attribute) and n.func.attr=='_rescue_for':
   return ast.parse('getattr(self, "_rescue", False)' if self.fn in ('_soft_nebula','_neb_cand_step') else 'self._rescue',mode='eval').body
  return self.generic_visit(n)
equivalent=ast.dump(old,include_attributes=False)==ast.dump(Normalize().visit(new),include_attributes=False)
assert equivalent
ns={};exec(compile(ast.fix_missing_locations(ast.Module(body=[helper],type_ignores=[])),'helper','exec'),ns)
for p1 in (False,True):
 for p2 in (False,True):
  for rescue in (False,True):
   dummy=types.SimpleNamespace(_rescue=rescue,_rescue_zones=set(),cfg=types.SimpleNamespace(point_pair_swap=p1,art_move_guard=p2))
   assert ns['_rescue_for'](dummy,None,None) is rescue
src=show('35a9ebc','scripts/sherlock_server.py');tree=ast.parse(src)
keep=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('BadRequest','Sessions','decode','make_handler')]
ns=dict(Callable=object,MAX_SESSIONS=8,IDLE_SECONDS=1800,MAX_DEPTH=12,threading=threading,secrets=secrets,time=time,BaseHTTPRequestHandler=BaseHTTPRequestHandler)
# Strip annotations to keep extraction entirely stdlib.
class Strip(ast.NodeTransformer):
 def visit_arg(self,n):n.annotation=None;return n
 def visit_FunctionDef(self,n):n.returns=None;return self.generic_visit(n)
mod=Strip().visit(ast.Module(body=keep,type_ignores=[]));exec(compile(ast.fix_missing_locations(mod),'server_extracted','exec'),ns)
entered=0;lock=threading.Lock();release=threading.Event();all_entered=threading.Event()
def factory(player):
 global entered
 with lock:
  entered+=1
  if entered==8:all_entered.set()
 release.wait(3)
 return object()
s=ns['Sessions'](factory,max_sessions=1)
threads=[threading.Thread(target=s.new,args=('player_0',)) for _ in range(8)]
for t in threads:t.start()
try:
 assert all_entered.wait(2)
 observed={'max_sessions':1,'simultaneous_factory_calls':entered,'registered_sessions_during_construction':len(s.items)}
finally:
 release.set()
 for t in threads:t.join()
captured=[]
fake=types.SimpleNamespace(set_env_cfg=lambda cfg:captured.append(cfg))
s2=ns['Sessions'](lambda p:fake);sid=s2.new('player_0')
h=object.__new__(ns['make_handler'](s2,'dummy',True));h.path='/env_cfg'
h._route({'session':sid,'env_cfg':{'map_width':1000000000,'map_height':1000000000}})
assert captured==[{'map_width':1000000000,'map_height':1000000000}]
result={'zone_off_normalized_full_main_AST_equal':equivalent,'zone_off_boolean_P_flags_cases':8,'session_limit_counterexample':observed,'unbounded_dimensions_forwarded_to_agent':captured[0],'imports':'stdlib only; extracted AST; no sockets/models/games','source_sha256':{p:hashlib.sha256(show('35a9ebc',p).encode()).hexdigest() for p in ['agents/sherlock/main.py','agents/sherlock/config.py','scripts/sherlock_server.py','scripts/sherlock_remote_stub.py']}}
Path('/tmp/MM_review_20261102/evidence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
