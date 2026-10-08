import tempfile,unittest
from pathlib import Path
from khub.config import Settings
from khub.ingestion import chunk_text
from khub.index import HybridIndex
from khub.service import KnowledgeService
class CoreTests(unittest.TestCase):
    def test_chunking(self):
        chunks=chunk_text('one '*500,None,100,20); self.assertGreater(len(chunks),3); self.assertTrue(chunks[0].text)
    def test_hybrid_search(self):
        idx=HybridIndex(); idx.rebuild([{'id':'1','document_id':'a','file_name':'a.md','content':'The annual learning budget is INR 30,000.','page':None},{'id':'2','document_id':'b','file_name':'b.md','content':'Employees may work remotely three days per week.','page':None}]); self.assertEqual(idx.search('learning budget',2)[0].chunk_id,'1')
    def test_local_rag(self):
        with tempfile.TemporaryDirectory() as td:
            s=KnowledgeService(Settings(data_dir=Path(td),llm_enabled=False)); s.ingest_bytes('policy.md',b'Employees receive 24 days of paid annual leave per year.'); r=s.ask('How many annual leave days do employees receive?'); self.assertIn('24',r['answer']); self.assertEqual(r['mode'],'local-extractive'); self.assertTrue(r['citations'])
if __name__=='__main__':unittest.main()
