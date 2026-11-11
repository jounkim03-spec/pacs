import sqlite3
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
app=FastAPI()
def db():
 c=sqlite3.connect('/data/app.db')
 c.execute('CREATE TABLE IF NOT EXISTS reports(uid TEXT PRIMARY KEY, department TEXT, encounter TEXT, status TEXT, report TEXT)')
 return c
async def orth(path):
 try:
  async with httpx.AsyncClient(base_url='http://orthanc:8042',timeout=30) as c:
   r=await c.get(path);r.raise_for_status();return r
 except httpx.HTTPError: raise HTTPException(503,'Orthanc 연결 실패')
class Report(BaseModel):
 department:str=''
 encounter:str=''
 status:str='미판독'
 report:str=''
@app.get('/studies')
async def studies():
 rows=(await orth('/studies?expand')).json()
 with db() as c: extra={r[0]:dict(zip(['department','encounter','status','report'],r[1:])) for r in c.execute('SELECT * FROM reports')}
 return [dict(id=s['ID'],patient=s['ParentPatient'],**s['PatientMainDicomTags'],**s['MainDicomTags'],**extra.get(s['MainDicomTags']['StudyInstanceUID'],{})) for s in rows]
@app.put('/reports/{uid}')
def save(uid:str,r:Report):
 if r.status not in ['미판독','판독 중','판독 완료'] or r.encounter not in ['','외래','입원']: raise HTTPException(422,'입력 오류')
 with db() as c: c.execute('INSERT OR REPLACE INTO reports VALUES(?,?,?,?,?)',(uid,r.department,r.encounter,r.status,r.report))
 return r
@app.get('/studies/{id}/series')
async def series(id:str): return (await orth('/studies/'+id+'/series')).json()
@app.get('/series/{id}/thumbnail')
async def thumb(id:str):
 s=(await orth('/series/'+id)).json()
 if not s['Instances']: raise HTTPException(404)
 r=await orth('/instances/'+s['Instances'][0]+'/preview')
 return Response(r.content,media_type=r.headers.get('content-type','image/png'))
