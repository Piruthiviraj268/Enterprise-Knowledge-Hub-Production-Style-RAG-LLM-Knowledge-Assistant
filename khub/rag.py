from __future__ import annotations
import math,re
from .text import sentences,tokens
from .index import Hit
CITE_RE=re.compile(r'\[(\d+)\]')
def citations_for(hits): return [{'id':i+1,'documentId':h.document_id,'fileName':h.file_name,'page':h.page,'excerpt':h.content[:700],'score':round(h.score,4)} for i,h in enumerate(hits)]
def build_context(hits): return '\n\n'.join(f"[{i}] {h.file_name}{f', page {h.page}' if h.page else ''}\n{h.content}" for i,h in enumerate(hits,1))
def extractive_answer(q,hits,min_evidence=.18):
    citations=citations_for(hits)
    if not hits or hits[0].score<min_evidence:return "I couldn't find enough evidence in the indexed documents to answer that confidently.",[]
    qset=set(tokens(q)); candidates=[]
    for idx,h in enumerate(hits):
        for s in sentences(h.content):
            st=set(tokens(s)); overlap=len(qset&st)
            if not overlap: continue
            coverage=overlap/max(1,len(qset)); density=overlap/max(1.0,math.sqrt(len(st))); score=.72*coverage+.18*min(1,density)+.10*h.score; candidates.append((score,s,idx+1))
    candidates.sort(reverse=True); selected=[]; seen=set()
    for _,s,idx in candidates:
        key=' '.join(tokens(s))
        if key in seen: continue
        seen.add(key); selected.append((s,idx))
        if len(selected)>=3: break
    if not selected:return "I couldn't find a passage that clearly answers this. Try a more specific question.",[]
    return 'From the indexed documents:\n\n'+'\n\n'.join(f'• {s} [{i}]' for s,i in selected),citations
def validate_generated(answer,citations,hits):
    cited=[int(n) for n in CITE_RE.findall(answer)]
    if not answer.strip() or not citations or not hits or not cited or any(n<1 or n>len(citations) for n in cited): return False
    factual=[s for s in sentences(CITE_RE.sub('',answer)) if len(tokens(s))>=4]
    if not factual:return False
    evidence=set(tokens(' '.join(citations[n-1]['excerpt'] for n in cited)))
    return all(len(set(tokens(s))&evidence)>=2 for s in factual)
def llm_prompt(q,context,history):
    system='''You are an enterprise knowledge assistant. Answer ONLY from the supplied evidence. Every factual claim must end with citations like [1] or [2]. If evidence is insufficient, say so. Never invent policies, numbers, names, dates or procedures.'''
    hist='\n'.join(f"{m['role']}: {m['content']}" for m in history[-6:]) or '(none)'
    return system,f'Conversation context:\n{hist}\n\nEvidence:\n{context}\n\nQuestion: {q}'
