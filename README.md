# Orthanc 기반 로컬 웹 PACS

Orthanc에 DICOM을 수신·저장하고, OHIF에서 CT·X-ray를 조회하는 시제품입니다.
React 워크리스트와 FastAPI/SQLite에서 진료 정보·판독문을 관리합니다.
참고 PDF는 제공되지 않아 해당 페이지와의 일치 여부는 미확인입니다.
L3 슬라이스·골격근 분석은 이번 단계에 포함하지 않습니다.

## 다른 PC에서 실행

서버는 Docker Compose로 구성되어 있어 프로젝트 코드를 다른 PC에 복제한 후 실행할 수 있습니다.
Windows에서는 Docker Desktop의 Linux 컨테이너 환경(WSL2 백엔드),
macOS에서는 Docker Desktop, Linux에서는 Docker Engine과 Compose 플러그인을 준비합니다.
현재 검증 환경은 Windows/WSL2의 Linux x86_64입니다.
다른 OS와 ARM/Apple Silicon에서는 직접 검증하지 않았으며 이미지 아키텍처 호환 확인이 필요합니다.

최초 이미지 다운로드와 빌드에는 인터넷이 필요합니다.
현재 워크리스트의 React도 esm.sh에서 불러오므로 브라우저에 인터넷 연결이 필요합니다.
8080과 4242 포트를 다른 프로그램이 사용 중이면 먼저 충돌을 해결합니다.

```sh
git clone https://github.com/jounkim03-spec/pacs.git
cd pacs
docker compose up --build -d
docker compose ps
```

Linux에서 Docker 접근 권한이 없으면 docker 명령 앞에 sudo를 붙입니다.
Windows PowerShell과 macOS에서는 sudo를 일괄적으로 붙이지 않습니다.
접속 주소: http://localhost:8080
DICOM 수신 주소: 127.0.0.1:4242 / AE Title: ORTHANC

중지 및 다시 시작:
```sh
docker compose down
docker compose up -d
```

### 코드와 데이터는 별도로 이동

Git 복제는 코드와 설정만 가져옵니다. 기존 PC에 등록한 환자 영상과 판독문은 자동으로 복사되지 않습니다.

- 영상과 Orthanc 인덱스: Docker의 dicom 볼륨
- 판독문·판독 상태·진료과·외래/입원: Docker의 db 볼륨
- .venv와 samples 폴더: Git에서 제외

새 PC에서는 영상을 다시 전송하고 진료 정보를 등록하거나,
기존 Orthanc 볼륨과 SQLite 볼륨을 함께 백업·복원해야 합니다.
정확한 볼륨 이름은 Compose 프로젝트 이름에 따라 달라집니다.
docker compose down은 볼륨을 유지하지만, down -v는 데이터를 삭제하므로 붙이지 않습니다.
Python 가상환경은 PC 간에 복사하지 않고 각 환경에서 새로 만듭니다.

현재 포트는 127.0.0.1에만 바인딩되어 같은 PC에서 접속하는 로컬 시연용입니다.
다른 PC에서 서버에 원격 접속하는 배포 구성은 포함하지 않습니다.

## DICOM 전송 환경 준비

서버와 달리 현재 전송 스크립트는 호스트 Python에서 실행합니다.
Python 3.12 이상과 pip/venv를 준비한 후 프로젝트 폴더에서 실행하세요.
Ubuntu에서 venv 생성이 실패하면 python3-venv 패키지가 필요할 수 있습니다.

Linux / macOS / WSL:
```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements.txt
```

Windows PowerShell:
```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r scripts/requirements.txt
```

## 가지고 있는 DICOM 전송

ZIP이면 먼저 압축을 풉니다. 파일 한 개 또는 폴더를 지정할 수 있으며,
하위 폴더도 검색합니다. 실제 경로로 바꿔 실행하세요.

WSL 예시:
```sh
.venv/bin/python scripts/send_dicom.py "/mnt/c/Users/사용자명/Downloads/DICOM폴더"
```

Linux / macOS 예시:
```sh
.venv/bin/python scripts/send_dicom.py "/절대경로/DICOM폴더"
```

Windows PowerShell 예시:
```powershell
.\.venv\Scripts\python.exe scripts/send_dicom.py "C:\Users\사용자명\Downloads\DICOM폴더"
```

기본 대상은 127.0.0.1:4242, AE Title ORTHANC입니다.
필요하면 --host, --port, --aet로 변경합니다.
pynetdicom C-STORE로 기존 UID와 픽셀을 그대로 전송하며 합성 데이터를 만들지 않습니다.

- 파일마다 OK/FAILED/SKIP 결과와 마지막 전송 집계를 출력합니다.
- 확장자와 무관하게 Part 10 DICOM을 판별하며 일반 사진·CSV 등은 건너뜁니다.
- DICOM preamble이 없는 파일은 강제로 읽지 않고 건너뜁니다.
- 파일의 원래 전송 구문을 사용합니다. 서버가 이를 수락하지 않으면 실패를 표시합니다.
- 전송 실패·경고가 있거나 성공 건수가 없으면 종료 코드 1을 반환합니다.
- 같은 SOPInstanceUID 파일을 재전송해도 새 검사 UID를 만들지 않습니다.

