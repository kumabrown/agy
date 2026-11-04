# 프로젝트 Antigravity 사용자 정의 설정 (Project Antigravity Customizations)

이 디렉터리는 팀 전체가 공유하는 Google Antigravity 에이전트용 워크스페이스 레벨 커스터마이징(사용자 정의 설정)을 포함합니다.

## 디렉터리 구조 (Directory Structure)
- **agents/**: YAML 프론트매터(Frontmatter) 및 전용 시스템 프롬프트를 갖춘 열유동 CFD 해석용 영구 커스텀 서브에이전트 (`cfd-manager.md`, `cfd-architect.md`, `cfd-solver.md`, `cfd-reporter.md`).
- **rules/**: 코딩 표준, 아키텍처 제약사항, 파일 명명 규칙 및 산출물 관리 가이드라인.
- **skills/**: 특화된 다단계 워크플로우 (`rag-builder`, `artifact-standard`, `init-env`, `meta-prompting`).
- **hooks.json**: 수명 주기 자동화 훅 (파일 명명 규칙 강제 적용).
- **mcp_config.json**: Model Context Protocol (MCP) 서버 연동 설정.

---

## 등록된 열유동 CFD 서브에이전트 (`agents/`)

| 서브에이전트 (Subagent) | 역할 (Role) | 허용 도구 (Allowed Tools) | 연계 스킬 (Integrated Skills) | 정의 파일 (Definition File) |
| :--- | :--- | :--- | :--- | :--- |
| **`cfd-manager`** | 열유동 프로젝트 총괄 PM & 품질 검수 게이트키퍼 | `read_file`, `write_file`, `edit_file`, `run_command`, `invoke_subagent`, `send_message`, `manage_subagents` | `init-env`<br/>`artifact-standard`<br/>`meta-prompting` | [`agents/cfd-manager.md`](agents/cfd-manager.md) |
| **`cfd-architect`** | 열유동 물리 모델링 & 해석 설계자 | `read_file`, `write_file`, `edit_file`, `run_command` | `rag-builder`<br/>`artifact-standard` | [`agents/cfd-architect.md`](agents/cfd-architect.md) |
| **`cfd-solver`** | Windows 워크스테이션 PyAnsys/솔버 스크립트 개발 & 수렴 분석가 | `read_file`, `write_file`, `edit_file`, `run_command` | `rag-builder` | [`agents/cfd-solver.md`](agents/cfd-solver.md) |
| **`cfd-reporter`** | 정량(Plot)·정성(Contour/Vector/Streamlines) 가시화 & 보고서/PPTX 작성자 | `read_file`, `write_file`, `edit_file`, `run_command` | `artifact-standard`<br/>`rag-builder` | [`agents/cfd-reporter.md`](agents/cfd-reporter.md) |

---

## 3단계 품질 게이트 워크플로우 (3-Stage Quality Gate Workflow, Hub-and-Spoke)

1. **Gate 1 (해석 기획 & 물리 설계)**:
   - `@cfd-architect`가 무차원수($Re, Pr, Gr, Ra$) 계산 및 모델링 설계를 거쳐 `00_artifacts/designs/design_*.md` 작성 $\rightarrow$ `@cfd-manager` 사전 감사(Pass/Feedback).
2. **Gate 2 (Windows 워크스테이션 스크립트 & 수렴성)**:
   - `@cfd-solver`가 Windows 워크스테이션용 PyAnsys(`py_*.py`), Fluent(`jou_*.jou`), CFX(`ccl_*.ccl`)를 `03_scripts/`에 작성.
   - 워크스테이션 계산 후 반입된 로그(`log_*.log`)와 결과(`csv_*.csv`)의 잔차/모니터/열평형 수렴성을 `@cfd-manager`가 감사.
3. **Gate 3 (가시화 & 보고서/PPTX)**:
   - `@cfd-reporter`가 정량 플롯(`plot_*.png`), 정성 유동장(`image_*.png` Contour, Vector, Streamlines), 마크다운 기술 보고서(`report_*.md`) 및 발표자료(`ppt_*.pptx`) 작성 $\rightarrow$ `@cfd-manager` 최종 승인.
