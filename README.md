# 메디브릿지

메디브릿지는 질환명을 입력하면 공개 문헌과 데이터베이스 근거를 바탕으로 기존 승인약을 제외한 약물 재창출 후보를 탐색하고, 안전성, 실현 가능성, 초기 임상 설계, 비판 검토까지 정리하는 연구 지원 MVP입니다.

이 프로젝트는 진단, 처방, 자동 승인 판단을 목적으로 하지 않습니다. 연구자가 가설을 빠르게 만들고 검토할 수 있도록 돕는 근거 기반 의사결정 보조 도구입니다.

## 목표

- 한국어 또는 영어 질환명을 표준 질환명과 검색어로 정규화합니다.
- PubMed/NCBI와 ScienceON 등 공개 API에서 관련 근거를 수집합니다.
- 문헌에서 약물 재창출 후보를 추출합니다.
- 해당 질환에서 이미 승인되었거나 표준치료로 쓰이는 약물은 제외합니다.
- 후보별 안전성, 실현 가능성, 근거 신뢰도, 신규성을 점수화합니다.
- 초기 임상 설계 초안과 비판 검토 결과를 제공합니다.
- LangGraph 기반 멀티 에이전트 실행 흐름과 에이전트 간 협업 로그를 화면에 보여줍니다.

## 아키텍처

```text
frontend/  Next.js 기반 대시보드
backend/   FastAPI 기반 API 서버와 멀티 에이전트 파이프라인
docs/      아키텍처와 개발 계획 문서
```

전체 실행 흐름은 아래와 같습니다.

```text
사용자 질환명 입력
  -> Next.js 프론트엔드
  -> FastAPI 백엔드
  -> LangGraph Runtime
    -> Chief Decision Agent
    -> Disease Normalizer
    -> Disease Analyst Agent
    -> Evidence Retrieval Agent
      -> PubMedProvider
      -> KoreanPaperProvider
      -> EvidenceMerger
    -> Repurposing Hypothesis Agent
    -> Approval Status Agent
    -> Safety and Feasibility Agent
    -> Scoring Engine
    -> Clinical Design Agent
    -> Citation Validator
    -> Critic Agent
  -> 최종 리포트 반환
```

## 주요 에이전트

- `Chief Decision Agent`: 전체 목표를 설정하고 상태를 보며 다음 서브 에이전트에게 업무를 배정합니다.
- `Disease Normalizer`: 사용자가 입력한 한국어/영어 질환명을 표준 검색어로 변환합니다.
- `Disease Analyst Agent`: 질환 개요, 미충족 의료 수요, 타깃, 바이오마커, 환자군을 정리합니다.
- `Evidence Retrieval Agent`: PubMed/NCBI와 국내 논문 API를 병렬 호출하고 중복 근거를 병합합니다.
- `Repurposing Hypothesis Agent`: 문헌 근거에서 약물 재창출 후보를 생성합니다.
- `Approval Status Agent`: 해당 질환에서 이미 승인되었거나 표준치료로 쓰이는 약물을 제외합니다.
- `Safety and Feasibility Agent`: 금기, 이상반응, 약물상호작용, 기초 물성 기반 위험을 검토합니다.
- `Clinical Design Agent`: 대상 환자군, endpoint, inclusion/exclusion criteria, 안전성 모니터링 초안을 만듭니다.
- `Critic Agent`: 근거 부족, 출처 누락, 임상 설계 위험, 신규성 부족을 비판적으로 점검합니다.

## 필요한 API 키

루트의 `.env.example`을 복사해 `.env`를 만든 뒤 필요한 값을 채웁니다.

```powershell
Copy-Item .env.example .env
```

주요 환경 변수는 아래와 같습니다.

