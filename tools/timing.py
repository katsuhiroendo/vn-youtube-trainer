import re, json, sys, itertools, statistics
VI=set('ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ')
VIW={'alo','ao','mình','không','có','canada','em','anh','cho','con','hai','ba','nam','sao','nha','xin','la','mai','kem','bia','toi','ga','ca','an'}
ENW=set("i you he she it we they the a an is are am was were do does did can could will would have has had my your his her our their this that to of in on at for with from and or but not please excuse me what where when how why who there here be very so just like want go let it's i'm don't".split())
def read_cues(path):
    L=open(path,encoding='utf-8').read().split('\n')
    re1=re.compile(r'^(\d+:\d{2}(?::\d{2})?)(?:\d+ 時間 ?)?(?:\d+ 分 ?)?(?:\d+ 秒)?')
    cues=[]
    for i,l in enumerate(L):
        s=l.strip(); m=re1.match(s)
        if m:
            p=[int(x) for x in m.group(1).split(':')]; t=p[0]*60+p[1] if len(p)==2 else p[0]*3600+p[1]*60+p[2]
            cues.append([t,s[m.end():]])
        elif not cues and s: cues.append([0,s])
        elif cues: cues[-1][1]+=' '+s
    out=[]
    for t,x in cues:
        music='âm nhạc' in x
        x=re.sub(r'\[[^\]]*\]','',x).strip()
        out.append({'t':t,'txt':x,'music':music and not x})
    return out
def isvi_sent(s):
    t=re.sub(r'[.?!,]',' ',s).split()
    if not t: return False
    en=sum(1 for w in t if w.lower() in ENW or w.lower().split("'")[0] in ENW)
    vi=sum(1 for w in t if any(c in VI for c in w.lower()) or w.lower() in VIW)
    if en>=2: return False
    return vi/len(t)>=0.3 or (vi>0 and en==0)
def build(cues, tmax=None):
    toks=[]  # each: text, cue idx, sent idx, newsent flag
    sent=0; buf_end=True
    for k,c in enumerate(cues):
        if tmax and c['t']>tmax: break
        for w in c['txt'].split():
            toks.append({'w':w,'cue':k,'new':buf_end})
            buf_end = bool(re.search(r'[.?!]$',w))
    # sentences
    sents=[];cur=None
    for i,t in enumerate(toks):
        if t['new']: cur={'toks':[]}; sents.append(cur)
        cur['toks'].append(i); t['s']=len(sents)-1
    norm=lambda s: re.sub(r'[^\w ]','',s.lower()).strip()
    for si,s in enumerate(sents):
        s['text']=' '.join(toks[i]['w'] for i in s['toks']); s['vi']=isvi_sent(s['text'])
    for si,s in enumerate(sents):
        prev=sents[si-1] if si else None
        if not s['vi']: s['role']='en'
        elif prev and prev['vi'] and norm(prev['text'])==norm(s['text']): s['role']='slow'
        else: s['role']='norm'
    for t in toks: t['role']=sents[t['s']]['role']
    return toks,sents
def syl(w): return max(1,len(re.findall(r'[aeiouy]+',w.lower()))) 
def weights(toks,P):
    W=[]
    for t in toks:
        if t['role']=='en': W.append(P['en0']+P['en1']*syl(t['w']))
        elif t['role']=='slow': W.append(P['vs'])
        else: W.append(P['vn'])
        if re.search(r'\d',t['w']): W[-1]*=2
    return W
def pause_before(toks,i,P):
    if not toks[i]['new'] or i==0: return 0
    a,b=toks[i-1]['role'],toks[i]['role']
    if a=='en' and b!='en': return P['p_en_vi']
    if a!='en' and b=='en': return P['p_vi_en']
    return P['p_same']
def assign(toks,cues,P,skip=None):
    """times for tokens; skip=cue index whose boundary is removed (LOO)"""
    # group tokens by cue, merging skip into previous
    n=len(toks); start=[0]*n; end=[0]*n
    W=weights(toks,P)
    groups={}
    for i,t in enumerate(toks):
        k=t['cue']
        if skip is not None and k==skip: k=skip-1
        groups.setdefault(k,[]).append(i)
    keys=sorted(groups)
    for gi,k in enumerate(keys):
        idx=groups[k]; T0=cues[k]['t']
        # span end = next cue start (any cue incl. music) after the merged ones
        nk=k+1
        if skip is not None and nk==skip: nk+=1
        T1=cues[nk]['t'] if nk<len(cues) else T0+4
        units=[]
        for j,i in enumerate(idx):
            p = pause_before(toks,i,P) if j>0 else 0
            units.append((p,W[i]))
        # trailing pause if next token starts new sentence
        last=idx[-1]; tail = pause_before(toks,last+1,P) if last+1<n and toks[last+1]['cue']!=toks[last]['cue'] else 0
        if nk<len(cues) and cues[nk]['music']: tail+=0  # music cue: span already ends
        tot=sum(p+w for p,w in units)+tail
        # if cue span much longer than the speech (music/silence), cap scale to real speech rate
        sc=(T1-T0)/tot if tot else 0
        sc=min(sc,P['maxsc'])
        cur=T0
        for (p,w),i in zip(units,idx):
            cur+=p*sc; start[i]=cur; cur+=w*sc; end[i]=cur
    return start,end
def char_assign(toks,cues,skip=None):
    n=len(toks); start=[0]*n
    groups={}
    for i,t in enumerate(toks):
        k=t['cue']
        if skip is not None and k==skip: k=skip-1
        groups.setdefault(k,[]).append(i)
    for k,idx in groups.items():
        T0=cues[k]['t']; nk=k+1
        if skip is not None and nk==skip: nk+=1
        T1=cues[nk]['t'] if nk<len(cues) else T0+4
        L=sum(len(toks[i]['w'])+1 for i in idx); c=0
        for i in idx: start[i]=T0+(T1-T0)*c/L; c+=len(toks[i]['w'])+1
    return start
def loo(toks,cues,P,char=False):
    errs=[]
    firsttok={}
    for i,t in enumerate(toks): firsttok.setdefault(t['cue'],i)
    ks=[k for k in firsttok if k>0 and (k-1) in firsttok and not cues[k-1]['music']]
    for k in ks[::3]:
        if char: s=char_assign(toks,cues,skip=k)
        else: s,_=assign(toks,cues,P,skip=k)
        errs.append(abs(s[firsttok[k]]-cues[k]['t']))
    return statistics.mean(errs), statistics.median(errs), sorted(errs)[int(len(errs)*0.9)]
