"""15 mm sheet DXF (from build_sheets.py) -> NC for his 1325 router, rules in cnc/NC15.md (learned from his 01.nc).
Only --home-z changes per job: used ONLY at start (N40 G43Z..) and final park. Retracts between cuts stay Z5."""
import argparse,math,os,ezdxf
from ezdxf import path as epath
from shapely.geometry import Polygon,LineString,Point
from shapely.geometry.polygon import orient
from shapely.strtree import STRtree
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--dxf',required=True); ap.add_argument('--home-z',type=float,required=True); ap.add_argument('--out')
A=ap.parse_args()
TR=1.25; SAFE=5.0; Z1=1.0; ZIG=8.0
def levels(z0,depth,n): return [z0+(depth-z0)*(k+1)/n for k in range(n)] if z0<0 else [depth*(k+1)/n for k in range(n)]
# ---------- read DXF (LAYER_1 only: XARAXI text not cut for now) ----------
doc=ezdxf.readfile(A.dxf); C=[]; CL=[]; OP=[]; TAPS=[]
def flat(e): return [(v.x,v.y) for v in epath.make_path(e).flattening(.01)]
sh=[flat(e) for e in doc.modelspace() if e.dxf.layer=='SHEET' and e.dxftype()!='CIRCLE']  # his Corel DXFs: sheet centred on 0,0 -> move to bottom-left
OX,OY=(min(p[0] for p in sh[0]),min(p[1] for p in sh[0])) if sh else (0,0)
def circ_of(e,pts):
    if e.dxftype()=='CIRCLE': return (e.dxf.center.x-OX,e.dxf.center.y-OY,e.dxf.radius)
    if len(pts)>=13 and math.dist(pts[0],pts[-1])<.01:
        g=Polygon(pts); c=g.centroid; rr=[math.dist(q,(c.x,c.y)) for q in pts]
        if max(rr)-min(rr)<.02 and max(rr)<30: return (c.x,c.y,sum(rr)/len(rr))
for e in doc.modelspace():
    if e.dxf.layer=='LAYER_10':  # τάπες (Ø7.65 plugs): his 01.nc cuts them last, outside, helical 4x3.775 through, F1800, CW
        c=circ_of(e,[(x-OX,y-OY) for x,y in flat(e)] if e.dxftype()!='CIRCLE' else [])
        if c: TAPS.append(c)
        continue
    if e.dxf.layer!='LAYER_1': continue
    if e.dxftype()=='CIRCLE': C.append((e.dxf.center.x-OX,e.dxf.center.y-OY,e.dxf.radius)); continue
    pts=[(x-OX,y-OY) for x,y in flat(e)]
    closed=bool(getattr(e,'closed',False) or (e.dxftype()=='POLYLINE' and e.is_closed) or math.dist(pts[0],pts[-1])<.01)
    if closed and pts[0]!=pts[-1]: pts.append(pts[0])
    if closed and len(pts)>=13:  # polyline drawn circle (Corel export)
        g=Polygon(pts); c=g.centroid; rr=[math.dist(q,(c.x,c.y)) for q in pts]
        if max(rr)-min(rr)<.02 and max(rr)<30: C.append((c.x,c.y,sum(rr)/len(rr))); continue
    pts=list(LineString(pts).simplify(.02).coords)
    if closed and len(pts)>3: CL.append(Polygon(pts).buffer(0))
    else: OP.append(LineString(pts))
outers=[p for p in CL if not any(q is not p and q.area>p.area and q.contains(p) for q in CL)]
inner=[p for p in CL if not any(p is o for o in outers)]
def owner(g): return next((o for o in outers if o.contains(g)),None)
loose=[c for c in C if 3.7<c[2]<3.95 and owner(Point(c[:2])) is None]  # τάπες written on LAYER_1 (older sheets) -> taps
TAPS+=loose; C=[c for c in C if c not in loose]
# ---------- classify ----------
slits=list(OP); wedges=[]; slots=[]; pockets=[]; cb=[]; holes=[]; pkc=[]
for p in inner:
    x0,y0,x1,y1=p.bounds
    if any(p.contains(Point(cx,cy)) for cx,cy,r in C): pockets.append(p)
    elif min(x1-x0,y1-y0)<=6: wedges.append(p)
    else: slots.append(p)
