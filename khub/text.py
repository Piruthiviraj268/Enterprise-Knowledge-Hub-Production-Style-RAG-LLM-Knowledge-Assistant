from __future__ import annotations
import re
from collections import Counter
TOKEN_RE=re.compile(r'[a-zA-Z0-9_]+')
SENTENCE_RE=re.compile(r'(?<=[.!?])\s+|[\r\n]+')
STOPWORDS=frozenset('''a about above after again all also am an and any are as at be because been before being below between both but by can could did do does doing down during each few for from further had has have having he her here hers him his how i if in into is it its just me more most my no nor not of off on once only or other our out over own same she should so some such than that the their them then there these they this those through to too under until up us very was we were what when where which while who whom why will with would you your tell please give'''.split())
def normalize(t): return re.sub(r'\s+',' ',t).strip()
def tokens(t): return [x.lower() for x in TOKEN_RE.findall(t) if x.lower() not in STOPWORDS]
def term_counter(t): return Counter(tokens(t))
def sentences(t): return [normalize(s.strip(' -•*#\t')) for s in SENTENCE_RE.split(t) if normalize(s.strip(' -•*#\t'))]
def query_variants(q):
    base=normalize(q); terms=tokens(base); return list(dict.fromkeys([base]+([' '.join(terms[:8])] if len(terms)>=3 else [])))
