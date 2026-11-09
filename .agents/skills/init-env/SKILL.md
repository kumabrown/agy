---
name: init-env
description: 표준 워크스페이스 5대 실무·산출물 저장소(00_artifacts 에이전트 산출물 전용 저장소, 01_input_data 실무 투입 자료 저장소, 02_output_data 실무 자료 저장소, 03_scripts 자동화 스크립트 저장소, 04_rag_database RAG 지식 베이스 저장소)를 스캐폴딩하고 초기화합니다. 순수하게 5대 실무 저장소 디렉터리와 README/gitkeep 파일만 생성하며, .agents 디렉터리 및 하위 거버넌스 파일은 일체 생성하지 않습니다.
---

# 워크스페이스 5대 실무 저장소 초기화 (`00_artifacts` ~ `04_rag_database`)

사용자가 `/init-env`를 실행하거나 현재 워크스페이스에 5대 번호형 디렉터리(`00_artifacts/`, `01_input_data/`, `02_output_data/`, `03_scripts/`, `04_rag_database/`) 구축 및 초기화를 요청할 때 이 스킬을 사용합니다.

## 스캐폴딩 절차 (Scaffolding Procedure)

1. **워크스페이스 경로 확인**:
   - 현재 워크스페이스 디렉터리를 확인합니다.
   - 5대 번호형 디렉터리가 이미 존재하는지 점검합니다.

2. **스캐폴딩 실행**:
   - 워크스페이스에서 스캐폴딩 스크립트를 실행하여 5대 실무 저장소를 초기화합니다:
     ```bash
     python .agents/skills/init-env/scripts/scaffold_env.py --target-dir "<workspace_path>"
     ```
   - 스크립트 실행이 불가능한 경우, 파일 생성 도구를 사용하여 5대 디렉터리와 템플릿 파일을 직접 생성합니다.

3. **스캐폴딩되는 5대 번호형 파일 구조**:
   - **`00_artifacts/` (오직 Antigravity 에이전트 작업 산출물 전용)**:
     - `00_artifacts/README.md`: 에이전트 산출물 중앙 인덱스 테이블 및 가이드.
     - `00_artifacts/plans/`: 구현 계획서 및 기능 기획서.
     - `00_artifacts/walkthroughs/`: 작업 완료 보고서 및 테스트 검증 리포트.
     - `00_artifacts/reports/`: 에이전트가 자체 조사·분석한 심층 기술 리포트.
     - `00_artifacts/designs/`: 시스템 아키텍처 및 상세 설계서.
   - **`01_input_data/` (실무 투입 자료 저장소 - 2개 폴더)**:
     - `01_input_data/README.md`: 투입 자료 보관 개요, 일련번호 규칙 및 인덱스 테이블.
     - `01_input_data/00_received/`: 외부 고객사, 시험실, 협력사에서 전달받은 원천 자료 (사양서, CAD/STEP 도면, 물성치 시트, 메쉬/격자, 측정 데이터 등).
     - `01_input_data/01_references/`: 
       - **에이전트 작업 지시 투입 자료**: 사용자가 에이전트에게 구체적인 작업을 지시하기 위해 작성·준비한 작업 요구사항 정의서, 작업 지시 메모, 해석 가이드라인, 프롬프트용 참조 텍스트.
       - **엔지니어링 표준 기준**: 솔버 공식 매뉴얼, 설계 기준, 산업 규격(ISO/ASME/ASTM).
       - **사용자 조사 리서치 자료**: 업무 수행 중 사용자가 직접 탐색·수집한 참고 논문, 장비 카탈로그, 기술 데이터시트, 웹 포럼 해결 팁.
   - **`02_output_data/` (실무 엔지니어링 자산 저장소 - 작업 흐름 3단계)**:
     - `02_output_data/README.md`: 실무 자료 보관 개요, 일련번호/버전 관리 안내 및 인덱스 테이블.
     - `02_output_data/00_data/`: 1단계 가공·정제 입력 데이터 및 시뮬레이션 솔버 해석 결과 수치 데이터.
     - `02_output_data/01_figure/`: 2단계 시각화 플롯 차트, 아키텍처 다이어그램 이미지, 유선/온도장 콘투어 이미지, 격자/도면 캡처, 솔버 실행 로그.
     - `02_output_data/02_reports/`: 3단계 최종 기술 완료 보고서, 고객 보고용 발표 슬라이드, 배포용 요약 문서.
   - **`03_scripts/` (엔지니어링 자동화 스크립트 저장소)**:
     - `03_scripts/README.md`: 스크립트 저장소 개요, 하위 폴더별 분류 기준 및 인덱스 테이블.
     - `03_scripts/python/`: 데이터 전/후처리 및 파이프라인 등 Python 스크립트 전용 (`.py`).
     - `03_scripts/script/`: 솔버 배치 저널, 세션 스크립트, 배치 파일 및 실행 파일 전용 (`.jou`, `.ccl`, `.cse`, `.bat`, `.exe`).
   - **`04_rag_database/` (RAG 지식 베이스 및 벡터 인덱스 저장소)**:
     - `04_rag_database/README.md`: RAG 관리 원칙 및 `rag-builder` 스킬 연동 가이드.
     - `.gitkeep`: 클린 베이스 디렉터리 유지 (세부 타깃 인덱스, 메타데이터, `.gitignore`는 `rag-builder` 스킬이 동적으로 생성/관리).

---

## 자료 분류 및 명명 규칙 준수 지침 (Reference Rules)

- **저장소 영역 격리 및 인덱스 관리 원칙**: 5대 번호형 저장소별 자료 분류 기준과 `README.md` 인덱스 동기화 수칙은 [`.agents/rules/directory_structure.md`](../../rules/directory_structure.md) 규칙을 엄격히 따릅니다.
- **통합 파일명 명명 규칙 및 버전 관리 표준**: 모든 생성 파일의 명명 템플릿(`[포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]`), 포맷태그 매핑, 일련번호 및 리비전 부여 수칙은 [`.agents/rules/file_naming.md`](../../rules/file_naming.md) 규칙을 단일 기준(SSOT)으로 준수합니다.
