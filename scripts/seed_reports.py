"""Register app metadata for studies created by sample.py."""
import argparse,json,urllib.request
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--url',default='http://localhost:8080')
p.add_argument('--manifest',default='samples/manifest.json')
a=p.parse_args()
for study in json.loads(Path(a.manifest).read_text()):
 ct=study['modality']=='CT'
 body={'department':'영상의학과' if ct else '정형외과','encounter':'입원' if ct else '외래','status':'판독 완료' if ct else '미판독','report':'[합성 데이터 시연용 판독문]\n합성 CT 축상면 및 스카우트 영상입니다.\n영상 조회와 측정 기능 확인을 위한 자료이며 실제 환자나 임상 소견을 나타내지 않습니다.' if ct else ''}
 request=urllib.request.Request(a.url+'/api/reports/'+study['StudyInstanceUID'],data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='PUT')
 with urllib.request.urlopen(request,timeout=30) as r:
  print(study['modality'],study['StudyInstanceUID'],r.status)
