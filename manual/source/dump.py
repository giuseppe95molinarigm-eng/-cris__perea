import sys,re,json
from lxml import etree
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
SRC=sys.argv[1]
doc=etree.parse(SRC+'/word/document.xml')
rels=etree.parse(SRC+'/word/_rels/document.xml.rels')
rmap={r.get('Id'):r.get('Target') for r in rels.getroot()}
body=doc.getroot().find(W+'body')
def runs(p):
    out=[]
    for r in p.iter(W+'r'):
        rpr=r.find(W+'rPr')
        b=i=False;sz=col=None;caps=False
        if rpr is not None:
            bb=rpr.find(W+'b'); b= bb is not None and bb.get(W+'val') not in('0','false')
            ii=rpr.find(W+'i'); i= ii is not None and ii.get(W+'val') not in('0','false')
            s=rpr.find(W+'sz'); sz=s.get(W+'val') if s is not None else None
            c=rpr.find(W+'color'); col=c.get(W+'val') if c is not None else None
            cp=rpr.find(W+'caps'); caps=cp is not None
        for ch in r:
            if ch.tag==W+'t': out.append({'t':ch.text or '','b':b,'i':i,'sz':sz,'c':col,'caps':caps})
            elif ch.tag==W+'br' and ch.get(W+'type')=='page': out.append({'pb':1})
            elif ch.tag==W+'br': out.append({'t':'\n','b':b,'i':i,'sz':sz,'c':col})
            elif ch.tag==W+'tab': out.append({'t':'\t'})
            elif ch.tag==W+'drawing':
                for bl in ch.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
                    ext=ch.find('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent')
                    out.append({'img':rmap[bl.get(R+'embed')].split('/')[-1],'cx':int(ext.get('cx')) if ext is not None else 0})
    return out
def para(p):
    ppr=p.find(W+'pPr'); st=num=shd=jc=None; ind=None
    if ppr is not None:
        s=ppr.find(W+'pStyle'); st=s.get(W+'val') if s is not None else None
        n=ppr.find(W+'numPr')
        if n is not None: num=n.find(W+'numId').get(W+'val')
        sh=ppr.find(W+'shd'); shd=sh.get(W+'fill') if sh is not None else None
        j=ppr.find(W+'jc'); jc=j.get(W+'val') if j is not None else None
        bd=ppr.find(W+'pBdr')
    return {'type':'p','style':st,'num':num,'shd':shd,'jc':jc,'runs':runs(p),'border':ppr is not None and ppr.find(W+'pBdr') is not None}
def table(t):
    rows=[]
    for tr in t.findall(W+'tr'):
        row=[]
        for tc in tr.findall(W+'tc'):
            tcpr=tc.find(W+'tcPr'); shd=None; span=1
            if tcpr is not None:
                s=tcpr.find(W+'shd'); shd=s.get(W+'fill') if s is not None else None
                g=tcpr.find(W+'gridSpan'); span=int(g.get(W+'val')) if g is not None else 1
            row.append({'shd':shd,'span':span,'content':[block(x) for x in tc if x.tag in(W+'p',W+'tbl')]})
        rows.append(row)
    return {'type':'tbl','rows':rows}
def block(x): return para(x) if x.tag==W+'p' else table(x)
blocks=[block(x) for x in body if x.tag in(W+'p',W+'tbl')]
# split into pages on page breaks
pages=[[]]
for b in blocks:
    if b['type']=='p' and any('pb' in r for r in b['runs']):
        rs=b['runs']; k=[j for j,r in enumerate(rs) if 'pb' in r][0]
        before=dict(b,runs=rs[:k]); after=dict(b,runs=rs[k+1:])
        if any(r.get('t','').strip() or 'img' in r for r in before['runs']): pages[-1].append(before)
        pages.append([])
        if any(r.get('t','').strip() or 'img' in r for r in after['runs']): pages[-1].append(after)
    else: pages[-1].append(b)
json.dump(pages,open('pages.json','w'),ensure_ascii=False,indent=0)
print(len(pages))
