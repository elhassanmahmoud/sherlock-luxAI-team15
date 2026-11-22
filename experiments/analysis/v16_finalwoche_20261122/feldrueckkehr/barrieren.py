"""Post-policy observation of reasons a known early scoring tile does not get an immediate replacement."""
import numpy as np
from regel import DIR,MIRROR


def count(ctx_source,obs,original,early,previous,eligible,counts):
    inner=ctx_source.inner
    if inner.last_fz is None:
        return
    b=inner.belief
    ctx, ids, _, mask, _, _, pos=inner.last_fz
    world_vis=np.asarray(obs['sensor_mask'],dtype=bool)
    vis=world_vis[::-1,::-1].T if b.mirrored else world_vis
    ships=[]
    for k,uid in enumerate(ids):
        if ctx['ally_ene'][uid]<0:
            continue
        tile=tuple(map(int,pos[k]))
        d0=int(original[uid,0])
        d=MIRROR[d0] if b.mirrored else d0
        dx,dy=DIR[d] if d!=5 else (0,0)
        ships.append((k,uid,tile,d,(tile[0]+dx,tile[1]+dy)))
    enemies=set(map(tuple,ctx['enemy_coords']))
    for x,y in early-previous:
        p=(b.W-1-y,b.H-1-x) if b.mirrored else (x,y)
        if not b.point_tiles[p]: why='unbestaetigt'
        elif not vis[p]: why='nicht_sichtbar'
        elif p in enemies: why='sichtbar_vom_gegner_besetzt'
        elif any(q[-1]==p for q in ships): why='v16_kehrt_bereits_zurueck'
        else:
            near=[q for q in ships if abs(q[2][0]-p[0])+abs(q[2][1]-p[1])==1]
            free=[q for q in near if not b.point_tiles[q[2]] and not b.point_tiles[q[4]] and q[3]!=5]
            legal=[q for q in free if mask[q[0],DIR.index((p[0]-q[2][0],p[1]-q[2][1]))]
                   and ctx['ally_ene'][q[1]]-ctx['move_cost']>=10]
            if not near: why='keine_nachbareinheit'
            elif not free: why='alle_nachbarn_punkten_oder_schiessen'
            elif not legal: why='nicht_bezahlbar_oder_gesperrt'
            elif any(c['tile']==list(p) for c in eligible): why='konkreter_reparaturvorschlag'
            elif p not in ctx_source.established or b.match_step-ctx_source.established[p]>8: why='besetzung_zu_kurz_oder_zu_lange_her'
            else: why='zu_grosse_abweichung_vom_netz'
        counts[why]=counts.get(why,0)+1