for cx,cy,r in C:
    pt=Point(cx,cy)
    if any(pk.contains(pt) for pk in pockets): pkc.append((cx,cy,r)); continue
    if abs(r-2)<.05:
        o=owner(pt)
        if o is not None:
            x0,y0,x1,y1=o.bounds; d={'L':cx-x0,'R':x1-cx,'B':cy-y0,'T':y1-cy}; side=min(d,key=d.get)
            same=sum(1 for c2 in C if abs(c2[2]-2)<.05 and o.contains(Point(c2[0],c2[1])) and
                     min({'L':c2[0]-x0,'R':x1-c2[0],'B':c2[1]-y0,'T':y1-c2[1]}.items(),key=lambda t:t[1])[0]==side)
            if same>=2: cb.append((cx,cy,r)); continue   # 3 holes of the long side -> Ø7 counterbore + Ø3 (his 01.nc)
    holes.append((cx,cy,r))
# ---------- G-code writer ----------
L=[]; st=dict(x=None,y=None,z=None,f=None)
def f3(v): return '%.3f'%v
def emit(g,x=None,y=None,z=None,f=None,extra=''):
    s=g
    for k,v in (('X',x),('Y',y),('Z',z)):
        if v is not None and (st[k.lower()] is None or abs(st[k.lower()]-v)>5e-4): s+=k+f3(v); st[k.lower()]=v
    if f is not None and f!=st['f']: s+='F%.1f'%f; st['f']=f
    s+=extra
    if s!=g or extra: L.append(s)
def rapid_to(x,y): emit('G00',z=SAFE); emit('G00',x=x,y=y)
def enter(z,f):  st['f']=None; emit('G01',z=z,f=f)
def along(P,dist):  # points of closed ring P walking forward 'dist' from P[0]
    out=[]; acc=0
    for a,b in zip(P,P[1:]):
        s=math.dist(a,b)
        if acc+s>=dist: t=(dist-acc)/s if s else 0; out.append(((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])),dist)); return out
        acc+=s; out.append((b,acc))
    return out
def ring_cut(P,lv,f):  # zig ramp forward/back on the contour, then a flat lap, every level
    rapid_to(*P[0]); enter(Z1,f); z=Z1; per=sum(math.dist(a,b) for a,b in zip(P,P[1:])); zl=min(ZIG,per/2)
    for d in lv:
        fw=along(P,zl); mid=(z+d)/2
        for q,s in fw: emit('G01',x=q[0],y=q[1],z=z+(mid-z)*s/zl)
        bk=[q for q,_ in fw[:-1]][::-1]+[P[0]]; acc=0; prev=fw[-1][0]
        for q in bk: acc+=math.dist(prev,q); prev=q; emit('G01',x=q[0],y=q[1],z=mid+(d-mid)*min(acc/zl,1))
        for q in P[1:]: emit('G01',x=q[0],y=q[1],z=d)
        z=d
def ring(poly,off,ccw):
    g=poly.buffer(off,join_style=1,quad_segs=4) if off else poly
    if g.is_empty: return None
    if g.geom_type!='Polygon': g=max(g.geoms,key=lambda a:a.area)
    g=g.simplify(.02)
    g=orient(g,1 if ccw else -1); P=list(g.exterior.coords)
    k=min(range(len(P)-1),key=lambda i:(P[i][1],P[i][0])); P=P[k:-1]+P[:k+1]; return P
def helix(cx,cy,rp,lv,f,z0=Z1,cw=True,outside=False):
    sx=cx+rp; rapid_to(sx,cy)
    if z0<0: emit('G00',z=Z1); enter(z0,f)
    else: enter(z0,f)
    z=z0; sg=-1 if cw else 1; N=24; rv=rp/math.cos(math.pi/N) if outside else rp  # outside cut: chords must not cut into the part
    for d in lv:
        for k in range(1,N+1):
            a=sg*2*math.pi*k/N; r_=rp if k==N else rv; emit('G01',x=cx+r_*math.cos(a),y=cy+r_*math.sin(a),z=z+(d-z)*k/N)
        z=d
    g='G02' if cw else 'G03'
    emit(g,x=cx-rp,y=cy,extra='I%+.3fJ%+.3f'%(-rp,0)); emit(g,x=sx,y=cy,extra='I%+.3fJ%+.3f'%(rp,0))
