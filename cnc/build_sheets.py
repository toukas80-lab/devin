import re, os, sys, glob, shutil, subprocess, argparse, ezdxf
from svgpathtools import parse_path, Line
import matplotlib; matplotlib.use('Agg')
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
FONT=FontProperties(family=['Arial','Liberation Sans','DejaVu Sans'])
import matplotlib.pyplot as plt
K=2.83465
ap=argparse.ArgumentParser(description='CDR (CorelDRAW) machine templates -> nested DXF sheets 15/20/25 mm')
ap.add_argument('--cdr-dir',required=True); ap.add_argument('--out-dir',required=True)
ap.add_argument('--version',default='v1'); ap.add_argument('--cdr2xhtml',default=shutil.which('cdr2xhtml') or 'cdr2xhtml')
A=ap.parse_args(); os.makedirs(A.out_dir,exist_ok=True)
def svg_of(path):
    r=subprocess.run([A.cdr2xhtml,path],capture_output=True)
    t=r.stdout.decode('utf-8','replace')
    if '<svg:svg' not in t: sys.exit('cdr2xhtml failed on %s: %s'%(path,r.stderr.decode('utf-8','replace')[:300]))
    return t[t.index('<svg:svg'):t.rindex('</svg:svg>')+10].replace('svg:','')
def load(path):
    s=svg_of(path); H=float(re.search(r'height="([\d.]+)"',s)[1])
    polys=[]
    for d in re.findall(r'<path d="([^"]*)"',s):
        p=parse_path(d.replace('\n',' '))
        for sp in p.continuous_subpaths():
            pts=[]
            for seg in sp:
                n=1 if isinstance(seg,Line) else max(8,int(seg.length()/K/0.3))
                for i in range(0 if not pts else 1,n+1):
                    z=seg.point(i/n); pts.append((z.real/K,(H-z.imag)/K))
            closed=sp.isclosed() or abs(complex(*pts[0])-complex(*pts[-1]))<1e-3
            polys.append((pts,closed))
    texts=[]
    for x,y,fs,t in re.findall(r'<text x="([\d.]+)" y="([\d.]+)">\s*<tspan[^>]*font-size="([\d.]+)"[^>]*>\s*([^<]*?)\s*</tspan>',s):
        # libcdr drops text rotation; in the templates the label is vertical, reading bottom->top,
        # filling the text frame whose bottom-left corner is (x,y)
        bx,by=float(x)/K,(H-float(y))/K
        tp=[[(-py,px) for px,py in poly] for poly in TextPath((0,0),t,size=float(fs)/K,prop=FONT).to_polygons()]
        mx=min(p[0] for q in tp for p in q); my=min(p[1] for q in tp for p in q)
        texts+=[[(px-mx+bx,py-my+by) for px,py in q] for q in tp]
    return polys,texts
def bb(pts):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; return min(xs),min(ys),max(xs),max(ys)
def parts(fn):
    polys,texts=load(fn); out=[]
    big=[(pl,bb(pl[0])) for pl in polys if 100<bb(pl[0])[2]-bb(pl[0])[0]<320 and 100<bb(pl[0])[3]-bb(pl[0])[1]<320]
    # keep only outermost outlines
    big=[(pl,b) for pl,b in big if not any(o is not pl and o[1][0]<=b[0]+.01 and o[1][1]<=b[1]+.01 and o[1][2]>=b[2]-.01 and o[1][3]>=b[3]-.01 and (o[1][2]-o[1][0])>(b[2]-b[0])+.01 for o in big)]
    for pl,b in big:
        ins=[q for q in polys if (lambda c:c[0]>=b[0]-.6 and c[1]>=b[1]-.6 and c[2]<=b[2]+.6 and c[3]<=b[3]+.6)(bb(q[0]))]
        tx=[q for q in texts if (lambda c:c[0]>=b[0] and c[1]>=b[1] and c[2]<=b[2] and c[3]<=b[3])(bb(q))]
        w,h=b[2]-b[0],b[3]-b[1]
        tri=sum(1 for q in ins if 6.5<bb(q[0])[2]-bb(q[0])[0]<7.5 and bb(q[0])[3]-bb(q[0])[1]<7.5)
        kind='panel' if abs(w-215)<.5 else ('top' if tri>8 else 'bottom') if abs(w-h)<1 and w<201 else 'base' if abs(w-239)<.5 else 'other'
        ins=[([(x-b[0],y-b[1]) for x,y in q[0]],q[1]) for q in ins]
        tx=[[(x-b[0],y-b[1]) for x,y in q] for q in tx]
        out.append(dict(kind=kind,w=w,h=h,polys=ins,texts=tx,rot=0,src=fn))
    return out