전송 후 http://localhost:8080에서 새로고침 → 검색 초기화를 누르고 환자·검사를 선택합니다.
진료과, 내원 구분, 판독 상태와 판독문은 화면에서 입력하고 저장합니다.
영상과 앱 정보는 StudyInstanceUID로 연결됩니다. 미등록 판독문은 '판독문 없음'입니다.
사진(PNG/JPEG)이나 엑셀 파일을 이 스크립트로 전송할 수는 없습니다.

## 합성 샘플 생성·전송

아래는 Linux/macOS/WSL 명령입니다.
Windows에서는 .venv/bin/python을 .\.venv\Scripts\python.exe로 바꿉니다.

```sh
.venv/bin/python scripts/sample.py
.venv/bin/python scripts/seed_reports.py
```

samples/에 합성 CT 1건(축상면 32장·스카우트 1장), DX 1건(1장)을 생성해 전송합니다.
실제 환자나 임상 소견을 나타내지 않는 단순 합성 영상입니다.
같은 폴더로 재실행하면 UID를 유지하며 manifest.json에 검사 UID와 예상 개수가 기록됩니다.

seed_reports.py는 manifest의 검사에 다음 앱 정보를 등록합니다.
기존 샘플 검사에 수정한 정보가 있으면 덮어쓰므로 주의하세요.

| 검사 | 진료과 | 구분 | 상태 | 판독문 |
| --- | --- | --- | --- | --- |
| CT | 영상의학과 | 입원 | 판독 완료 | 합성 자료 시연용 예시 판독문 |
| DX | 정형외과 | 외래 | 미판독 | 판독문 없음 |

## 화면과 시연 순서

1. 이름·ID, 검사 날짜 범위, 진료과, 외래/입원으로 검색합니다.
2. 환자 → 검사 순서로 선택합니다.
3. 가로 시리즈 썸네일과 판독문을 확인하고 필요하면 진료 정보를 수정·저장합니다.
4. View 또는 검사 더블클릭으로 해당 검사만 왼쪽 내장 OHIF에서 엽니다.
5. 썸네일을 왼쪽으로 드래그해도 해당 검사가 열립니다.
6. 뷰어 크게 보기 / 목록과 함께 보기로 영역 폭을 전환합니다.
7. OHIF 돋보기(Zoom)를 선택하고 영상 위에서 왼쪽 버튼을 누른 채
   아래로 드래그하면 확대, 위로 드래그하면 축소됩니다.
8. 영상 닫기를 눌러도 검색 및 선택은 유지됩니다.

썸네일 드래그는 검사 단위입니다. 특정 시리즈를 OHIF 뷰포트에 직접 배치하는 기능은 아닙니다.
검색 결과 없음, 판독문 없음, Orthanc 연결 실패는 구분해 표시합니다.

## 실제 검증 결과와 남은 작업

현재까지 같은 로컬 Windows/WSL2 x86_64 환경에서 확인한 결과입니다.

| 항목 | 결과 |
| --- | --- |
| Compose 기동, Orthanc·OHIF 연결 | 통과 |
| pynetdicom 합성 CT/DX 34장 C-STORE | 전부 성공 |
| manifest와 워크리스트 검사 UID 대조 | 통과 |
| DICOMweb 인스턴스 개수 CT 33장/DX 1장 | 통과 |
| 3시리즈 썸네일 및 예시 앱 정보 저장 | HTTP 200 |
| Chromium 내장 OHIF CT/DX 실제 픽셀 표시 | 통과 |
| CT 로딩 JavaScript 오류·HTTP 400 이상 | 관찰되지 않음 |
| crossOriginIsolated 및 뷰어 폭 전환 | 통과 |
| CT Zoom 축소/확대 | 영상 영역 너비 246 → 120 → 386px 확인 |
| 사용자 DICOM 전송 스크립트 | 구문·도움말 확인, 사용자 파일 전송은 미실행 |
| 스크롤, W/L, 회전, 측정, 주석, 분할, 위치 참조선 | 도구별 실제 조작 검증 남음 |
| DB 재기동 영속성, 장애 화면 자동 검증 | 남음 |
| 다른 PC/OS, ARM 환경 | 미검증 |

프런트는 현재 React JavaScript이며 TypeScript 전환이 남아 있습니다.
전송용 Compose 프로필과 저장된 자동 API/브라우저 테스트 구성도 남아 있습니다.

### OHIF 경로 설정

사전 빌드 OHIF가 /app-config.js, /app.bundle.* 및 worker를 루트 경로에서 요청하므로
nginx는 워크리스트 파일 외 경로를 OHIF로 전달합니다.
상위 화면과 iframe에 COOP/COEP 헤더를 적용합니다.
nginx.conf 변경 후에는 설정을 확인하고 다시 불러옵니다.

```sh
docker compose exec -T web nginx -t
docker compose exec -T web nginx -s reload
```

화면이 이전 상태로 남으면 Ctrl+Shift+R로 새로고침하세요.