def slit(ls,lv,f):  # on the line: ramp there, ramp back, flat pass, up, return (his 01.nc)
    P=list(ls.coords); A_,B_=P[0],P[-1]; rapid_to(*A_); enter(Z1,f); z=Z1
    for d in lv:
        mid=(z+d)/2
        for q in P[1:]: emit('G01',x=q[0],y=q[1],z=mid)
        for q in P[::-1][1:]: emit('G01',x=q[0],y=q[1],z=d)
        for q in P[1:]: emit('G01',x=q[0],y=q[1])
        emit('G00',z=SAFE); emit('G00',x=A_[0],y=A_[1]); st['f']=None; emit('G01',z=d,f=f); z=d
def ramp_lap(P,z,d):  # one lap on the ring while going down z->d (his wedges/pockets)
    per=sum(math.dist(a,b) for a,b in zip(P,P[1:])); acc=0
    for a,b in zip(P,P[1:]): acc+=math.dist(a,b); emit('G01',x=b[0],y=b[1],z=z+(d-z)*acc/per)
def helix_ring(P,lv,f):  # continuous ramp lap after lap, then a flat lap at the bottom
    rapid_to(*P[0]); enter(Z1,f); z=Z1
    for d in lv: ramp_lap(P,z,d); z=d
    for q in P[1:]: emit('G01',x=q[0],y=q[1])
def pocket(poly,lv,f):  # area clearance: ramp down on the outer ring, flat lap, then rings inward (his 00064 pocket)
    rings=[]; o=-TR
    while True:
        P=ring(poly,o,False)
        if P is None or Polygon(P).area<.05: break
        rings.append(P); o-=TR*.8
    rapid_to(*rings[0][0]); enter(Z1,f); z=Z1
    for d in lv:
        emit('G01',x=rings[0][0][0],y=rings[0][0][1]); ramp_lap(rings[0],z,d); z=d
        for P in rings:
            emit('G01',x=P[0][0],y=P[0][1])
            for q in P[1:]: emit('G01',x=q[0],y=q[1])
def nn(items,key):
    out=[]; cur=(0,0); items=list(items)
    while items:
        i=min(range(len(items)),key=lambda j:math.dist(cur,key(items[j]))); it=items.pop(i); out.append(it); cur=key(it)
    return out
c0=lambda p:(p.bounds[0],p.bounds[1])
# ---------- program in his order ----------
# stages (his rule): finish 3 boxes (12 side panels) completely, then the next 3...; other parts (fill) after; taps last
OT=STRtree(outers)
def own(g):
    pt=g if isinstance(g,Point) else (g.interpolate(.5,normalized=True) if isinstance(g,LineString) else g.representative_point())
    return next((int(k) for k in OT.query(pt) if outers[k].contains(pt)),None)
F={}
for kind,items,geo in (('slits',slits,lambda s:s),('wedges',wedges,lambda w:w),('cb',cb,lambda c:Point(c[:2])),('holes',holes,lambda c:Point(c[:2])),
                       ('slots',slots,lambda p:p),('pockets',pockets,lambda p:p),('pkc',pkc,lambda c:Point(c[:2]))):
    for it in items: F.setdefault((kind,own(geo(it))),[]).append(it)
BOX_PER_STAGE=3
pan={}
for s_ in slits:
    k=own(s_)
    if k is not None: pan[k]=s_
groups={}
for k,s_ in pan.items():
    (ax,ay),(bx,by)=s_.coords[0],s_.coords[-1]; x0,y0,x1,y1=outers[k].bounds
    Lk,Wk=((y1-y0),(x1-x0)) if abs(by-ay)>abs(bx-ax) else ((x1-x0),(y1-y0))
    groups.setdefault(round(Lk*2)/2,{}).setdefault(round(Wk*2)/2,[]).append(k)
cen=lambda k:outers[k].centroid.coords[0]
boxes=[]
for Lk,byw in groups.items():
    ws={w:nn(v,cen) for w,v in byw.items()}
    if len(ws)==2 and len(set(len(v) for v in ws.values()))==1:  # custom: 2+2 different sides
        a_,b_=ws.values(); boxes+=[a_[i:i+2]+b_[i:i+2] for i in range(0,len(a_),2)]
    else:
        flat_=[k for w in sorted(ws) for k in ws[w]]; boxes+=[flat_[i:i+4] for i in range(0,len(flat_),4)]
