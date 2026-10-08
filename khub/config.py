from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

def load_dotenv(path: str|Path = '.env') -> None:
    p=Path(path)
    if not p.is_file(): return
    for raw in p.read_text(encoding='utf-8').splitlines():
        line=raw.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))

def _int(n,d):
    try: return int(os.getenv(n,d))
    except ValueError: return d

def _float(n,d):
    try: return float(os.getenv(n,d))
    except ValueError: return d

@dataclass(frozen=True)
class Settings:
    host:str='127.0.0.1'; port:int=8000; data_dir:Path=Path('data')
    openai_api_key:str=''; openai_model:str='gpt-4o-mini'; openai_base_url:str='https://api.openai.com/v1'
    llm_enabled:bool=True; top_k:int=6; min_evidence:float=0.18; max_upload_mb:int=10; rate_limit_per_min:int=30; api_token:str=''
    @classmethod
    def load(cls):
        load_dotenv(); key=os.getenv('OPENAI_API_KEY','').strip()
        return cls(host=os.getenv('KHUB_HOST',cls.host),port=_int('KHUB_PORT',cls.port),data_dir=Path(os.getenv('KHUB_DATA_DIR',str(cls.data_dir))),openai_api_key=key,openai_model=os.getenv('OPENAI_MODEL',cls.openai_model),openai_base_url=os.getenv('OPENAI_BASE_URL',cls.openai_base_url).rstrip('/'),llm_enabled=os.getenv('KHUB_LLM_ENABLED','true').lower() not in {'0','false','no'},top_k=max(1,_int('KHUB_TOP_K',cls.top_k)),min_evidence=max(0,min(1,_float('KHUB_MIN_EVIDENCE',cls.min_evidence))),max_upload_mb=max(1,_int('KHUB_MAX_UPLOAD_MB',cls.max_upload_mb)),rate_limit_per_min=max(1,_int('KHUB_RATE_LIMIT_PER_MIN',cls.rate_limit_per_min)),api_token=os.getenv('KHUB_API_TOKEN','').strip())
    @property
    def db_path(self): return self.data_dir/'hub.sqlite3'
    @property
    def upload_dir(self): return self.data_dir/'uploads'
    @property
    def use_openai(self): return self.llm_enabled and bool(self.openai_api_key)
