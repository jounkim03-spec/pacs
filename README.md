# 로컬 PACS 시제품

빈 프로젝트에서 구성한 Orthanc + OHIF + FastAPI/SQLite + React 워크리스트입니다.
**아직 Docker 및 브라우저 통합 검증을 수행하지 않았으며 완료된 PACS로 간주하면 안 됩니다.**
PDF는 제공되지 않아 해당 페이지와의 일치 여부도 미확인입니다.

## 실행
Docker Engine 및 Compose 플러그인을 준비한 뒤:
```sh
docker compose up --build -d
python3 -m venv .venv
. .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/sample.py
```
http://localhost:8080 접속. DICOM 수신은 localhost:4242, AE Title ORTHANC.
합성 샘플은 samples/에 생성하며 같은 폴더로 다시 실행하면 UID를 유지합니다.
manifest.json에서 검사 UID와 예상 개수를 확인합니다.
종료는 docker compose down. 볼륨은 유지됩니다.

## 시연
환자 이름/ID, 날짜 범위, 진료과, 외래/입원으로 검색합니다.
환자를 고르고 검사를 선택하면 시리즈 썸네일과 판독문이 표시됩니다.
판독문이 없으면 '판독문 없음'입니다. 진료 정보와 판독문은 SQLite에서 관리합니다.
판독 상태 입력값은 미판독/판독 중/판독 완료, 내원 구분은 외래/입원입니다.
View 또는 검사 더블클릭으로 해당 UID의 OHIF URL을 엽니다.
브라우저 뒤로 가기로 돌아오면 검색과 선택 상태를 복원합니다.

## 검증 현황 및 남은 작업
- 통과: Python 소스 구문 컴파일.
- 미실행: 컨테이너 이미지 가용성, Compose 기동, C-STORE 수신, QIDO/WADO 조회.
- 미실행: CT/DX 표시, 실제 로드 UID와 manifest 대조, 썸네일, DB 영속성, 오류 화면.
- 미실행: 스크롤, W/L, 확대, 회전, 길이 측정, 주석, 분할 및 스카우트 위치 참조선.
- 합성 스카우트와 축상면에 동일 좌표계를 지정했으나 실제 참조선 동작 검증이 필요합니다.
- 현재 프런트는 React JavaScript 프로토타입이며 TypeScript 빌드 전환이 남아 있습니다.
- React는 esm.sh에서 로드하므로 인터넷 연결이 필요합니다.
- OHIF 전용 목록 복귀 버튼은 아직 없으며 브라우저 뒤로 가기를 사용합니다.
- 자동 API/브라우저 테스트 및 샘플 Compose 프로필은 아직 없습니다.

Orthanc 관리 HTTP 포트는 외부에 게시하지 않으며 로컬 시연만 대상으로 합니다.
L3 슬라이스/근육 분석은 이번 구현에 포함하지 않습니다.

## 예시 판독문·진료 정보 등록
샘플 DICOM 전송 후 다음 명령으로 같은 검사 UID에 앱 정보를 등록합니다.
```sh
.venv/bin/python scripts/seed_reports.py
```
CT는 영상의학과/입원/판독 완료 및 합성 자료임을 밝힌 예시 판독문,
X-ray는 정형외과/외래/미판독/판독문 없음으로 등록됩니다.
이 명령은 샘플 manifest에 있는 검사의 앱 정보를 덮어씁니다.

### 2026-11-11 로컬 샘플 등록 검증
실행 중인 서버에 pynetdicom C-STORE로 34개 인스턴스를 전송해 전부 성공했습니다.
API에서 CT 1건(2시리즈, 33장), DX 1건(1시리즈, 1장)을 확인했습니다.
manifest의 StudyInstanceUID와 워크리스트 UID 일치, DICOMweb 인스턴스 개수 일치,
전체 3시리즈 썸네일 HTTP 200 및 예시 진료 정보·판독문 저장 응답 200을 확인했습니다.
OHIF 페이지 응답은 200입니다. 브라우저에서 실제 픽셀 표시·도구 조작은 아직 미검증입니다.

## 워크스테이션 화면
참고 스크린샷 구도로 왼쪽 OHIF, 오른쪽 검색·환자·검사 목록,
시리즈 필름스트립 및 판독문 패널을 배치했습니다.
View/검사 더블클릭은 왼쪽 내장 OHIF에 해당 검사 UID를 전달합니다.
썸네일을 왼쪽 영역으로 드래그하면 해당 검사가 열립니다.
드래그는 검사 단위이며 특정 시리즈를 OHIF 뷰포트에 직접 배치하는 기능은 아닙니다.
영상 닫기를 눌러도 검색 및 검사 선택은 유지됩니다.
변경 후 JavaScript 구문 검사와 CSS·OHIF 경로 HTTP 200을 확인했습니다.
브라우저 자동 검증은 호스트의 libnspr4.so 누락으로 실행하지 못했습니다.