```text
OPENAI_API_KEY=          # LLM 기반 계획/비판/요약 기능 확장용
NCBI_API_KEY=            # NCBI/PubMed 요청 한도 완화용
NCBI_EMAIL=              # NCBI 권장 식별 이메일
NCBI_TOOL=medibridge
SCIENCEON_API_KEY=       # ScienceON 논문 API 인증키
SCIENCEON_CLIENT_ID=     # ScienceON에서 Client ID를 별도로 주는 경우 사용
SCIENCEON_API_URL=https://openapi.ndsl.kr/itemsearch.do
SCIENCEON_TICKET=ARTI
OPENFDA_API_KEY=         # 향후 openFDA 안전성 데이터 연동용
NEXT_PUBLIC_API_URL=http://localhost:8000
```

`ScienceON` 키가 없으면 국내 논문 provider는 건너뛰고 PubMed 중심으로 파이프라인이 계속 실행됩니다.

## 설치

PowerShell에서 프로젝트 루트로 이동합니다.

```powershell
cd C:\Users\bumji\source\repos\바이오공모
```

Python 가상환경을 새로 만드는 경우:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

이미 `.venv`가 있는 경우에는 의존성만 다시 설치하면 됩니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

프론트엔드 의존성 설치:

```powershell
cd C:\Users\bumji\source\repos\바이오공모\frontend
pnpm install
```

`pnpm` 명령어가 인식되지 않으면 Codex 번들 pnpm을 사용할 수 있습니다.

```powershell
C:\Users\bumji\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\pnpm.cmd install
```

## 백엔드 실행

터미널 1개를 열고 아래 명령어를 실행합니다.

```powershell
cd C:\Users\bumji\source\repos\바이오공모\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

정상 실행 확인:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

분석 API 직접 호출 예시:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/analysis/run `
  -ContentType "application/json; charset=utf-8" `
  -Body '{"input_text":"심부전","mode":"live","top_k":5}'
```

## 프론트엔드 실행

터미널을 하나 더 열고 아래 명령어를 실행합니다.

```powershell
cd C:\Users\bumji\source\repos\바이오공모\frontend
pnpm dev
```

`pnpm`이 인식되지 않는 경우:

```powershell
cd C:\Users\bumji\source\repos\바이오공모\frontend
C:\Users\bumji\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\pnpm.cmd dev
```

브라우저에서 아래 주소로 접속합니다.

```text
http://127.0.0.1:3000
```

## 테스트와 빌드

백엔드 테스트:

```powershell
cd C:\Users\bumji\source\repos\바이오공모\backend
..\.venv\Scripts\python.exe -m unittest discover -s tests
```

프론트엔드 빌드:

```powershell
cd C:\Users\bumji\source\repos\바이오공모\frontend
pnpm build
```

`pnpm`이 인식되지 않는 경우:

```powershell
cd C:\Users\bumji\source\repos\바이오공모\frontend
C:\Users\bumji\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\pnpm.cmd build
```

## Docker로 PostgreSQL 실행

향후 캐시와 벡터 검색 저장소를 PostgreSQL/pgvector로 연결할 때 사용합니다.

```powershell
cd C:\Users\bumji\source\repos\바이오공모
docker compose up -d postgres
```

중지:

```powershell
docker compose down
```

## 현재 개발 상태

- FastAPI 백엔드와 Next.js 프론트엔드가 연결되어 있습니다.
- PubMed/NCBI provider와 ScienceON provider 구조가 준비되어 있습니다.
- Evidence Retrieval Agent 내부에서 해외/국내 근거 provider를 병렬 호출하고 병합합니다.
- 기존 승인약/표준치료 약물을 제외하는 Approval Status Agent가 추가되어 있습니다.
- LangGraph Runtime이 API 응답의 `graph_summary`와 에이전트 로그에 반영됩니다.
- 프론트엔드 사이드바에서 LangGraph 노드 실행 요약과 에이전트 협업 타임라인을 확인할 수 있습니다.

## 주의사항

- 이 서비스의 결과는 연구용 가설 생성 보조 자료입니다.
- 진단, 처방, 임상시험 승인, 실제 투약 판단에 직접 사용하면 안 됩니다.
- 후보 약물은 반드시 전문가 검토, 원문 문헌 검증, 안전성 데이터 검증, 규제 검토가 필요합니다.