def rot_ccw(p):  # 90 CCW, keep bottom-left at 0
    W,H=p['w'],p['h']
    f=lambda x,y:(H-y,x)
    return dict(p,w=H,h=W,polys=[([f(x,y) for x,y in q],c) for q,c in p['polys']],texts=[[f(x,y) for x,y in q] for q in p['texts']],rot=90)
def fix200(p):  # 00033 bottom plate drawn 200.0 -> 199.7 (corrected by user)
    if abs(p['w']-200)<.05:
        s=199.7/200; p=dict(p,w=199.7,h=199.7,polys=[([(x*s,y*s) for x,y in q],c) for q,c in p['polys']])
    return p
M={}
for f in sorted(glob.glob(os.path.join(A.cdr_dir,'*.cdr'))):
    n=os.path.basename(f)
    if re.match(r'\d{5}',n) and 'ΑΝΩ' in n and 'ΚΑΤΩ' in n: M[n[:5]]=f
print('machines:',{k:os.path.basename(v) for k,v in M.items()})
base=[p for p in parts(os.path.join(A.cdr_dir,'02536.cdr')) if p['kind']=='base'][0]
sheets={15:[],20:[],25:[]}
for code,fn in M.items():
    ps=parts(fn); pan=[p for p in ps if p['kind']=='panel']
    assert len([p for p in ps if p['kind']=='top'])==1 and len([p for p in ps if p['kind']=='bottom'])==1 and len(pan) in (1,2),(code,[p['kind'] for p in ps])
    pan=pan*4 if len(pan)==1 else pan*2
    sheets[15]+=[dict(rot_ccw(p),code=code) for p in pan]
    sheets[20]+=[dict(fix200([p for p in ps if p['kind']=='bottom'][0]),code=code),dict(base,code=code+' base')]
    sheets[25]+=[dict([p for p in ps if p['kind']=='top'][0],code=code)]
GAP={15:2.6,20:3.275,25:3.275}; SW,SH,S=1015,2020,11
def pack(items,gap):
    items=sorted(items,key=lambda p:(-p['h'],p['code'])); x=y=S; rowh=0; pl=[]
    for p in items:
        if x+p['w']>SW-S+1e-6: x=S; y+=rowh+gap; rowh=0
        assert y+p['h']<=SH-S, 'does not fit'
        pl.append((p,x,y)); x+=p['w']+gap; rowh=max(rowh,p['h'])
    return pl
V=A.version
for th,items in sheets.items():
    pl=pack(items,GAP[th]); doc=ezdxf.new('R12'); m=doc.modelspace()
    doc.layers.add('SHEET'); doc.layers.add('XARAXI')
    m.add_polyline2d([(0,0),(SW,0),(SW,SH),(0,SH)],close=True,dxfattribs={'layer':'SHEET'})
    fig,ax=plt.subplots(figsize=(6,12)); ax.plot([0,SW,SW,0,0],[0,0,SH,SH,0],'k-',lw=.6)
    used=0; maxy=0
    for p,x,y in pl:
        used+=p['w']*p['h']; maxy=max(maxy,y+p['h'])
        for q,c in p['polys']:
            pts=[(x+a,y+b) for a,b in q]
            if c and pts[0]==pts[-1]: pts=pts[:-1]
            m.add_polyline2d(pts,close=c,dxfattribs={'layer':'LAYER_1'})
            xs,ys=zip(*(pts+[pts[0]] if c else pts)); ax.plot(xs,ys,'k-',lw=.25)
        for q in p['texts']:
            pts=[(x+a,y+b) for a,b in q]
            if pts[0]==pts[-1]: pts=pts[:-1]
            m.add_polyline2d(pts,close=True,dxfattribs={'layer':'XARAXI'})
            xs,ys=zip(*(pts+[pts[0]])); ax.plot(xs,ys,'b-',lw=.25)
        ax.text(x+p['w']/2,y+3,p['code'],fontsize=4,color='r',ha='center')
    fn=os.path.join(A.out_dir,f'fyllo_{th}mm_{len(M)}mixanes_{V}')
    doc.saveas(fn+'.dxf'); ax.set_aspect('equal'); ax.set_title(f'{th}mm 1015x2020 - {len(pl)} kommatia',fontsize=8)
    fig.savefig(fn+'.png',dpi=200,bbox_inches='tight'); plt.close(fig)
    print(th,'mm:',len(pl),'parts, gap',GAP[th],'used height to',round(maxy,1),'fill %.0f%%'%(100*used/(SW*SH)))
    for p,x,y in pl: print('   ',p['code'],p['kind'],round(p['w'],1),'x',round(p['h'],1),'@',round(x,1),round(y,1))
