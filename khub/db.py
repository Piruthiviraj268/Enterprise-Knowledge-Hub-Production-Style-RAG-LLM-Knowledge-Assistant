from __future__ import annotations
import json,sqlite3,uuid
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
SCHEMA='''
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY,file_name TEXT NOT NULL,file_type TEXT NOT NULL,size_bytes INTEGER NOT NULL,created_at TEXT NOT NULL,status TEXT NOT NULL,chunk_count INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS chunks(id TEXT PRIMARY KEY,document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,ordinal INTEGER NOT NULL,page INTEGER,content TEXT NOT NULL,metadata TEXT NOT NULL DEFAULT '{}');
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY,title TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,role TEXT NOT NULL,content TEXT NOT NULL,created_at TEXT NOT NULL,citations TEXT NOT NULL DEFAULT '[]');
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id,created_at);'''
def now(): return datetime.now(timezone.utc).isoformat()
class Database:
    def __init__(self,path): self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self.init()
    @contextmanager
    def connect(self):
        c=sqlite3.connect(self.path); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON')
        try: yield c; c.commit()
        finally: c.close()
    def init(self):
        with self.connect() as c: c.executescript(SCHEMA)
    def create_document(self,name,file_type,size):
        i=str(uuid.uuid4())
        with self.connect() as c: c.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?)',(i,name,file_type,size,now(),'indexing',0))
        return i
    def save_chunks(self,doc_id,chunks):
        with self.connect() as c:
            c.execute('DELETE FROM chunks WHERE document_id=?',(doc_id,))
            for ch in chunks: c.execute('INSERT INTO chunks VALUES (?,?,?,?,?,?)',(str(uuid.uuid4()),doc_id,ch.ordinal,ch.page,ch.text,'{}'))
            c.execute("UPDATE documents SET status='indexed',chunk_count=? WHERE id=?",(len(chunks),doc_id))
    def fail_document(self,doc_id):
        with self.connect() as c: c.execute("UPDATE documents SET status='failed' WHERE id=?",(doc_id,))
    def list_documents(self):
        with self.connect() as c: return [dict(r) for r in c.execute('SELECT * FROM documents ORDER BY created_at DESC')]
    def get_chunks(self):
        with self.connect() as c: return [dict(r) for r in c.execute("SELECT c.*,d.file_name FROM chunks c JOIN documents d ON d.id=c.document_id WHERE d.status='indexed' ORDER BY c.id")]
    def delete_document(self,i):
        with self.connect() as c: return c.execute('DELETE FROM documents WHERE id=?',(i,)).rowcount>0
    def stats(self):
        with self.connect() as c: return {'documents':c.execute("SELECT COUNT(*) FROM documents WHERE status='indexed'").fetchone()[0],'chunks':c.execute('SELECT COUNT(*) FROM chunks').fetchone()[0],'conversations':c.execute('SELECT COUNT(*) FROM conversations').fetchone()[0],'messages':c.execute('SELECT COUNT(*) FROM messages').fetchone()[0]}
    def conversation(self,i,title='New research'):
        with self.connect() as c:
            if i and c.execute('SELECT 1 FROM conversations WHERE id=?',(i,)).fetchone(): return i
            n=str(uuid.uuid4()); t=now(); c.execute('INSERT INTO conversations VALUES (?,?,?,?)',(n,title[:120],t,t)); return n
    def add_message(self,conv,role,content,citations):
        with self.connect() as c:
            c.execute('INSERT INTO messages VALUES (?,?,?,?,?,?)',(str(uuid.uuid4()),conv,role,content,now(),json.dumps(citations))); c.execute('UPDATE conversations SET updated_at=? WHERE id=?',(now(),conv))
    def recent_messages(self,conv,limit=8):
        with self.connect() as c: rows=c.execute('SELECT role,content,citations,created_at FROM messages WHERE conversation_id=? ORDER BY created_at DESC LIMIT ?',(conv,limit)).fetchall()
        return [{'role':r[0],'content':r[1],'citations':json.loads(r[2])} for r in reversed(rows)]
