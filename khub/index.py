from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from .text import query_variants,tokens
@dataclass
class Hit:
    chunk_id:str; document_id:str; file_name:str; content:str; page:int|None; score:float; lexical:float; semantic:float
class HybridIndex:
    def __init__(self): self.rows=[]; self.vectorizer=None; self.matrix=None
    def rebuild(self,rows):
        self.rows=rows
        if not rows: self.vectorizer=None; self.matrix=None; return
        self.vectorizer=TfidfVectorizer(lowercase=True,stop_words='english',ngram_range=(1,2),sublinear_tf=True); self.matrix=self.vectorizer.fit_transform([r['content'] for r in rows])
    @staticmethod
    def lexical_score(q,text):
        qc=Counter(tokens(q)); dc=Counter(tokens(text))
        if not qc:return 0.0
        overlap=sum(min(v,dc[k]) for k,v in qc.items()); coverage=overlap/max(1,sum(qc.values())); phrase=.15 if q.lower().strip() in text.lower() else 0.0
        return min(1.0,coverage+phrase)
    def search(self,q,k=6):
        if not self.rows or self.vectorizer is None:return []
        scores=np.zeros(len(self.rows))
        for v in query_variants(q): scores=np.maximum(scores,(self.matrix@self.vectorizer.transform([v]).T).toarray().ravel())
        out=[]
        for i,r in enumerate(self.rows):
            semantic=float(max(0,min(1,scores[i]))); lexical=self.lexical_score(q,r['content']); score=.65*semantic+.35*lexical
            if score>0: out.append(Hit(r['id'],r['document_id'],r['file_name'],r['content'],r['page'],score,lexical,semantic))
        return sorted(out,key=lambda x:x.score,reverse=True)[:k]
