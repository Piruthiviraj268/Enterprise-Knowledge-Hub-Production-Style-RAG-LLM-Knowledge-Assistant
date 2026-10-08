from __future__ import annotations
import json
from pathlib import Path
from khub.service import KnowledgeService
def main():
    s=KnowledgeService(); s.seed(); cases=json.loads((Path(__file__).parent/'questions.json').read_text()); rh=kh=0; rows=[]
    for c in cases:
        res=s.search(c['question'],5); ans=s.ask(c['question'])['answer'].lower(); hit=bool(res) and res[0]['score']>.15; cov=sum(k.lower() in ans for k in c['keywords'])/len(c['keywords']); rh+=hit; kh+=cov==1; rows.append({'question':c['question'],'retrievalHit':hit,'keywordCoverage':cov,'topFile':res[0]['fileName'] if res else None})
    print(json.dumps({'retrievalHitAt5':rh/len(cases),'answerKeywordCoverage':kh/len(cases),'cases':rows},indent=2))
if __name__=='__main__':main()