boxes=nn(boxes,lambda b:(sum(cen(k)[0] for k in b)/len(b),sum(cen(k)[1] for k in b)/len(b)))
stages=[set(k for b in boxes[i:i+BOX_PER_STAGE] for k in b) for i in range(0,len(boxes),BOX_PER_STAGE)]
rest=set(range(len(outers)))-set().union(*stages) if stages else set(range(len(outers)))
stages.append(rest|{None})
def g(kind,stg): return [it for k in stg for it in F.get((kind,k),[])]
for kind,items in (('slits',slits),('wedges',wedges),('cb',cb),('holes',holes),('slots',slots),('pockets',pockets),('pkc',pkc)):
    assert sum(len(g(kind,stg)) for stg in stages)==len(items),kind
assert sum(len([k for k in stg if k is not None]) for stg in stages)==len(outers)
for stg in stages:
    for s in nn(g('slits',stg),lambda s:s.coords[0]): slit(s,levels(0,-15.1,4),6000.0)
    for w in nn(g('wedges',stg),c0): helix_ring(ring(w,0,False),levels(0,-15.1,11),6000.0)
    for c in nn(g('cb',stg),lambda c:c[:2]): helix(c[0],c[1],3.5-TR,levels(0,-7.5,2),1800.0)
    for c in nn(g('holes',stg),lambda c:c[:2]): helix(c[0],c[1],c[2]-TR,levels(0,-15.1,4),1800.0)
    for c in nn(g('cb',stg),lambda c:c[:2]): helix(c[0],c[1],1.5-TR,[-11.3,-15.1],800.0,z0=-6.5)
    for p in nn(g('slots',stg),c0): helix_ring(ring(p,-TR,False),levels(0,-15.1,11),6000.0)
    for p in nn(g('pockets',stg),c0): pocket(p,levels(0,-7.0,5),6000.0)
    for c in nn(g('pkc',stg),lambda c:c[:2]): helix(c[0],c[1],c[2]-TR,[-9.7,-12.4,-15.1],1800.0,z0=-6.0)
    for o in nn([outers[k] for k in stg if k is not None],c0): ring_cut(ring(o,TR,True),levels(0,-14.1,10),6000.0)
print('stages:',' | '.join('%d parts'%len([k for k in stg if k is not None]) for stg in stages),'(boxes %d, %d per stage)'%(len(boxes),BOX_PER_STAGE))
TAP_PITCH=15.0  # his rule: taps always 15 mm apart (centre to centre, as in his DXF)
close=[(a,b) for i,a in enumerate(TAPS) for b in TAPS[i+1:] if math.dist(a[:2],b[:2])<TAP_PITCH-.05]
if close: print('ΠΡΟΣΟΧΗ τάπες πιο κοντά από 15 mm:',len(close),'ζεύγη, π.χ. %.2f,%.2f - %.2f,%.2f'%(close[0][0][:2]+close[0][1][:2]))
for c in nn(TAPS,lambda c:c[:2]): helix(c[0],c[1],c[2]+TR,levels(0,-15.1,4),1800.0,outside=True)
hz=f3(A.home_z)
out=['N0G00 G21 G17 G90','N10G00 G40 G49 G80','N20G71','N30T1M6','N40G43Z%sH1M8'%hz,'S15000M03','X0.000Y0.000']
L[1]=L[1]+'Z5.000' if L[1].startswith('G00X') else L[1]
body=L[1:]+['G00Z5.000','G00X0.000Y0.000','G00Z'+hz,'M09','G00X0.000Y0.000','M30']
out+=['N%d%s'%(70+10*i,s) for i,s in enumerate(body)]
fn=A.out or os.path.splitext(A.dxf)[0]+'.nc'
open(fn,'w',newline='\r\n').write('\n'.join(out)+'\n')
print('NC',fn,'lines',len(out),'| slits',len(slits),'wedges',len(wedges),'cb Ø7+Ø3',len(cb),'holes',len(holes),
      'slots',len(slots),'pockets',len(pockets),'pocket-circles',len(pkc),'outlines',len(outers),'taps',len(TAPS),'| home Z',hz)
