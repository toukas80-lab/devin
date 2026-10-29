"""CDR (CorelDRAW) machine templates -> nested DXF sheets 15/20/25 mm.
Geometry is kept as true CIRCLE / LWPOLYLINE(+bulge arcs) / SPLINE entities, like CorelDRAW's own DXF export."""
import random,time,re, os, sys, unicodedata, glob, math, shutil, subprocess, argparse, ezdxf
from svgpathtools import parse_path, Line, Arc, QuadraticBezier
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path as MPath
FONT=FontProperties(family=['Arial','Liberation Sans','DejaVu Sans'])
K=2.83465
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--cdr-dir',required=True); ap.add_argument('--out-dir',required=True)
ap.add_argument('--order',help='ΚΩΔΙΚΟΣ:ΤΕΜ[:κομμάτια], με κόμμα. ΤΕΜ=φύλλο: όσα χωράνε σε ολόκληρο φύλλο (π.χ. 00019:φύλλο:άνω). Custom: ΤΕΜΑΧΙΑ-ΑxΒxΜΗΚΟΣ αντί για κωδικό, π.χ. 100-25x25x185:1. Κομμάτια: κιβώτιο (4 πλαϊνά), πλαϊνό (το/τα διαφορετικά πλαϊνά μία φορά), άνω, κάτω, βάση, με + (κενό = ολόκληρη μηχανή). 4ο πεδίο ναι/όχι = εξωλκέας για τη βάση αυτής της μηχανής (αλλιώς --exolkeas). Π.χ. "00034:12:κιβώτιο,00030:3,00033:2:άνω+κάτω,00019:1::όχι". Κομμάτι-συσκευασίας (CDR χωρίς ΑΝΩ ΚΑΤΩ): ΚΩΔΙΚΟΣ:ΠΛΗΘΟΣ:ΠΑΧΟΣ π.χ. "03839:4:20" (ΤΕΜ=φύλλο: όσα χωράνε)')
ap.add_argument('--exolkeas',default='όχι',help='βάσεις για εξωλκέα: ναι (με τους κύκλους Ø90/Ø66 στη μέση) / όχι (χωρίς, προεπιλογή).')
ap.add_argument('--fill',help='ΚΩΔΙΚΟΣ:ΠΑΧΟΣ, με κόμμα: γεμίζει ΟΛΑ τα κενά σε κάθε φύλλο αυτού του πάχους (με 11 mm περιμετρικά) με όσα κομμάτια του CDR χωράνε, και στραμμένα 90° (π.χ. "03839:20,03923:15")')
ap.add_argument('--diag',help='κωδικοί με κόμμα: τυπώνει τα κομμάτια του CDR (διαστάσεις, κύκλοι ανά Ø, μικρά σχήματα) και σταματά')
ap.add_argument('--ena-dxf',action='store_true',help='όλα τα κομμάτια σε ένα DXF (για έλεγχο)')
ap.add_argument('--version',default='v1'); ap.add_argument('--cdr2xhtml',default=shutil.which('cdr2xhtml') or 'cdr2xhtml')
A=ap.parse_args()

# contour = (segs, closed); seg = ('L',p0,p1) | ('A',p0,pmid,p1) | ('C',p0,c1,c2,p1)
def tf(ct,f): return ([(s[0],*[f(*p) for p in s[1:]]) for s in ct[0]],ct[1])
def bez(s,t):
    p0,c1,c2,p1=s[1:]; u=1-t
    return tuple(u**3*p0[i]+3*u*u*t*c1[i]+3*u*t*t*c2[i]+t**3*p1[i] for i in (0,1))
