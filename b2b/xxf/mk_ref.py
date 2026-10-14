from xsf_ref import *
import copy
b=open('template_7021.XXF','rb').read()
G=dict(groups_bytes(b))
def T(tn):
    blob=dict(G['STDSALDOC'])[tn]; hdr,fs,p=fields(blob); n,R,q=rows(blob,fs,p)
    return blob,fs,p,[r for r,_ in R]
lines=[('03137',121126,1.0,5.0),('02576',118519,2.0,10.0)]
out=[]
# FINDOC
blob,fs,p,R=T('#STDSALDOC.FINDOC'); f=R[0]
net=sum(round(q*pr,2) for _,_,q,pr in lines); vat=round(net*0.24,2); tot=round(net+vat,2)
f['SERIESNUM']=0; f['TAXSERIESNUM']=None; f['FINCODE']=None; f['POSGUID']=None
f['COMMENTS']='B2B W-000007'; f['REMARKS']='W-000007'; f['ISPRINT']=0; f['PAYMENT']=None; f['SHIPMENT']=None
for k in ('TURNOVR','TTURNOVR','LTURNOVR','NETAMNT','TNETAMNT','LNETAMNT'): f[k]=net
for k in ('VATAMNT','TVATAMNT','LVATAMNT'): f[k]=vat
for k in ('SUMAMNT','SUMTAMNT','SUMLAMNT'): f[k]=tot
out.append(('#STDSALDOC.FINDOC',build(blob,fs,p,R)))
for tn in ['#STDSALDOC.MTRDOC','#STDSALDOC.MTRLINES','#STDSALDOC.SNLINES','#STDSALDOC.FINPAYTERMS','#STDSALDOC.FPAYTRMS2','#STDSALDOC.VATANAL','#STDSALDOC.EXPANAL','#STDSALDOC.ABCTRNLINES']:
    blob,fs,p,R=T(tn)
    if tn=='#STDSALDOC.MTRDOC':
        R[0]['QTY']=R[0]['QTY1']=sum(l[2] for l in lines)
        for k in ('SHIPPINGADDR','SHPZIP','SHPCITY','SOCARRIER','TRUCKS','TRUCKSNO'): R[0][k]=None
    if tn=='#STDSALDOC.MTRLINES':
        t=R[0]; R=[]
        for i,(code,mtrl,q,pr) in enumerate(lines,1):
            r=dict(t); n=round(q*pr,2); v=round(n*0.24,2)
            r.update(MTRLINES=i,LINENUM=i,MTRL=mtrl,MTRL_CODE=code,QTY=q,QTY1=q,PRICE=pr,PRICE1=pr)
            for k in ('LINEVAL','LLINEVAL','NETLINEVAL','LNETLINEVAL','TRNLINEVAL','LTRNLINEVAL'): r[k]=n
            r['VATAMNT']=r['LVATAMNT']=v; r['SXPERC']=round(n+v,2); R.append(r)
    if tn=='#STDSALDOC.VATANAL':
        R[0].update(SUBVAL=net,LSUBVAL=net,VATVAL=vat,LVATVAL=vat)
    if tn=='#STDSALDOC.FINPAYTERMS':
        R=[]
    out.append((tn,build(blob,fs,p,R)))
data=assemble(b[:0x1c],[('STDSALDOC',out)])
open('ref_out.XXF','wb').write(data)
# verify
for name,tabs in groups_bytes(data):
    for tn,bl in tabs:
        hdr,fs,p=fields(bl); n,R,q=rows(bl,fs,p); assert q==len(bl)
        if tn in('#STDSALDOC.FINDOC','#STDSALDOC.MTRLINES','#STDSALDOC.VATANAL','#STDSALDOC.FINPAYTERMS'):
            for r,_ in R: print(tn,{k:v for k,v in r.items() if k in('SERIESNUM','FINCODE','COMMENTS','REMARKS','NETAMNT','VATAMNT','SUMAMNT','MTRL_CODE','QTY1','PRICE','LINEVAL','SUBVAL','VATVAL','AMNT')})
print(len(data),net,vat,tot)
