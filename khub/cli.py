from __future__ import annotations
import argparse,json
from .service import KnowledgeService
def main():
    p=argparse.ArgumentParser(prog='khub',description='Enterprise Knowledge Hub CLI'); s=p.add_subparsers(dest='command',required=True)
    s.add_parser('seed'); x=s.add_parser('ingest'); x.add_argument('path'); x=s.add_parser('ask'); x.add_argument('question'); x=s.add_parser('search'); x.add_argument('question'); x.add_argument('-k',type=int,default=6); s.add_parser('stats'); s.add_parser('reindex'); s.add_parser('doctor'); a=p.parse_args(); svc=KnowledgeService()
    if a.command=='seed': print(json.dumps(svc.seed(),indent=2)); return 0
    if a.command=='ingest': print(json.dumps(svc.ingest_path(a.path),indent=2)); return 0
    if a.command=='ask': print(json.dumps(svc.ask(a.question),indent=2,ensure_ascii=False)); return 0
    if a.command=='search': print(json.dumps(svc.search(a.question,a.k),indent=2,ensure_ascii=False)); return 0
    if a.command=='stats': print(json.dumps(svc.db.stats(),indent=2)); return 0
    if a.command=='reindex': svc.reindex(); print(json.dumps(svc.db.stats(),indent=2)); return 0
    if a.command=='doctor': print(json.dumps({'database':str(svc.db.path),'documents':svc.db.stats()['documents'],'indexChunks':len(svc.index.rows),'openAIConfigured':svc.settings.use_openai},indent=2)); return 0
    return 0
if __name__=='__main__': raise SystemExit(main())