def circ3(a,b,c):
    ax,ay=a; bx,by=b; cx,cy=c; d=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    if abs(d)<1e-12: return None
    ux=((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
    uy=((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
    return (ux,uy),math.hypot(ax-ux,ay-uy)
def sweep(s):  # signed sweep angle of 3-point arc
    (c,r)=circ3(*s[1:]); an=lambda p:math.atan2(p[1]-c[1],p[0]-c[0])
    d1=(an(s[3])-an(s[1]))%(2*math.pi); dm=(an(s[2])-an(s[1]))%(2*math.pi)
    return d1 if dm<d1 else -(2*math.pi-d1)
def arcpts(s,n=24):
    (c,r)=circ3(*s[1:]); a0=math.atan2(s[1][1]-c[1],s[1][0]-c[0]); sw=sweep(s)
    return [(c[0]+r*math.cos(a0+sw*i/n),c[1]+r*math.sin(a0+sw*i/n)) for i in range(n+1)]
def sample(ct):
    pts=[]
    for s in ct[0]:
        q=[s[1],s[2]] if s[0]=='L' else arcpts(s) if s[0]=='A' and circ3(*s[1:]) else [bez(s,i/16) for i in range(17)] if s[0]=='C' else [s[1],s[3]]
        pts+=q if not pts else q[1:]
    return pts
def bb(pts):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; return min(xs),min(ys),max(xs),max(ys)
def as_circle(ct):
    segs,closed=ct
    if not closed or not segs or any(s[0]!='A' for s in segs): return None
    cr=circ3(*segs[0][1:])
    if not cr: return None
    (c,r)=cr
    if all(abs(math.hypot(p[0]-c[0],p[1]-c[1])-r)<1e-3 for s in segs for p in s[1:]) and abs(abs(sum(sweep(s) for s in segs))-2*math.pi)<1e-3: return c,r
def to_bez(s):
    if s[0]=='C': return [s[1:]]
    if s[0]=='L' or not circ3(*s[1:]):
        p0,p1=s[1],s[-1]; d=(p1[0]-p0[0],p1[1]-p0[1]); return [(p0,(p0[0]+d[0]/3,p0[1]+d[1]/3),(p0[0]+2*d[0]/3,p0[1]+2*d[1]/3),p1)]
    (c,r)=circ3(*s[1:]); a0=math.atan2(s[1][1]-c[1],s[1][0]-c[0]); sw=sweep(s); k=max(1,math.ceil(abs(sw)/(math.pi/2)-1e-9)); d=sw/k
    h=4/3*math.tan(d/4); out=[]; P=lambda t:(c[0]+r*math.cos(t),c[1]+r*math.sin(t))
    for i in range(k):
        t0,t1=a0+i*d,a0+(i+1)*d; p0,p1=P(t0),P(t1)
        out.append((p0,(p0[0]-h*r*math.sin(t0),p0[1]+h*r*math.cos(t0)),(p1[0]+h*r*math.sin(t1),p1[1]-h*r*math.cos(t1)),p1))
    return out
def write(m,ct,layer):
    a={'layer':layer,'color':250}; c=as_circle(ct)  # same entity colour as CorelDRAW's DXF export
    if c: m.add_circle(c[0],c[1],dxfattribs=a); return
    segs,closed=ct; run=[]
    def flush(close=False):
        if not run: return
        pts=[(s[1][0],s[1][1],(math.tan(sweep(s)/4) if s[0]=='A' and circ3(*s[1:]) else 0)) for s in run]
        if not close: pts.append((run[-1][-1][0],run[-1][-1][1],0))
        m.add_lwpolyline(pts,format='xyb',close=close,dxfattribs=a); run.clear()
    if all(s[0] in 'LA' for s in segs): run+=segs; flush(close=closed); return
    # one SPLINE for the whole contour (never broken), Bezier pieces like CorelDRAW: 4 control points each, knots x4
    bz=[q for s in segs for q in to_bez(s)]; n=len(bz)
    sp=m.add_spline(dxfattribs=a); sp.dxf.degree=3
    sp.control_points=[p for q in bz for p in q]; sp.knots=[i/n for i in range(n+1) for _ in range(4)]
    sp.dxf.flags=11 if closed else 8
def svg_of(path):
    r=subprocess.run([A.cdr2xhtml,path],capture_output=True); t=r.stdout.decode('utf-8','replace')
    if '<svg:svg' not in t: sys.exit('cdr2xhtml failed on %s: %s'%(path,r.stderr.decode('utf-8','replace')[:300]))
    return [g.replace('svg:','') for g in re.findall(r'<svg:svg.*?</svg:svg>',t,re.S)]  # one SVG per CDR page
def text_contours(t,size):
    out=[]; cur=[]; start=last=None
    for v,code in TextPath((0,0),t,size=size,prop=FONT).iter_segments(curves=True,simplify=False):
        v=[tuple(v[i:i+2]) for i in range(0,len(v),2)]
        if code==MPath.MOVETO:
            if cur: out.append((cur,False))
            cur=[]; start=last=v[0]
        elif code==MPath.LINETO: cur.append(('L',last,v[0])); last=v[0]
        elif code==MPath.CURVE3:
            q,e=v; cur.append(('C',last,tuple(last[i]+2/3*(q[i]-last[i]) for i in (0,1)),tuple(e[i]+2/3*(q[i]-e[i]) for i in (0,1)),e)); last=e
        elif code==MPath.CURVE4: cur.append(('C',last,v[0],v[1],v[2])); last=v[2]
        elif code==MPath.CLOSEPOLY:
            if last!=start: cur.append(('L',last,start))
            out.append((cur,True)); cur=[]
    if cur: out.append((cur,False))
    return out
def rev(ct): return [(g[0],*g[:0:-1]) for g in ct[::-1]]
def join_open(cts,tol=.05):  # open pieces whose ends chain into a loop -> one closed contour (e.g. 03923 outline drawn as 4 open paths)
    eq=lambda a,b:abs(a[0]-b[0])<tol and abs(a[1]-b[1])<tol
    op=[i for i,(c,cl) in enumerate(cts) if not cl and c]; used=set(); out=[c for c in cts if c[1] or not c[0]]
    for i in op:
        if i in used: continue
        ch=list(cts[i][0]); mem=[i]
        while not eq(ch[-1][-1],ch[0][1]):
            nx=next(((j,False) for j in op if j not in used and j not in mem and eq(cts[j][0][0][1],ch[-1][-1])),None) or \
               next(((j,True) for j in op if j not in used and j not in mem and eq(cts[j][0][-1][-1],ch[-1][-1])),None)
            if not nx: break
            j,r=nx; ch+=rev(cts[j][0]) if r else cts[j][0]; mem.append(j)
        if len(mem)>1 and eq(ch[-1][-1],ch[0][1]): used.update(mem); out.append((ch,True))
    return out+[cts[i] for i in op if i not in used]
def load(path,join=False):
  cts=[]; texts=[]
  for pg,s in enumerate(svg_of(path)):  # pages placed 5 m apart in x so parts of different pages never overlap
    H=float((re.search(r'viewBox="[\d.\s-]*?([\d.]+)"',s) or re.search(r'height="([\d.]+)',s))[1]); X0=pg*5000; P=lambda z,H=H,X0=X0:(z.real/K+X0,(H-z.imag)/K)  # libcdr 0.1.9: viewBox in pt, height in "in"; older: height in pt
    for d in re.findall(r'<path d="([^"]*)"',s):
        for sp in parse_path(d.replace('\n',' ')).continuous_subpaths():
            segs=[]
            for g in sp:
                if isinstance(g,Line): segs.append(('L',P(g.start),P(g.end)))
                elif isinstance(g,Arc): segs.append(('A',P(g.start),P(g.point(.5)),P(g.end)))
                elif isinstance(g,QuadraticBezier):
                    a,q,e=g.start,g.control,g.end; segs.append(('C',P(a),P(a+2/3*(q-a)),P(e+2/3*(q-e)),P(e)))
                else: segs.append(('C',P(g.start),P(g.control1),P(g.control2),P(g.end)))
            cts.append((segs,sp.isclosed()))
    for x,y,fs,t in re.findall(r'<text x="([\d.]+)" y="([\d.]+)">\s*<tspan[^>]*font-size="([\d.]+)"[^>]*>\s*([^<]*?)\s*</tspan>',s):
        # libcdr drops text rotation; in the templates the label is vertical, reading bottom->top,
        # filling the text frame whose bottom-left corner is (x,y)
        bx,by=float(x)/K+X0,(H-float(y))/K
        tc=[tf(c,lambda px,py:(-py,px)) for c in text_contours(t,float(fs)/K)]
        b=bb([p for c in tc for p in sample(c)])
        texts+=[tf(c,lambda px,py:(px-b[0]+bx,py-b[1]+by)) for c in tc]
  return (join_open(cts) if join else cts),texts
def parts(fn,lo=50,hi=320,join=False):
    cts,texts=load(fn,join); out=[]; B=[(c,bb(sample(c))) for c in cts]; TB=[(c,bb(sample(c))) for c in texts]
    big=[(c,b) for c,b in B if lo<b[2]-b[0]<hi and lo<b[3]-b[1]<hi]
    big=[(c,b) for c,b in big if not any(o is not c and ob[0]<=b[0]+.01 and ob[1]<=b[1]+.01 and ob[2]>=b[2]-.01 and ob[3]>=b[3]-.01 and (ob[2]-ob[0])>(b[2]-b[0])+.01 for o,ob in big)]
    inside=lambda c,b,t:c[0]>=b[0]-t and c[1]>=b[1]-t and c[2]<=b[2]+t and c[3]<=b[3]+t
    for _,b in big:
        ins=[(c,cb) for c,cb in B if inside(cb,b,.6)]; tx=[c for c,cb in TB if inside(cb,b,0)]
        w,h=b[2]-b[0],b[3]-b[1]
        marks=sum(1 for c,cb in ins if max(cb[2]-cb[0],cb[3]-cb[1])<10 and not as_circle(c))  # small edge marks (triangles/squares) of the top plate
        nc=sum(1 for c,_ in ins if as_circle(c))
        kind='plate' if nc>=16 else 'base' if abs(w-h)<1 else 'panel'
        mv=lambda x,y:(x-b[0],y-b[1])
        out.append(dict(kind=kind,marks=marks,w=w,h=h,cts=[tf(c,mv) for c,_ in ins],texts=[tf(c,mv) for c in tx]))
    pl=sorted([p for p in out if p['kind']=='plate'],key=lambda p:p['marks'])  # top plate = the one with the edge marks
    if len(pl)==2 and pl[1]['marks']>pl[0]['marks']: pl[0]['kind'],pl[1]['kind']='bottom','top'
    return out
def rot_ccw(p):  # 90 CCW, keep bottom-left at 0 (same orientation as his Untitled-1.dxf)
    H=p['h']; f=lambda x,y:(H-y,x)
    return dict(p,w=p['h'],h=p['w'],cts=[tf(c,f) for c in p['cts']],texts=[tf(c,f) for c in p['texts']])
def fix200(p):  # 00033 bottom plate drawn 200.0 -> 199.7 (corrected by user)
    if abs(p['w']-200)<.05:
        s=199.7/200; p=dict(p,w=199.7,h=199.7,cts=[tf(c,lambda x,y:(x*s,y*s)) for c in p['cts']])
    return p
import datetime
if not A.diag: A.out_dir=os.path.join(A.out_dir,datetime.date.today().isoformat())  # every run goes to a dated subfolder
os.makedirs(A.out_dir,exist_ok=True)
M={}
for f in sorted(glob.glob(os.path.join(A.cdr_dir,'**','*.cdr'),recursive=True)):  # also in sub-folders
    n=os.path.basename(f)
    if re.match(r'\d{5}',n) and 'ΑΝΩ' in n.upper() and 'ΚΑΤΩ' in n.upper():
        if n[:5] in M: print('ΠΡΟΣΟΧΗ: 2 CDR για %s, κρατάω %s'%(n[:5],M[n[:5]]))
        else: M[n[:5]]=f
print('machines:',{k:os.path.basename(v) for k,v in M.items()})
if A.diag:
    import collections
    for code in [c.strip().zfill(5) for c in A.diag.split(',')]:
        if code not in M: print(code,'δεν υπάρχει CDR'); continue
        cts,_=load(M[code]); B=[(c,bb(sample(c))) for c in cts]
        print('==',code,os.path.basename(M[code]),'contours',len(cts))
        for c,b in B:
            w,h=b[2]-b[0],b[3]-b[1]
            if w<50 or h<50: continue
            ins=[(o,ob) for o,ob in B if o is not c and ob[0]>=b[0]-.6 and ob[1]>=b[1]-.6 and ob[2]<=b[2]+.6 and ob[3]<=b[3]+.6]
            ci=collections.Counter(round(2*as_circle(o)[1],1) for o,_ in ins if as_circle(o))
            sm=collections.Counter('%s%.1fx%.1f'%('κλειστό ' if o[1] else 'ανοιχτό ',ob[2]-ob[0],ob[3]-ob[1]) for o,ob in ins if not as_circle(o) and max(ob[2]-ob[0],ob[3]-ob[1])<60)
            print(' part at (%.1f,%.1f) %.1fx%.1f closed=%s inside=%d circles Ø:%s'%(b[0],b[1],w,h,c[1],len(ins),dict(ci)))
            print('   small:',dict(sm.most_common(8)))
    sys.exit()
base=[p for p in parts((glob.glob(os.path.join(A.cdr_dir,'**','02536.cdr'),recursive=True) or [os.path.join(A.cdr_dir,'02536.cdr')])[0]) if p['kind']=='base'][0]

# ---- custom machines «100-25x25x185» = pieces (n×n) - piece a×b - skewer length ----
# box length = skewer+55 (≤155) / +60 (>155); panels from 00657 (box ≤210) or 00034 (box >210);
# plates from 00657 (Ø11, top with the 7 mm edge triangles); base from 02536; margins kept in mm, grid Π = n·piece.
WEDGE_DOWN=1.5  # custom: wedges 1.5 mm lower than in the templates (towards the slit start)
CUSTOM=re.compile(r'^(\d+)-([\d.]+)x([\d.]+)x([\d.]+)$')
def cnorm(t): return re.sub(r'[χΧ×*]','x',t.strip().lower()).replace(',','.')
def circle(cx,cy,r): return ([('A',(cx+r,cy),(cx,cy+r),(cx-r,cy)),('A',(cx-r,cy),(cx,cy-r),(cx+r,cy))],True)
def cbb(c): return bb(sample(c))
def pw(v,mid,d): return v+d if v>mid else v   # stretch: everything past the middle moves by d
def base_for(Px,Py,exo=None):  # every base: 02536 (Π=200) stretched to grid Π, margins kept in mm, circles Ø90/Ø66 unchanged, centred
    dx,dy=Px-200,Py-200; m0=base['w']/2; out=[]
    for c in base['cts']:
        cr=as_circle(c)
        if cr and not (EXOLK if exo is None else exo): continue  # no extractor: no centre circles
        out.append(circle(cr[0][0]+dx/2,cr[0][1]+dy/2,cr[1]) if cr else tf(c,lambda x,y:(pw(x,m0,dx),pw(y,m0,dy))))
    return dict(kind='base',w=base['w']+dx,h=base['h']+dy,cts=out,texts=[])
def custom_parts(spec):
    N,a,b,sk=CUSTOM.match(spec).groups(); N=int(N); a,b,sk=float(a),float(b),float(sk); n=math.isqrt(N)
    if n*n!=N: sys.exit('custom %s: τα τεμάχια πρέπει να είναι n×n (π.χ. 100=10×10)'%spec)
    L=sk+(55 if sk<=155 else 60); ref='00657' if L<=210 else '00034'
    if ref not in M or '00657' not in M: sys.exit('custom χρειάζεται τα CDR 00657 και 00034')
    rp=[q for q in parts(M[ref]) if q['kind']=='panel'][0]; W0,L0=rp['w'],rp['h']; P0=200
    def panel(d):
        P=n*d; out=[]; sl=sorted([c for c in rp['cts'] if not c[1] and cbb(c)[2]-cbb(c)[0]<.01],key=lambda c:cbb(c)[0])
        x0=cbb(sl[0])[0]; wd=[c for c in rp['cts'] if c[1] and abs(cbb(c)[2]-cbb(c)[0]-5)<.2 and cbb(c)[0]<x0<cbb(c)[2]]
        for c in rp['cts']:
            cr=as_circle(c); b_=cbb(c)
            if cr:
                (cx,cy),r=cr
                if cx>20: cx=15+P/2+(cx-(15+P0/2))      # bottom hole: middle of the grid
                cy=cy+(L-L0) if cy>L0-30 else (L/2 if abs(cy-L0/2)<1 else cy)
                out.append(circle(cx,cy,r))
            elif b_[2]-b_[0]>W0-1: out.append(tf(c,lambda x,y:(pw(x,W0/2,P-P0),pw(y,L0/2,L-L0))))
        for k in range(1,n):
            dx=15+k*d-x0; dL=L-L0  # slit top end + wedge follow the top edge (wedge distance from the top as in the template)
            out+=[tf(sl[0],lambda x,y,dx=dx:(x+dx,pw(y,L0/2,dL)))]+[tf(c,lambda x,y,dx=dx:(x+dx,pw(y,L0/2,dL)-WEDGE_DOWN)) for c in wd]
        return dict(kind='panel',w=P+15,h=L,cts=out,texts=[])
    pl={q['kind']:q for q in parts(M['00657'])}
    def plate(top):
        t=pl['top']; Px,Py=n*a,n*b; e=-0.15; out=[]
        for c in t['cts']:
            b_=cbb(c)
            if c[1] and not as_circle(c) and b_[2]-b_[0]>190: out.append(tf(c,lambda x,y:(pw(x,100,Px-P0),pw(y,100,Py-P0))))
        for k in range(1,n):
            out.append(([('L',(e+k*a,e),(e+k*a,e+Py))],False)); out.append(([('L',(e,e+k*b),(e+Px,e+k*b))],False))
        for i in range(n):
            for j in range(n): out.append(circle(e+(i+.5)*a,e+(j+.5)*b,5.5))
        if top:  # 00657 triangles of its first grid line (at 20) on each edge, centred on every new grid line
            for c in t['cts']:
                b_=cbb(c)
                if c[1] or max(b_[2]-b_[0],b_[3]-b_[1])>10: continue
                cx,cy=(b_[0]+b_[2])/2,(b_[1]+b_[3])/2
                if cx<10 or cx>190:   # left/right edge: along y
                    if abs(cy-(e+20))>4: continue
                    out+=[tf(c,lambda x,y,k=k:(pw(x,100,Px-P0),y+k*b-20)) for k in range(1,n)]
                else:
                    if abs(cx-(e+20))>4: continue
                    out+=[tf(c,lambda x,y,k=k:(x+k*a-20,pw(y,100,Py-P0))) for k in range(1,n)]
        return dict(kind='top' if top else 'bottom',w=Px-0.3,h=Py-0.3,cts=out,texts=[])
    pa,pb=panel(a),panel(b)
    return dict(kivotio=[dict(rot_ccw(q),code=spec) for q in (pa,pa,pb,pb)],
                plai=[dict(rot_ccw(q),code=spec) for q in [pa]+([pb] if (pa['w'],pa['h'])!=(pb['w'],pb['h']) else [])],
                kato=[dict(plate(False),code=spec)],
                vasi=[dict(base_for(n*a,n*b),code=spec+' base')],ano=[dict(plate(True),code=spec)])
PARTS={'kivotio':15,'plai':15,'kato':20,'vasi':20,'ano':25}  # kivotio = the 4 side panels; plai = each distinct side once
ALL=[k for k in PARTS if k!='plai']  # κομπλέ (κενό πεδίο κομματιών) = χωρίς πλαϊνό
ALIAS={'κιβωτιο':'kivotio','πλαινο':'plai','κατω':'kato','βαση':'vasi','ανω':'ano'}
norm=lambda w:''.join(c for c in unicodedata.normalize('NFD',w.strip().lower()) if not unicodedata.combining(c))
def cdr_of(code): return [g for g in glob.glob(os.path.join(A.cdr_dir,'**','*.cdr'),recursive=True) if os.path.basename(g).startswith(code)]
order=[]; FULL={}
for it in (A.order.split(',') if A.order else [c+':1' for c in M]):
    f=it.strip().split(':'); code=cnorm(f[0]); code=code if CUSTOM.match(code) else code.zfill(5); q=(0 if norm(f[1]) in ('φυλλο','fyllo','fullo') else int(f[1])) if len(f)>1 else 1
    if code not in M and not CUSTOM.match(code):  # κομμάτι-συσκευασίας (piece-CDR): ΚΩΔΙΚΟΣ:ΠΛΗΘΟΣ:ΠΑΧΟΣ
        if not cdr_of(code): sys.exit('no CDR template for %s (have: %s)'%(code,', '.join(M)))
        mm=int(f[2]) if len(f)>2 and f[2].strip() else 0
        if mm not in (15,20,25): sys.exit('πάχος στο %r: γράψε ΚΩΔΙΚΟΣ:ΠΛΗΘΟΣ:ΠΑΧΟΣ (15/20/25)'%it)
        order.append((code,q,['%dmm'%mm],None,mm)); continue
    want=[ALIAS.get(norm(w),norm(w)) for w in f[2].split('+')] if len(f)>2 and f[2].strip() else list(ALL)
    exo=None
    if len(f)>3:
        v=norm(f[3])
        if v not in ('ναι','οχι','nai','oxi','yes','no'): sys.exit('εξωλκέας στο %r: γράψε ναι ή όχι'%it)
        exo=v in ('ναι','nai','yes')
    if set(want)-set(PARTS): sys.exit('άγνωστο κομμάτι στο %r, γράψε: κιβώτιο / πλαϊνό / άνω / κάτω / βάση'%it)
    order.append((code,q,want,exo,None))
EXOLK=None
if any('vasi' in w for _,_,w,_,_ in order):
    v=norm(A.exolkeas)
    if v not in ('ναι','οχι','nai','oxi','yes','no'): sys.exit('--exolkeas: γράψε ναι (με τρύπα στη μέση) ή όχι (χωρίς).')
    EXOLK=v in ('ναι','nai','yes')
print('order:',[(c,q,'+'.join(w))+(() if e is None else ('εξωλκέας' if e else 'χωρίς εξωλκέα',)) for c,q,w,e,_ in order])
sheets={15:[],20:[],25:[]}; cache={}; skipped=[]
for code,q,want,exo,mm in order:
    if mm:  # κομμάτι-συσκευασίας: q αντίτυπα κάθε μοναδικού κομματιού του CDR σε φύλλο mm (φύλλο: γέμισμα ολόκληρου)
        if code not in cache:
            fp=[dict(p,code=code) for p in parts(cdr_of(code)[0],5,1000,join=True)]
            seen=set(); fp=[u for u in fp if not ((k:=(tuple(sorted((round(u['w'],1),round(u['h'],1)))),len(u['cts']))) in seen or seen.add(k))]
            if not fp: sys.exit('το %s δεν έχει κομμάτια'%cdr_of(code)[0])
            print(code,'κομμάτια CDR:',', '.join('%.1fx%.1f'%(p['w'],p['h']) for p in fp))
            cache[code]=fp
        if q: sheets[mm]+=cache[code]*q
        else: FULL[mm]=FULL.get(mm,[])+cache[code]
        continue
    if code not in cache and CUSTOM.match(code): cache[code]=custom_parts(code)
    if code not in cache:
        ps=parts(M[code]); pan=[p for p in ps if p['kind'] in ('panel','base')]; one=lambda k:[p for p in ps if p['kind']==k]
        print(code,'κομμάτια CDR:',', '.join('%s %.1fx%.1f'%(p['kind'],p['w'],p['h']) for p in ps))
        if not (len(one('top'))==1 and len(one('bottom'))==1 and len(pan) in (1,2)):
            print('ΠΡΟΣΟΧΗ: %s παραλείπεται, το CDR δεν έχει 1 άνω + 1 κάτω + 1-2 πλαϊνά: %s'%(code,[p['kind'] for p in ps])); skipped.append(code); continue
        bt=fix200(one('bottom')[0])
        cache[code]=dict(kivotio=[dict(rot_ccw(p),code=code) for p in (pan*4 if len(pan)==1 else pan*2)],
                         plai=[dict(rot_ccw(p),code=code) for p in pan],
                         kato=[dict(bt,code=code)],vasi=[dict(base_for(bt['w']+.3,bt['h']+.3),code=code+' base')],Px=bt['w']+.3,Py=bt['h']+.3,
                         ano=[dict(one('top')[0],code=code)])
    for k in want:
        ps_=cache[code][k]
        if k=='vasi' and exo is not None and 'Px' in cache[code]: ps_=[dict(base_for(cache[code]['Px'],cache[code]['Py'],exo),code=code+' base')]
        if q: sheets[PARTS[k]]+=ps_*q
        else: FULL[PARTS[k]]=FULL.get(PARTS[k],[])+ps_  # ΤΕΜ=φύλλο: as many as fit on a whole sheet
GAP={15:2.6,20:3.275,25:3.275}; SW,SH,S=1015,2020,11
def pack(items,gap):  # maxrects (0°/90°), several orders/rules; keep fewest sheets, then lowest used height (biggest leftover)
    for p in items: assert min(p['w'],p['h'])<=SW-2*S and max(p['w'],p['h'])<=SH-2*S,'part bigger than sheet'
    W,H=SW-2*S+gap,SH-2*S+gap  # each part takes w+gap x h+gap
    def cut(fr,x,y,w,h):
        nf=[]
        for (fx,fy,fw,fh) in fr:
            if x>=fx+fw-1e-9 or x+w<=fx+1e-9 or y>=fy+fh-1e-9 or y+h<=fy+1e-9: nf.append((fx,fy,fw,fh)); continue
            if x>fx: nf.append((fx,fy,x-fx,fh))
            if x+w<fx+fw: nf.append((x+w,fy,fx+fw-x-w,fh))
            if y>fy: nf.append((fx,fy,fw,y-fy))
            if y+h<fy+fh: nf.append((fx,y+h,fw,fy+fh-y-h))
        return [a for k,a in enumerate(nf) if not any(k!=m and b[0]<=a[0]+1e-9 and b[1]<=a[1]+1e-9 and b[0]+b[2]>=a[0]+a[2]-1e-9
                and b[1]+b[3]>=a[1]+a[3]-1e-9 and (b!=a or m<k) for m,b in enumerate(nf))]
    def run(order,rule):
        shs=[]
        for p in order:
            vs=(p,rot(p)) if abs(p['w']-p['h'])>.01 else (p,)
            for si in list(range(len(shs)))+[len(shs)]:
                if si==len(shs): shs.append([[(0,0,W,H)],[]])
                fr,pl=shs[si]; best=None
                for q in vs:
                    w,h=q['w']+gap,q['h']+gap
                    for (fx,fy,fw,fh) in fr:
                        if w<=fw+1e-6 and h<=fh+1e-6:
                            sc=(fy+h,fx) if rule==0 else (min(fw-w,fh-h),fy+h,fx)
                            if best is None or sc<best[0]: best=(sc,q,fx,fy,w,h)
                if best: break
            _,q,x,y,w,h=best; pl.append((q,x+S,y+S)); shs[si][0]=cut(fr,x,y,w,h)
        return [pl for _,pl in shs]
    keys=[lambda p:(-p['h'],p['code']),lambda p:(-p['w']*p['h'],p['code']),lambda p:(-max(p['w'],p['h']),p['code']),lambda p:(-p['w'],p['code'])]
    score=lambda r:(len(r),max(y+q['h'] for q,x,y in r[-1]),sum(max(y+q['h'] for q,x,y in s_) for s_ in r))
    best=min((run(sorted(items,key=k),rule) for k in keys for rule in (0,1)),key=score)
    rnd=random.Random(1); t0=time.time(); base=sorted(items,key=keys[1])
    while time.time()-t0<min(20,1+.4*len(items)):  # random swaps of the area order: keep any better layout (deterministic seed)
        o=base[:]
        for _ in range(rnd.randint(1,max(1,len(o)//3))): a,b=rnd.randrange(len(o)),rnd.randrange(len(o)); o[a],o[b]=o[b],o[a]
        r=run(o,rnd.randint(0,1))
        if score(r)<score(best): best=r; base=o
    return best
tag='_'.join('%sx%s%s%s'%(c,q or 'fyllo','' if set(ALL)<=set(w) else '-'+'+'.join(w),'' if e is None else ('-exo' if e else '-xoris')) for c,q,w,e,_ in order) if A.order else '%dmixanes'%(len(M)-len(skipped))
if EXOLK is not None and all(e is None for *_,e,_ in order): tag+='_exolkeas' if EXOLK else '_xoris-exolkea'
if len(tag)>80: tag='%dkodikoi_%s'%(len(order),'-'.join(c for c,*_ in order))[:80]
FILL={}
for it in (A.fill.split(',') if A.fill else []):
    c,th=it.strip().split(':'); c=c.zfill(5); th=int(th)
    fs=[f for f in glob.glob(os.path.join(A.cdr_dir,'**','*.cdr'),recursive=True) if os.path.basename(f).startswith(c)]
    if not fs: sys.exit('--fill: δεν βρέθηκε CDR που να αρχίζει με %s'%c)
    fp=[dict(p,code=c) for p in parts(fs[0],5,1000,join=True)]
    seen=set(); fp=[q for q in fp if not ((k:=(tuple(sorted((round(q['w'],1),round(q['h'],1)))),len(q['cts']))) in seen or seen.add(k))]  # many copies of the same piece in one CDR -> one
    print('fill',c,os.path.basename(fs[0]),th,'mm, κομμάτια:',', '.join('%.1fx%.1f'%(p['w'],p['h']) for p in fp))
    if not fp: sys.exit('--fill: το %s δεν έχει κλειστά κομμάτια'%fs[0])
    FILL[th]=FILL.get(th,[])+fp
for th,v in FULL.items(): FILL[th]=v+FILL.get(th,[])
if A.ena_dxf: sheets={'ola':[p for v in sheets.values() for p in v]}; GAP['ola']=max(GAP.values())
def rot(p):
    f=lambda x,y,h=p['h']:(h-y,x)
    return dict(p,w=p['h'],h=p['w'],cts=[tf(c,f) for c in p['cts']],texts=[tf(c,f) for c in p['texts']])
def fill_sheet(pl,fps,gap):  # try preferring 0° and 90°, keep the one that fits more
    best=max((fill_try(list(pl),fps,gap,fl) for fl in (False,True)),key=len); n=len(best)-len(pl); pl[:]=best; return n
def outer(p):  # outline polygon of a part (largest closed contour)
    from shapely.geometry import Polygon
    return max((Polygon(sample(c)) for c in p['cts'] if c[1] and len(sample(c))>2),key=lambda g:g.area).buffer(.1,join_style=2)  # +0.1: sampled chords lie inside curves
LAT={}; AREA={}
def lattice(q,gap):  # densest repeat pattern of q by real shape: rows with offset, or 0°/90° checkerboard; None if no better than its box
    key=(id(q),gap)
    if key in LAT: return LAT[key]
    from shapely.affinity import translate
    vs=[q,rot(q)]; P=[translate(outer(v),-v['w']/2,-v['h']/2) for v in vs]; R=max(q['w'],q['h'])
    def ok(var,px,py,ox):  # var(i,j)->variant index; check cells (0..1,0..1) against neighbours
        for i0,j0 in ((0,0),(1,0),(0,1),(1,1)):
            a=translate(P[var(i0,j0)],i0*px+j0*ox,j0*py)
            for i in range(i0-3,i0+4):
                for j in range(j0-2,j0+3):
                    if (i,j)==(i0,j0): continue
                    cx,cy=i*px+j*ox,j*py
                    if abs(cx-(i0*px+j0*ox))>R+gap or abs(cy-j0*py)>R+gap: continue
                    if a.distance(translate(P[var(i,j)],cx,cy))<gap-1e-6: return False
        return True
    def least(f,lo,hi):
        if not f(hi): return None
        for _ in range(22):
            m=(lo+hi)/2; lo,hi=(lo,m) if f(m) else (m,hi)
        return hi+1e-3
    best=None; base=(q['w']+gap)*(q['h']+gap)
    one=lambda i,j:0; chk=lambda i,j:(i+j)%2
    px1=least(lambda px:ok(one,px,1e4,0),0,q['w']+gap+.5)
    if not px1: LAT[key]=None; return None
    for k in range(16):  # single orientation, row offset ox
        ox=px1*k/16; py=least(lambda py:ok(one,px1,py,ox),0,q['h']+gap+.5)
        if py and (not best or px1*py<best[0]): best=(px1*py,one,px1,py,ox)
    for k in range(25):  # checkerboard 0°/90°
        px=R*(.5+k/24)+gap; py=least(lambda py:ok(chk,px,py,0),0,R+gap+.5)
        if py and ok(chk,px,py,0) and (not best or 2*px*py/2<best[0]): best=(px*py,chk,px,py,0)
    LAT[key]=best+(q,) if best and best[0]<base*.97 else None
    return LAT[key]
def lat_place(q,gap,f,lat):  # lattice points of q inside free rect f (same rule as boxes: x>=a0, x+w+gap<=a1)
    _,var,px,py,ox=lat; vs=[q,rot(q)]; a0,b0,a1,b1=f; out=[]
    for sx in range(4):
      for sy in range(4):
        cand=[]; x0=a0+max(v['w'] for v in vs)/2+sx*px/4; y0=b0+max(v['h'] for v in vs)/2+sy*py/4
        for j in range(-2,int((b1-b0)/py)+3):
            for i in range(-3,int((a1-a0)/px)+4):
                v=vs[var(i,j)]; cx=x0+i*px+(j*ox)%px; cy=y0+j*py; x,y=cx-v['w']/2,cy-v['h']/2
                if x>=a0-1e-6 and y>=b0-1e-6 and x+v['w']+gap<=a1+1e-6 and y+v['h']+gap<=b1+1e-6: cand.append((v,x,y))
        if len(cand)>len(out): out=cand
    return out
def fill_try(pl,fps,gap,flip):  # maxrects: drop fill parts (both orientations) into every free gap, keeping S mm at the edges
    mind=min(min(p['w'],p['h']) for p in fps)+gap; free=[(S,S,SW-S+gap,SH-S+gap)]; n=0
    def occupy(x0,y0,x1,y1):
        nf=[]
        for f in free:
            a0,b0,a1,b1=f
            if x0>=a1 or x1<=a0 or y0>=b1 or y1<=b0: nf.append(f); continue
            if x0>a0: nf.append((a0,b0,x0,b1))
            if x1<a1: nf.append((x1,b0,a1,b1))
            if y0>b0: nf.append((a0,b0,a1,y0))
            if y1<b1: nf.append((a0,y1,a1,b1))
        nf=list(dict.fromkeys(f for f in nf if f[2]-f[0]>=mind-1e-6 and f[3]-f[1]>=mind-1e-6))
        free[:]=[f for f in nf if not any(g is not f and g[0]<=f[0] and g[1]<=f[1] and g[2]>=f[2] and g[3]>=f[3] for g in nf)]
    for p,x,y in pl:  # real extents: some library lines stick out of the outline by a few 0.1 mm
        e=[bb(sample(c)) for c in p['cts']]; occupy(x+min(min(b[0] for b in e),0),y+min(min(b[1] for b in e),0),x+max(max(b[2] for b in e),p['w'])+gap,y+max(max(b[3] for b in e),p['h'])+gap)
    for q in sorted(fps,key=lambda p:-p['w']*p['h']):
        lat=lattice(rot(q) if flip and abs(q['w']-q['h'])>.01 else q,gap) if len(q['cts'])<40 else None
        while lat:  # shaped piece that nests tighter than its box: fill the biggest gap with a lattice block, repeat
            best=max(((lat_place(lat[5],gap,f,lat[:5]),f) for f in free),key=lambda t:len(t[0]),default=([],None))[0]
            if not best: break
            pl+=best; occupy(min(x for _,x,_ in best),min(y for *_,y in best),max(x+v['w'] for v,x,_ in best)+gap,max(y+v['h'] for v,_,y in best)+gap)
        vs=[q]+([rot(q)] if abs(q['w']-q['h'])>.01 else []); vs=vs[::-1] if flip else vs
        while True:
            c=min(((f[1],f[0],i) for f in free for i,v in enumerate(vs) if f[2]-f[0]>=v['w']+gap-1e-6 and f[3]-f[1]>=v['h']+gap-1e-6),default=None)
            if not c: break
            y,x,i=c; v=vs[i]; pl.append((v,x,y)); occupy(x,y,x+v['w']+gap,y+v['h']+gap)
    return pl
packs_by={th:pack(items,GAP[th]) for th,items in sheets.items() if items}
for th,fp in FILL.items():
    key='ola' if A.ena_dxf else th; pk=packs_by.setdefault(key,[[]])
    print('fill',th,'mm:',sum(fill_sheet(pl,fp,GAP[key]) for pl in pk),'κομμάτια σε',len(pk),'φύλλα')
for th,packs in packs_by.items():
  for si,pl in enumerate(packs,1):
      doc=ezdxf.new('R2000'); doc.units=ezdxf.units.MM; m=doc.modelspace()
      for L in ('SHEET','LAYER_1','XARAXI'): doc.layers.add(L)
      m.add_lwpolyline([(0,0),(SW,0),(SW,SH),(0,SH)],close=True,dxfattribs={'layer':'SHEET'})
      fig,ax=plt.subplots(figsize=(6,12)); ax.plot([0,SW,SW,0,0],[0,0,SH,SH,0],'k-',lw=.6)
      used=0; maxy=0
      for p,x,y in pl:
          used+=AREA.get(id(p)) or AREA.setdefault(id(p),outer(p).area); maxy=max(maxy,y+p['h']); mv=lambda a,b:(x+a,y+b)
          for lay,col,cs in (('LAYER_1','k',p['cts']),('XARAXI','b',p['texts'])):
              for c in cs:
                  c=tf(c,mv); write(m,c,lay); xs,ys=zip(*sample(c)); ax.plot(xs,ys,col+'-',lw=.25)
          ax.text(x+p['w']/2,y+3,p['code'],fontsize=4,color='r',ha='center')
      fn=os.path.join(A.out_dir,f'fyllo_{th}'+('' if th=='ola' else 'mm')+f'_{tag}'+(f'_f{si}of{len(packs)}' if len(packs)>1 else '')+f'_{A.version}')
      doc.saveas(fn+'.dxf'); ax.set_aspect('equal'); ax.set_title(f'{th} 1015x2020 - {len(pl)} kommatia',fontsize=8)
      fig.savefig(fn+'.png',dpi=200,bbox_inches='tight'); plt.close(fig)
      print(os.path.basename(fn)+'.dxf',th,'mm:',len(pl),'parts, gap',GAP[th],'used height to',round(maxy,1),'material used %.0f%%'%(100*used/(SW*SH)))
