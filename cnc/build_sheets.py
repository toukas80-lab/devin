"""CDR (CorelDRAW) machine templates -> nested DXF sheets 15/20/25 mm.
Geometry is kept as true CIRCLE / LWPOLYLINE(+bulge arcs) / SPLINE entities, like CorelDRAW's own DXF export."""
import re, os, sys, glob, math, shutil, subprocess, argparse, ezdxf
from svgpathtools import parse_path, Line, Arc, QuadraticBezier, CubicBezier
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path as MPath
FONT=FontProperties(family=['Arial','Liberation Sans','DejaVu Sans'])
K=2.83465
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--cdr-dir',required=True); ap.add_argument('--out-dir',required=True)
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
    for s in segs:
        if s[0]=='C': flush(); m.add_open_spline([s[1],s[2],s[3],s[4]],degree=3,dxfattribs=a)
        else: run.append(s)
    flush()
def svg_of(path):
    r=subprocess.run([A.cdr2xhtml,path],capture_output=True); t=r.stdout.decode('utf-8','replace')
    if '<svg:svg' not in t: sys.exit('cdr2xhtml failed on %s: %s'%(path,r.stderr.decode('utf-8','replace')[:300]))
    return t[t.index('<svg:svg'):t.rindex('</svg:svg>')+10].replace('svg:','')
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
def load(path):
    s=svg_of(path); H=float((re.search(r'viewBox="[\d.\s-]*?([\d.]+)"',s) or re.search(r'height="([\d.]+)',s))[1]); P=lambda z:(z.real/K,(H-z.imag)/K)  # libcdr 0.1.9: viewBox in pt, height in "in"; older: height in pt
    cts=[]
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
    texts=[]
    for x,y,fs,t in re.findall(r'<text x="([\d.]+)" y="([\d.]+)">\s*<tspan[^>]*font-size="([\d.]+)"[^>]*>\s*([^<]*?)\s*</tspan>',s):
        # libcdr drops text rotation; in the templates the label is vertical, reading bottom->top,
        # filling the text frame whose bottom-left corner is (x,y)
        bx,by=float(x)/K,(H-float(y))/K
        tc=[tf(c,lambda px,py:(-py,px)) for c in text_contours(t,float(fs)/K)]
        b=bb([p for c in tc for p in sample(c)])
        texts+=[tf(c,lambda px,py:(px-b[0]+bx,py-b[1]+by)) for c in tc]
    return cts,texts
def parts(fn):
    cts,texts=load(fn); out=[]; B=[(c,bb(sample(c))) for c in cts]; TB=[(c,bb(sample(c))) for c in texts]
    big=[(c,b) for c,b in B if 100<b[2]-b[0]<320 and 100<b[3]-b[1]<320]
    big=[(c,b) for c,b in big if not any(o is not c and ob[0]<=b[0]+.01 and ob[1]<=b[1]+.01 and ob[2]>=b[2]-.01 and ob[3]>=b[3]-.01 and (ob[2]-ob[0])>(b[2]-b[0])+.01 for o,ob in big)]
    inside=lambda c,b,t:c[0]>=b[0]-t and c[1]>=b[1]-t and c[2]<=b[2]+t and c[3]<=b[3]+t
    for _,b in big:
        ins=[(c,cb) for c,cb in B if inside(cb,b,.6)]; tx=[c for c,cb in TB if inside(cb,b,0)]
        w,h=b[2]-b[0],b[3]-b[1]
        tri=sum(1 for _,cb in ins if 6.5<cb[2]-cb[0]<7.5 and cb[3]-cb[1]<7.5)
        kind='panel' if abs(w-215)<.5 else ('top' if tri>8 else 'bottom') if abs(w-h)<1 and w<201 else 'base' if abs(w-239)<.5 else 'other'
        mv=lambda x,y:(x-b[0],y-b[1])
        out.append(dict(kind=kind,w=w,h=h,cts=[tf(c,mv) for c,_ in ins],texts=[tf(c,mv) for c in tx]))
    return out
