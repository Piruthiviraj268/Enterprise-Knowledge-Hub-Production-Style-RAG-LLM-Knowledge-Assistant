from __future__ import annotations
from pathlib import Path
from .config import Settings
from .db import Database
from .index import HybridIndex
from .ingestion import ALLOWED_EXTENSIONS,parse_and_chunk
from .llm import LLMError,generate
from .rag import build_context,extractive_answer,llm_prompt,validate_generated,citations_for
class KnowledgeService:
    def __init__(self,settings=None):
        self.settings=settings or Settings.load(); self.settings.data_dir.mkdir(parents=True,exist_ok=True); self.settings.upload_dir.mkdir(parents=True,exist_ok=True); self.db=Database(self.settings.db_path); self.index=HybridIndex(); self.reindex()
    def reindex(self): self.index.rebuild(self.db.get_chunks())
    def ingest_bytes(self,file_name,content):
        if Path(file_name).suffix.lower() not in ALLOWED_EXTENSIONS: raise ValueError('Unsupported file type.')
        if len(content)>self.settings.max_upload_mb*1024*1024: raise ValueError(f'File exceeds {self.settings.max_upload_mb} MB upload limit.')
        safe=Path(file_name).name; doc_id=self.db.create_document(safe,Path(safe).suffix.lower().lstrip('.'),len(content))
        try: chunks=parse_and_chunk(content,safe); self.db.save_chunks(doc_id,chunks); self.reindex()
        except Exception: self.db.fail_document(doc_id); raise
        return next(d for d in self.db.list_documents() if d['id']==doc_id)
    def ingest_path(self,path): p=Path(path); return self.ingest_bytes(p.name,p.read_bytes())
    def search(self,q,k=None):
        return [{'chunkId':h.chunk_id,'documentId':h.document_id,'fileName':h.file_name,'page':h.page,'excerpt':h.content[:700],'score':round(h.score,4),'lexical':round(h.lexical,4),'semantic':round(h.semantic,4)} for h in self.index.search(q,k or self.settings.top_k)]
    def ask(self,q,conversation_id=None):
        hits=self.index.search(q,self.settings.top_k); conv=self.db.conversation(conversation_id,title=q[:80]); history=self.db.recent_messages(conv); answer=''; citations=[]; mode='local-extractive'
        if hits and hits[0].score>=self.settings.min_evidence and self.settings.use_openai:
            try:
                system,user=llm_prompt(q,build_context(hits),history); candidate=generate(self.settings.openai_api_key,self.settings.openai_base_url,self.settings.openai_model,system,user); candidate_citations=citations_for(hits)
                if validate_generated(candidate,candidate_citations,hits): answer,citations,mode=candidate,candidate_citations,'openai-grounded'
            except LLMError: pass
        if not answer: answer,citations=extractive_answer(q,hits,self.settings.min_evidence)
        self.db.add_message(conv,'user',q,[]); self.db.add_message(conv,'assistant',answer,citations)
        return {'conversationId':conv,'answer':answer,'citations':citations,'mode':mode,'retrieved':len(hits)}
    def seed(self):
        sample=Path(__file__).resolve().parent.parent/'sample_docs'; existing={d['file_name'] for d in self.db.list_documents()}; out=[]
        for p in sorted(sample.glob('*')):
            if p.suffix.lower() in ALLOWED_EXTENSIONS and p.name not in existing: out.append(self.ingest_path(p))
        return out
