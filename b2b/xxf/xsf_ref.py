import struct
from xxfparse import parse
def fields(blob):
    n=blob[8]; p=9+n
    hdr,cnt=struct.unpack_from('<IH',blob,p); p+=6
    fs=[]
    for i in range(cnt):
        t,sz,off,at=struct.unpack_from('<4H',blob,p); p+=8
        e=blob.index(b'\0',p); nm=blob[p:e].decode(); p=e+1
        fs.append((nm,t,sz,off,at))
    return hdr,fs,p
def table(b,want):
    g,_=parse(b)
    for name,cnt,tabs in g:
        for p,sz,tn in tabs:
            if tn==want: return p+4,b[p+4:p+4+sz]
def dec(t,raw):
    if t in (3,1027) and len(raw)==4: return struct.unpack('<i',raw)[0]
    if t==2 and len(raw)==2: return struct.unpack('<h',raw)[0]
    if t in (6,11) and len(raw)==8: return struct.unpack('<d',raw)[0]
    try: return raw.decode('cp1253')
    except: return raw.hex()
def rows(blob,fs,p):
    R=[]; q=p
    while q<len(blob):
        q+=5; row={}; pos={}
        for nm,t,sz,off,at in fs:
            pos[nm]=q; L=blob[q]; q+=1
            if L==0xfe: L=struct.unpack_from('<H',blob,q)[0]; q+=2
            elif L==0xff: L=struct.unpack_from('<I',blob,q)[0]; q+=4
            if L: row[nm]=dec(t,blob[q:q+L])
            q+=L
        R.append((row,pos))
    return len(R),R,q
def enc(t,v):
    if v is None: return b'\0'
    if isinstance(v,float) or t in (6,11): raw=struct.pack('<d',float(v))
    elif t in (3,1027): raw=struct.pack('<i',v)
    elif t==2: raw=struct.pack('<h',v)
    elif isinstance(v,str):
        try: raw=v.encode('cp1253')
        except: raw=bytes.fromhex(v)
    else: raise Exception((t,v))
    L=len(raw)
    if L<0xfe: return bytes([L])+raw
    if L<0x10000: return b'\xfe'+struct.pack('<H',L)+raw
    return b'\xff'+struct.pack('<I',L)+raw
def build(blob,fs,p,R):
    if not R: return bytes(blob[:p])
    out=bytearray(blob[:p])
    for i,row in enumerate(R,1):
        out+=b'\x00'+struct.pack('<I',i)
        for nm,t,sz,off,at in fs: out+=enc(t,row.get(nm))
    return bytes(out)
def groups_bytes(b):
    g,_=parse(b); res=[]; p=0x1c
    for name,cnt,tabs in g:
        res.append((name,[(tn,b[pp+4:pp+4+sz]) for pp,sz,tn in tabs]))
    return res
def assemble(head,groups):
    out=bytearray(head)
    for name,tabs in groups:
        nb=name.encode('cp1253'); out+=bytes([len(nb)])+nb+struct.pack('<I',len(tabs))
        for tn,blob in tabs: out+=struct.pack('<I',len(blob))+blob
    return bytes(out)
