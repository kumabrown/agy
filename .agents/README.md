# 프로젝트 Antigravity 사용자 정의 설정 (Project Antigravity Customizations)

이 디렉터리는 팀 전체가 공유하는 Google Antigravity 에이전트용 워크스페이스 레벨 커스터마이징(사용자 정의 설정)을 포함합니다.

## 디렉터리 구조 (Directory Structure)
- **agents/**: YAML 프론트매터(Frontmatter) 및 전용 시스템 프롬프트를 갖춘 열유동 CFD 해석용 영구 커스텀 서브에이전트 3종 (`cfd-manager.md`, `cfd-solver.md`, `cfd-reporter.md`).
- **templates/**: CFD 물리 도메인별 JSON 스펙 템플릿 프리셋 4종 및 동적 카탈로그 레지스트리 (`template_catalog.json`, `generic`, `cht`, `multiphase`, `radiation_buoyancy`).
- **rules/**: 코딩 표준, 아키텍처 제약사항, 파일 명명 규칙 및 산출물 관리 가이드라인.
- **skills/**: 특화된 다단계 워크플로우 (`rag-builder`, `artifact-standard`, `init-env`, `meta-prompting`).
- **hooks.json**: 수명 주기 자동화 훅 (파일 명명 규칙 `file-naming-guard` 및 JSON SSOT 유효성 검증 `json-spec-guard` 강제 적용).
- **mcp_config.json**: Model Context Protocol (MCP) 서버 연동 설정.

---

## 등록된 열유동 CFD 서브에이전트 (`agents/`)

| 서브에이전트 (Subagent) | 역할 (Role) | 허용 도구 (Allowed Tools) | 연계 스킬 (Integrated Skills) | 정의 파일 (Definition File) |
| :--- | :--- | :--- | :--- | :--- |
| **`cfd-manager`** | 수석 CFD 아키텍트(사양/RAG 분석, 템플릿 카탈로그 기반 해석 전략·물리 모델·대표 무차원수 수립, **JSON SSOT 매니페스트 `json_*_spec_*.json` 생성**) & 프로젝트 총괄 PM / 품질 게이트키퍼 | `read_file`, `write_file`, `edit_file`, `run_command`, `invoke_subagent`, `send_message`, `manage_subagents` | `init-env`<br/>`rag-builder`<br/>`artifact-standard`<br/>`meta-prompting` | [`agents/cfd-manager.md`](agents/cfd-manager.md) |
| **`cfd-solver`** | `json.load()` 바인딩 기반 Windows 워크스테이션 솔버·3D유동장 캡처(`image_*.png`) 통합 스크립트 개발 & 원본 로그(`log_*.log`) 전담 파싱 / 시계열 CSV 추출 및 JSON SSOT(`results_summary`) 갱신 엔지니어 | `read_file`, `write_file`, `edit_file`, `run_command` | `rag-builder` | [`agents/cfd-solver.md`](agents/cfd-solver.md) |
| **`cfd-reporter`** | JSON SSOT 단 1회 로드 및 시계열 CSV(`csv_*_history_*.csv`) 기반 2D 정량 차트(`plot_*.png`) 전담 생성, 3D 유동장(`image_*.png`) 분석 & **단일 최종 마크다운 기술 보고서(`report_*.md`)** 작성자 | `read_file`, `write_file`, `edit_file`, `run_command` | `artifact-standard` | [`agents/cfd-reporter.md`](agents/cfd-reporter.md) |

---

## JSON SSOT 기반 단방향 파이프라인 및 품질 게이트 워크플로우

1. **Phase 1 (사양 이해, 물리 설계 & JSON SSOT 생성 — `@cfd-manager` 자체 수행)**:
   - `@cfd-manager`가 `01_input_data/` 및 RAG를 전담 분석하여 프로젝트 맥락과 목표 성능 스펙($T_{\text{limit}}, \Delta P_{\text{max}}$)을 파악.
   - `template_catalog.json`을 검색하여 최적 프리셋(CHT, 다상, 복사 또는 generic)을 선택하고, 대표 무차원수($Re, Pr, Gr, Ra, We, Fr$ 등)를 계산하여 정형 **JSON 스펙 매니페스트(`02_output_data/00_data/json_[SEQ]_([topic]_spec)_[YYMMDD]_rev00.json`, SSOT)** 생성 (`PreToolUse` 훅 `validate_json_spec.py`가 스키마를 실시간 검증).
2. **Phase 2 / Gate 1 (워크스테이션 솔버·3D캡처 스크립트 & 로그 파싱 검수 — `@cfd-solver`)**:
   - `@cfd-solver`가 `json_*_spec_*.json`을 파이썬 `json.load()`로 직접 바인딩하여 솔버 실행 및 3D 유동장(`image_*.png`) 자동 캡처 통합 스크립트(`03_scripts/python/py_*.py`, `03_scripts/script/jou_*.jou`, `ccl_*.ccl`) 작성.
   - 워크스테이션 계산 후 반입된 원본 로그(`log_*.log`)를 `@cfd-solver`가 전담 파싱하여 ① 수렴 이력 시계열 CSV(`02_output_data/00_data/csv_*_history_*.csv`)를 저장하고, ② 최종 수렴 수치와 자산 경로를 `json_*_spec_*.json`의 `"results_summary"` 블록에 업데이트 $\rightarrow$ `@cfd-manager` Gate 1 감사(Pass/Reject).
3. **Phase 3 / Gate 2 (2D 시각화 차트 & 단일 최종 기술 보고서 검수 — `@cfd-reporter`)**:
   - `@cfd-reporter`는 컨텍스트 보호를 위해 `csv_*_history_*.csv`를 `read_file`로 직접 열지 않고(Python 스크립트로만 플로팅), 오직 `json_*_spec_*.json` 파일 하나만 로드하여 설계 조건과 수렴 결과를 한 번에 파악.
   - 2D 정량 차트(`02_output_data/01_figure/plot_*.png`) 생성 및 반입된 3D 유동장(`image_*.png`) 해석 결과를 결합하여 프로젝트의 **유일한 완결형 마크다운 문서인 최종 기술 보고서(`00_artifacts/reports/report_*.md`)** 작성 $\rightarrow$ `@cfd-manager` Gate 2 최종 승인.
   - 신규 물리 도메인인 경우 `template_cfd_spec_<domain>.json` 저장 및 `template_catalog.json` 자동 등록(Self-Evolution).
