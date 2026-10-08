from __future__ import annotations
import base64,json,time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .config import Settings
from .service import KnowledgeService
ROOT=Path(__file__).resolve().parent.parent; WEB=ROOT/'web'; settings=Settings.load(); service=KnowledgeService(settings)
class RateLimiter:
    def __init__(self,limit): self.limit=limit; self.events={}
    def allow(self,key):
        now=time.time(); recent=[t for t in self.events.get(key,[]) if now-t<60]
        if len(recent)>=self.limit: self.events[key]=recent; return False
        recent.append(now); self.events[key]=recent; return True
limiter=RateLimiter(settings.rate_limit_per_min)
class Handler(BaseHTTPRequestHandler):
    server_version='KnowledgeHub/2.1'
    def log_message(self,fmt,*args): print(f'[{self.log_date_time_string()}] {self.command} {self.path.split("?")[0]}')
    def send_json(self,status,payload):
        b=json.dumps(payload,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(b)
    def auth(self):
        if not settings.api_token:return True
        if self.headers.get('Authorization','')==f'Bearer {settings.api_token}':return True
        self.send_json(401,{'error':'Authentication required.'}); return False
    def body(self):
        n=int(self.headers.get('Content-Length','0'))
        if n>settings.max_upload_mb*1024*1024*2:raise ValueError('Request too large.')
        return json.loads(self.rfile.read(n).decode()) if n else {}
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/health': self.send_json(200,{'status':'ok','version':'2.1.0','stats':service.db.stats(),'llmEnabled':settings.use_openai}); return
        if path=='/api/stats': self.send_json(200,service.db.stats()); return
        if path=='/api/config': self.send_json(200,{'llmEnabled':settings.use_openai,'model':settings.openai_model if settings.use_openai else None,'topK':settings.top_k,'maxUploadMb':settings.max_upload_mb,'authEnabled':bool(settings.api_token)}); return
        if path=='/api/documents': self.send_json(200,{'documents':service.db.list_documents()}); return
        if path=='/' or path=='/index.html' or path.startswith('/assets/'):
            rel=Path('index.html') if path in {'/','/index.html'} else Path('assets')/Path(path.removeprefix('/assets/')); target=(WEB/rel).resolve()
            if target.is_file() and WEB.resolve() in target.parents:
                data=target.read_bytes(); ext=target.suffix; ctype={'.html':'text/html','.css':'text/css','.js':'application/javascript','.svg':'image/svg+xml'}.get(ext,'application/octet-stream'); self.send_response(200); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
        self.send_json(404,{'error':'Not found.'})
    def do_POST(self):
        if not limiter.allow(self.client_address[0]): self.send_json(429,{'error':'Rate limit exceeded.'}); return
        if not self.auth():return
        try:
            path=urlparse(self.path).path; d=self.body()
            if path=='/api/documents':
                raw=base64.b64decode(d['contentBase64'],validate=True); self.send_json(201,{'document':service.ingest_bytes(d['fileName'],raw)}); return
            if path=='/api/search': self.send_json(200,{'results':service.search(str(d.get('question','')),d.get('k'))}); return
            if path=='/api/chat':
                q=str(d.get('question','')).strip()
                if len(q)<3:raise ValueError('Question must be at least 3 characters.')
                self.send_json(200,service.ask(q,d.get('conversationId'))); return
            if path=='/api/reindex': service.reindex(); self.send_json(200,{'status':'reindexed','stats':service.db.stats()}); return
            self.send_json(404,{'error':'Not found.'})
        except (ValueError,KeyError,json.JSONDecodeError) as e:self.send_json(400,{'error':str(e)})
        except Exception as e:self.send_json(500,{'error':str(e)})
    def do_DELETE(self):
        if not self.auth():return
        try:
            path=urlparse(self.path).path
            if path.startswith('/api/documents/'):
                ok=service.db.delete_document(path.rsplit('/',1)[-1]); service.reindex(); self.send_json(200 if ok else 404,{'deleted':ok}); return
            self.send_json(404,{'error':'Not found.'})
        except Exception as e:self.send_json(500,{'error':str(e)})
def main():
    print(f'Enterprise Knowledge Hub: http://{settings.host}:{settings.port}'); print('Generation:', 'OpenAI + evidence gate' if settings.use_openai else 'local extractive fallback'); ThreadingHTTPServer((settings.host,settings.port),Handler).serve_forever()
if __name__=='__main__':main()