def rot_ccw(p):  # 90 CCW, keep bottom-left at 0 (same orientation as his Untitled-1.dxf)
    H=p['h']; f=lambda x,y:(H-y,x)
    return dict(p,w=p['h'],h=p['w'],cts=[tf(c,f) for c in p['cts']],texts=[tf(c,f) for c in p['texts']])
def fix200(p):  # 00033 bottom plate drawn 200.0 -> 199.7 (corrected by user)
    if abs(p['w']-200)<.05:
        s=199.7/200; p=dict(p,w=199.7,h=199.7,cts=[tf(c,lambda x,y:(x*s,y*s)) for c in p['cts']])
    return p
os.makedirs(A.out_dir,exist_ok=True)
M={}
for f in sorted(glob.glob(os.path.join(A.cdr_dir,'*.cdr'))):
    n=os.path.basename(f)
    if re.match(r'\d{5}',n) and 'ΑΝΩ' in n and 'ΚΑΤΩ' in n: M[n[:5]]=f
print('machines:',{k:os.path.basename(v) for k,v in M.items()})
base=[p for p in parts(os.path.join(A.cdr_dir,'02536.cdr')) if p['kind']=='base'][0]
sheets={15:[],20:[],25:[]}
for code,fn in M.items():
    ps=parts(fn); pan=[p for p in ps if p['kind']=='panel']; one=lambda k:[p for p in ps if p['kind']==k]
    assert len(one('top'))==1 and len(one('bottom'))==1 and len(pan) in (1,2),(code,[p['kind'] for p in ps])
    pan=pan*4 if len(pan)==1 else pan*2
    sheets[15]+=[dict(rot_ccw(p),code=code) for p in pan]
    sheets[20]+=[dict(fix200(one('bottom')[0]),code=code),dict(base,code=code+' base')]
    sheets[25]+=[dict(one('top')[0],code=code)]
GAP={15:2.6,20:3.275,25:3.275}; SW,SH,S=1015,2020,11
def pack(items,gap):
    items=sorted(items,key=lambda p:(-p['h'],p['code'])); x=y=S; rowh=0; pl=[]
    for p in items:
        if x+p['w']>SW-S+1e-6: x=S; y+=rowh+gap; rowh=0
        assert y+p['h']<=SH-S,'does not fit'
        pl.append((p,x,y)); x+=p['w']+gap; rowh=max(rowh,p['h'])
    return pl
for th,items in sheets.items():
    pl=pack(items,GAP[th]); doc=ezdxf.new('R2000'); doc.units=ezdxf.units.MM; m=doc.modelspace()
    for L in ('SHEET','LAYER_1','XARAXI'): doc.layers.add(L)
    m.add_lwpolyline([(0,0),(SW,0),(SW,SH),(0,SH)],close=True,dxfattribs={'layer':'SHEET'})
    fig,ax=plt.subplots(figsize=(6,12)); ax.plot([0,SW,SW,0,0],[0,0,SH,SH,0],'k-',lw=.6)
    used=0; maxy=0
    for p,x,y in pl:
        used+=p['w']*p['h']; maxy=max(maxy,y+p['h']); mv=lambda a,b:(x+a,y+b)
        for lay,col,cs in (('LAYER_1','k',p['cts']),('XARAXI','b',p['texts'])):
            for c in cs:
                c=tf(c,mv); write(m,c,lay); xs,ys=zip(*sample(c)); ax.plot(xs,ys,col+'-',lw=.25)
        ax.text(x+p['w']/2,y+3,p['code'],fontsize=4,color='r',ha='center')
    fn=os.path.join(A.out_dir,f'fyllo_{th}mm_{len(M)}mixanes_{A.version}')
    doc.saveas(fn+'.dxf'); ax.set_aspect('equal'); ax.set_title(f'{th}mm 1015x2020 - {len(pl)} kommatia',fontsize=8)
    fig.savefig(fn+'.png',dpi=200,bbox_inches='tight'); plt.close(fig)
    print(th,'mm:',len(pl),'parts, gap',GAP[th],'used height to',round(maxy,1),'fill %.0f%%'%(100*used/(SW*SH)))
