---
trigger: always_on
description: 표준 파일 명명 규칙([포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]) 및 버전 관리 가이드라인
---

# 표준 파일 명명 규칙 및 버전 관리 가이드라인 (File Naming & Versioning Rules)

워크스페이스 내 모든 에이전트 산출물(`00_artifacts/`) 및 실무 엔지니어링 자산(`01_input_data/`, `02_output_data/`, `03_scripts/`, `04_rag_database/`)은 대량 파일 생성 시에도 생성 순서와 버전을 명확히 추적할 수 있도록 아래 통합 명명 규칙을 엄격히 준수합니다.

## 1. 표준 파일명 템플릿

```text
[포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]
```

## 2. 7대 필수 준수 수칙

1. **구분자 통일**: 하이픈(`-`)이나 공백 사용을 절대 금지하며, **언더스코어(`_`)만 반드시 사용**합니다.
2. **포맷 태그(`[포맷태그]`)**: 저장소 및 파일 성격에 맞는 지정 식별자를 사용합니다.
   - **`00_artifacts/` (에이전트 프로세스 산출물 - `.md` 전용)**: `plan`, `walkthrough`, `report`, `design`
   - **`01_input_data/01_references/` (작업 지시 및 참조 자료)**: `doc`, `pdf`, `excel`, `csv`, `txt`, `md`
   - **`02_output_data/00_data/` (1단계 수치 데이터 및 정형 스펙 매니페스트)**: `excel`, `csv`, `json`
   - **`02_output_data/01_figure/` (2단계 시각화 및 실행 로그)**: `plot`, `image`, `architecture`, `log`
     > [!IMPORTANT]
     > **아키텍처 다이어그램 이미지 예외 수칙**: 아키텍처 및 프로세스 흐름도 다이어그램을 이미지 파일로 저장할 때는 포맷태그를 반드시 **`architecture`**로 지정합니다 (예: `architecture_001_(system_flow)_261029_rev00.png`).
   - **`02_output_data/02_reports/` (3단계 최종 보고서 및 발표자료)**: `doc`, `ppt`, `pdf`
   - **`03_scripts/python/` (Python 스크립트 전용)**: `py`
   - **`03_scripts/script/` (솔버 배치 및 실행 파일)**: `jou`, `ccl`, `cse`, `bat`, `exe`
   - **`04_rag_database/<target_id>/images/` (RAG 추출 도면/차트 이미지)**: `image`
3. **일련번호(`[일련번호]`)**: 대상 폴더 및 포맷별 **3자리 문서번호/생성 순번(`001`, `002`, ..., `999`)**을 부여하여 생성 순서대로 탐색기 자동 정렬을 지원합니다.
4. **괄호 표기(`([주제명])`)**: 파일명 내의 `[주제명]` 부분은 반드시 소괄호 `(` 와 `)` 로 직접 감싸며, 주제명 내부 단어 구분에도 언더스코어(`_`)를 사용합니다.
5. **날짜 표기(`[YYMMDD]`)**: 6자리 연월일 숫자로 표기합니다 (예: 2026년 10월 29일 ➔ `261029`).
6. **버전 표기(`rev[NN]`)**:
   - **최초 생성 시 무조건 `rev00`을 기본 부여**합니다.
   - 동일 파일/주제의 내용을 수정·갱신할 경우 일련번호는 유지하고 **`rev01`**, **`rev02`** 순으로 번호를 증가시켜 이력을 추적합니다.
7. **원천 자료 보존 예외 (Raw Preservation - `01_input_data/00_received/`)**:
   - 외부 고객사, 시험실, 협력사로부터 수신한 원천 자료(`00_received/`)는 원본 추적성을 위해 원본 파일명을 그대로 유지하는 것을 허용하며, `01_input_data/README.md` 인덱스에 출처와 함께 등록합니다.

## 3. 저장소별 명명 예시

- **구현 계획서 생성**: `00_artifacts/plans/plan_001_(battery_cooling)_261029_rev00.md`
- **구현 계획서 수정**: `00_artifacts/plans/plan_001_(battery_cooling)_261029_rev01.md`
- **작업 완료 보고서**: `00_artifacts/walkthroughs/walkthrough_001_(battery_cooling)_261029_rev00.md`
- **심층 분석 리포트**: `00_artifacts/reports/report_001_(orm_performance)_261029_rev00.md`
- **정형 설계/결과 스펙 (JSON)**: `02_output_data/00_data/json_001_(battery_cooling_spec)_261029_rev00.json`
- **가공 수치 데이터**: `02_output_data/00_data/excel_001_(cell1_discharge_preprocessed)_261029_rev00.xlsx`
- **아키텍처 다이어그램 이미지**: `02_output_data/01_figure/architecture_001_(system_architecture)_261029_rev00.png`
- **일반 플롯/차트 이미지**: `02_output_data/01_figure/plot_001_(temperature_contour)_261029_rev00.png`
- **최종 기술 보고서**: `02_output_data/02_reports/doc_001_(final_analysis_report)_261029_rev00.docx`
- **자동화 스크립트 (Python)**: `03_scripts/python/py_001_(postprocess_parser)_261029_rev00.py`
- **자동화 스크립트 (솔버/배치/실행)**: `03_scripts/script/jou_001_(fluent_batch_solve)_261029_rev00.jou`
