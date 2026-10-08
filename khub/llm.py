from __future__ import annotations
import json,urllib.error,urllib.request
class LLMError(RuntimeError): pass
def generate(api_key,base_url,model,system,user,timeout=45):
    req=urllib.request.Request(base_url.rstrip('/')+'/chat/completions',data=json.dumps({'model':model,'temperature':.1,'messages':[{'role':'system','content':system},{'role':'user','content':user}]}).encode(),headers={'Content-Type':'application/json','Authorization':f'Bearer {api_key}'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=timeout) as resp: data=json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        try: detail=json.loads(exc.read().decode()).get('error',{}).get('message','')
        except Exception: detail=''
        raise LLMError(f'LLM request failed ({exc.code}). {detail}'.strip())
    except (urllib.error.URLError,TimeoutError,OSError) as exc: raise LLMError(f'LLM network error: {getattr(exc,"reason",exc)}')
    try:return data['choices'][0]['message']['content'].strip()
    except (KeyError,IndexError,TypeError):raise LLMError('The LLM returned an unexpected response.')
