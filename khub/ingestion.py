from __future__ import annotations
import csv,io
from dataclasses import dataclass
from pathlib import Path
from docx import Document as WordDocument
from pypdf import PdfReader
ALLOWED_EXTENSIONS={'.pdf','.docx','.txt','.md','.csv'}
@dataclass(frozen=True)
class Chunk: text:str; page:int|None; ordinal:int

def extract_pages(content,file_name):
    ext=Path(file_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS: raise ValueError('Supported files: PDF, DOCX, TXT, Markdown and CSV.')
    if not content: raise ValueError('The uploaded file is empty.')
    if ext=='.pdf':
        r=PdfReader(io.BytesIO(content)); return [(i,p.extract_text() or '') for i,p in enumerate(r.pages,1)]
    if ext=='.docx':
        d=WordDocument(io.BytesIO(content)); return [(None,'\n'.join(p.text for p in d.paragraphs))]
    text=content.decode('utf-8-sig')
    if ext=='.csv': text='\n'.join(' | '.join(row) for row in csv.reader(io.StringIO(text)))
    return [(None,text)]

def chunk_text(text,page,max_chars=1100,overlap=160):
    blocks=[b.strip() for b in text.replace('\r','\n').split('\n\n') if b.strip()]
    if not blocks: blocks=[text.strip()] if text.strip() else []
    out=[]; buf=''; ordinal=0
    for block in blocks:
        candidate=f'{buf}\n\n{block}'.strip() if buf else block
        if len(candidate)<=max_chars: buf=candidate; continue
        if buf: out.append(Chunk(buf,page,ordinal)); ordinal+=1
        tail=buf[-overlap:] if buf else ''; buf=f'{tail}\n{block}'.strip()
        while len(buf)>max_chars:
            cut=buf.rfind(' ',0,max_chars); cut=cut if cut>max_chars*.65 else max_chars
            out.append(Chunk(buf[:cut].strip(),page,ordinal)); ordinal+=1; buf=buf[max(0,cut-overlap):].strip()
    if buf: out.append(Chunk(buf,page,ordinal))
    return out

def parse_and_chunk(content,file_name):
    result=[]
    for page,text in extract_pages(content,file_name): result.extend(chunk_text(text,page))
    if not result: raise ValueError('No readable text was found. Scanned PDFs require OCR before upload.')
    return result
