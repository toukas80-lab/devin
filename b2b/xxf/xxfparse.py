import struct,sys
def parse(b):
    p=0x1c; groups=[]
    while p<len(b):
        n=b[p]; name=b[p+1:p+1+n].decode('cp1253'); p+=1+n
        cnt=struct.unpack_from('<I',b,p)[0]; p+=4; tabs=[]
        for i in range(cnt):
            sz=struct.unpack_from('<I',b,p)[0]; blob=b[p+4:p+4+sz]
            tn=blob[9:9+blob[8]].decode('cp1253') if blob[:4]==b'XSF_' else '?'
            tabs.append((p,sz,tn)); p+=4+sz
        groups.append((name,cnt,tabs))
    return groups,p
if __name__=='__main__':
    b=open(sys.argv[1],'rb').read(); print(b[:0x1c].hex(' '))
    g,end=parse(b)
    for name,cnt,tabs in g: print(name,cnt,[(t[2],t[1]) for t in tabs])
    print('end',end,len(b))
