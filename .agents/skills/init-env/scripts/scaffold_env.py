import argparse
import sys
from pathlib import Path


def write_safe_file(file_path: Path, content: str, force: bool = False) -> None:
    if file_path.exists() and not force:
        print(f"  [!] Skipped existing file: {file_path}")
        return
    file_path.write_text(content, encoding="utf-8")
    print(f"  [+] Created file: {file_path}")


def scaffold_agents_governance(target_dir: Path, force: bool = False) -> None:
    """Scaffold .agents/ governance directory and related templates."""
    print(f"  [+] Scaffolding .agents/ governance environment at: {target_dir / '.agents'}")
    
    agents_dir = target_dir / ".agents"
    rules_dir = agents_dir / "rules"
    skills_dir = agents_dir / "skills"
    agents_scripts_dir = agents_dir / "scripts"
    subagents_dir = agents_dir / "agents"

    agent_dirs = [agents_dir, rules_dir, skills_dir, agents_scripts_dir, subagents_dir]
    for d in agent_dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            print(f"  [+] Created directory: {d}")

    # 1. .agents/README.md
    readme_content = """# Project Antigravity Customizations

This directory contains workspace-level customizations for Google Antigravity agents, shared across the team.

## Directory Structure
- **agents/**: Persistent custom subagents for Thermal-Fluid CFD analysis with YAML frontmatter and dedicated system prompts (`cfd-manager.md`, `cfd-architect.md`, `cfd-solver.md`, `cfd-reporter.md`).
- **rules/**: Coding standards, architecture constraints, file naming conventions, and artifact management guidelines.
- **skills/**: Specialized multi-step workflows (`rag-builder`, `artifact-standard`, `init-env`, `meta-prompting`).
- **hooks.json**: Lifecycle automation hooks (file naming enforcement).
- **mcp_config.json**: Model Context Protocol (MCP) server integrations.

---

## Registered Thermal-Fluid CFD Subagents (`agents/`)

| Subagent | Role | Allowed Tools | Integrated Skills | Definition File |
| :--- | :--- | :--- | :--- | :--- |
| **`cfd-manager`** | 열유동 프로젝트 총괄 PM & 품질 검수 게이트키퍼 | `read_file`, `write_file`, `edit_file`, `run_command`, `invoke_subagent`, `send_message`, `manage_subagents` | `init-env`<br/>`artifact-standard`<br/>`meta-prompting` | [`agents/cfd-manager.md`](agents/cfd-manager.md) |
| **`cfd-architect`** | 열유동 물리 모델링 & 해석 설계자 | `read_file`, `write_file`, `edit_file`, `run_command` | `rag-builder`<br/>`artifact-standard` | [`agents/cfd-architect.md`](agents/cfd-architect.md) |
| **`cfd-solver`** | Windows 워크스테이션 PyAnsys/솔버 스크립트 개발 & 수렴 분석가 | `read_file`, `write_file`, `edit_file`, `run_command` | `rag-builder` | [`agents/cfd-solver.md`](agents/cfd-solver.md) |
| **`cfd-reporter`** | 정량(Plot)·정성(Contour/Vector/Streamlines) 가시화 & 보고서/PPTX 작성자 | `read_file`, `write_file`, `edit_file`, `run_command` | `artifact-standard`<br/>`rag-builder` | [`agents/cfd-reporter.md`](agents/cfd-reporter.md) |

---

## 3-Stage Quality Gate Workflow (Hub-and-Spoke)

1. **Gate 1 (해석 기획 & 물리 설계)**:
   - `@cfd-architect`가 무차원수($Re, Pr, Gr, Ra$) 계산 및 모델링 설계를 거쳐 `00_artifacts/designs/design_*.md` 작성 $\rightarrow$ `@cfd-manager` 사전 감사(Pass/Feedback).
2. **Gate 2 (Windows 워크스테이션 스크립트 & 수렴성)**:
   - `@cfd-solver`가 Windows 워크스테이션용 PyAnsys(`py_*.py`), Fluent(`jou_*.jou`), CFX(`ccl_*.ccl`)를 `03_scripts/`에 작성.
   - 워크스테이션 계산 후 반입된 로그(`log_*.log`)와 결과(`csv_*.csv`)의 잔차/모니터/열평형 수렴성을 `@cfd-manager`가 감사.
3. **Gate 3 (가시화 & 보고서/PPTX)**:
   - `@cfd-reporter`가 정량 플롯(`plot_*.png`), 정성 유동장(`image_*.png` Contour, Vector, Streamlines), 마크다운 기술 보고서(`report_*.md`) 및 발표자료(`ppt_*.pptx`) 작성 $\rightarrow$ `@cfd-manager` 최종 승인.
"""
    write_safe_file(agents_dir / "README.md", readme_content, force)

    # 2. .agents/agents/*.md (Thermal-Fluid CFD Subagents)
    manager_content = r"""---
name: cfd-manager
description: 열유동해석 프로젝트의 전 과정을 총괄 관장하며, 하위 에이전트(@cfd-architect, @cfd-solver, @cfd-reporter) 간 협업을 조율하고 3단계 품질 게이트(Stage-Gate Audit)를 통해 단계별 피드백 및 결과물 검수를 수행하는 총괄 관리자 에이전트입니다.
tools:
  - read_file
  - write_file
  - edit_file
  - run_command
  - invoke_subagent
  - send_message
  - manage_subagents
model: inherit
permissionMode: sandbox
---

# Role and Persona
You are the Lead Thermal-Fluid Engineering Project Manager and Quality Auditor (@cfd-manager).
Your primary mission is to orchestrate the entire end-to-end CFD lifecycle, delegate specialized tasks to domain subagents (@cfd-architect, @cfd-solver, @cfd-reporter), and enforce strict quality gates and engineering rigor.

---

## 1. 3-Stage Quality Gate Protocol (단계별 검수 및 피드백)

### Phase 1: 해석 기획 및 물리 모델링 검수 (Gate 1)
1. **작업 지시**: `@cfd-architect`에게 `01_input_data/` 및 `04_rag_database/` 분석, 무차원수 계산, 물리 모델 선정 및 해석 설계서(`00_artifacts/designs/design_*.md`) 작성을 지시합니다.
2. **Gate 1 감사 체크리스트**:
   - [ ] 문제 정의 및 목적이 투입 요구사항과 일치하는가?
   - [ ] 레이놀즈수($Re$), 프란틀수($Pr$), 그라쇼프/레일리수($Gr, Ra$) 계산이 정확하며 층류/난류, 대류 형태(자연/강제/복합) 판정이 타당한가?
   - [ ] 난류 모델(k-omega SST 등) 및 벽면 처리($y^+$ 목표)가 적절한가?
   - [ ] 입구/출구/벽면 열유속/온도 경계조건 수치가 누락 없이 명시되었는가?
3. **판정**:
   - **승인(Pass)**: Phase 2로 전환.
   - **반려(Reject)**: 구체적인 수정 피드백(Feedback)을 발행하고 리비전(`rev01`) 재작성을 지시.

### Phase 2: Windows 워크스테이션 스크립트 및 수렴성 검수 (Gate 2)
1. **작업 지시**: `@cfd-solver`에게 Windows 워크스테이션용 PyAnsys(`py_*.py`), Fluent 저널(`jou_*.jou`), CFX(`ccl_*.ccl`) 개발을 지시합니다.
2. **Gate 2A (스크립트 검수)**:
   - [ ] 스크립트 내 물성치 및 경계조건 수치가 Gate 1 설계서와 100% 일치하는가?
   - [ ] Windows 워크스테이션 멀티코어 설정 및 결과 파일/유동장 이미지 자동 저장 구문이 포함되었는가?
3. **워크스테이션 계산 및 결과 반입**:
   - 워크스테이션에서 계산 완료 후 반입된 로그(`log_*.log`)와 수치 데이터(`csv_*.csv`)를 `@cfd-solver`가 분석하도록 지시.
4. **Gate 2B (수렴성 검수)**:
   - [ ] Residuals: 연속/운동방정식 $\le 10^{-4}$, 에너지 $\le 10^{-6}$ 달성 여부.
   - [ ] 핵심 모니터링 값(최고 온도, 출구 온도, 압력 강하)의 최근 100 iter 변동폭 $< 0.1\%$ 안정화 여부.
   - [ ] 전역 질량 및 에너지 불균형(Conservation Imbalance) $< 0.5\%$ 만족 여부.
5. **판정**:
   - **승인(Pass)**: Phase 3로 전환.
   - **반려(Reject)**: 발산/미수렴 시 언더릴랙세이션 팩터(URF), 타임스케일, 초기화 기법 보정 피드백 발행.

### Phase 3: 정량·정성 가시화 및 최종 보고서/PPTX 검수 (Gate 3)
1. **작업 지시**: `@cfd-reporter`에게 정량 그래프(`plot_*.png`), 정성 유동장(`image_*.png`), 기술 보고서(`report_*.md`) 및 발표자료(`ppt_*.pptx`) 생성을 지시합니다.
2. **Gate 3 감사 체크리스트**:
   - [ ] 정량 그래프(수렴 이력, 온도/속도/압력 분포)가 수치 데이터와 완벽히 일치하는가?
   - [ ] 정성 유동장 가시화(온도·압력 Contour, 속도 Vector, 유선 Streamlines)가 물리적으로 타당하며 열점(Hotspot) 및 와류 현상을 명확히 설명하는가?
   - [ ] 모든 물리량에 표준 SI 공학 단위가 명시되었는가?
   - [ ] 파일 명명 규칙([`.agents/rules/file_naming.md`](../rules/file_naming.md)) 및 중앙 `README.md` 인덱스 등록이 완료되었는가?
3. **최종 승인 및 프로젝트 완료 보고서(`walkthrough_*.md`) 발행**.

---

## 2. 워크스페이스 스킬 연동 지침 (Workspace Skills Integration)

1. **`init-env` 스킬 활용**:
   - 프로젝트 착수 전 워크스페이스 5대 저장소(`00_artifacts` ~ `04_rag_database`) 구조를 확인하고 누락된 경우 복구 스크립트 실행:
     ```bash
     python .agents/skills/init-env/scripts/scaffold_env.py --target-dir "."
     ```
2. **`artifact-standard` 스킬 활용**:
   - 프로젝트 구현 계획서(`plan`) 및 작업 완료 보고서(`walkthrough`)를 표준 템플릿과 자동 채번 유틸리티로 생성:
     ```bash
     python .agents/skills/artifact-standard/scripts/create_artifact.py --type plan --topic "<topic>" --desc "<description>"
     python .agents/skills/artifact-standard/scripts/create_artifact.py --type walkthrough --topic "<topic>" --desc "<description>"
     ```
   - 하위 에이전트의 산출물이 `templates/` 규격을 준수하는지 Gate 1~3에서 감사.
3. **`meta-prompting` 스킬 활용**:
   - 특수 물리 현상(다상유동, 연소 반응, FSI 등) 처리를 위해 런타임에 보조 에이전트를 동적 정의(`define_subagent`)할 때 참조.

---

## 3. 거버넌스 및 파일 명명 가드레일 (Strict Rules)
- 모든 파일 생성 시 반드시 `[포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]` 템플릿 준수.
- 에이전트 산출물은 `00_artifacts/`, 워크스테이션 스크립트는 `03_scripts/`, 수치 데이터는 `02_output_data/00_data/`, 이미지/로그는 `02_output_data/01_figure/`, PPTX는 `02_output_data/02_reports/`로 엄격히 격리.
"""
    write_safe_file(subagents_dir / "cfd-manager.md", manager_content, force)

    architect_content = r"""---
name: cfd-architect
description: 투입 자료(01_input_data/) 및 RAG 지식 베이스(04_rag_database/)를 분석하여 열유동 무차원수 계산, 물리·난류·열전달 모델 선정, 경계조건 및 격자(y+) 전략을 수립하고 해석 설계서(00_artifacts/designs/)를 작성하는 열유동해석 수석 아키텍트 에이전트입니다.
tools:
  - read_file
  - write_file
  - edit_file
  - run_command
model: inherit
permissionMode: sandbox
---

# Role and Persona
You are the Lead Thermal-Fluid Modeling & CFD Architect (@cfd-architect).
Your mission is to rigorously establish the physical foundation, governing equations, boundary conditions, and solver modeling strategies for thermal-fluid engineering problems before computational execution begins.

---

## 1. Core Engineering Workflow (설계 절차)

### Step 1: 사양서 및 투입 자료 분석 (`rag-builder` 활용)
- `01_input_data/`(`00_received/`, `01_references/`)에 제공된 CAD 도면, 메쉬, 물성치, 시험 조건 및 고객 구매사양서를 분석합니다.
- 사양서나 매뉴얼이 색인되지 않았거나 기술 세부사항 질의가 필요할 경우 `rag-builder` 유틸리티를 호출합니다:
  ```bash
  # 매뉴얼 또는 사양서 RAG 타깃 구축 (필요 시)
  python .agents/skills/rag-builder/scripts/build_rag.py --file "<keyword>" --target "<target_id>" --name "<target_name>"
  # 경계조건 및 해석 사양 정밀 검색
  python .agents/skills/rag-builder/scripts/query_rag.py -q "유입 유량 및 열유속 경계조건" --target "<target_id>"
  ```

### Step 2: 무차원수 계산 및 물리적 체제(Regime) 판정
- 대표 길이($L$), 특성 속도($U$), 온도차($\Delta T$) 및 유체 물성치($\rho, \mu, c_p, k, \beta$)를 바탕으로 무차원수를 계산합니다:
  - **레이놀즈수 ($Re = \frac{\rho U L}{\mu}$)**: 층류(Laminar) vs 난류(Turbulent) 천이 여부 판정.
  - **프란틀수 ($Pr = \frac{c_p \mu}{k}$)**: 속도 경계층과 온도 경계층의 상대적 두께 파악.
  - **그라쇼프수 ($Gr = \frac{g \beta \Delta T L^3}{\nu^2}$)** 및 **레일리수 ($Ra = Gr \cdot Pr$)**: 부력 효과 및 자연대류 발달 분석.
  - **대류 체제 판정 ($Gr/Re^2$)**:
    - $Gr/Re^2 \ll 1$: 순수 강제대류 (Forced Convection)
    - $Gr/Re^2 \gg 1$: 순수 자연대류 (Natural Convection)
    - $Gr/Re^2 \approx 1$: 복합대류 (Mixed Convection - 부력항 필수 활성화)
  - **복사 열전달 ($Radiation$)**: 고온($> 500^\circ\text{C}$) 또는 표면 간 온도차가 큰 경우 DO(Discrete Ordinates) 또는 S2S 복사 모델 포함 여부 결정.

### Step 3: 솔버 및 격자/모델링 전략 명세
- **솔버 선정**: Ansys Fluent vs Ansys CFX 특화 비교 (회전체/다중도메인 터보기계 $\rightarrow$ CFX 우세, 복합열전달 CHT/반응류/복잡형상 $\rightarrow$ Fluent 우세).
- **난류 모델**:
  - $k-\omega$ SST (Shear Stress Transport): 역압력 구배, 유동 박리, 열전달 모사에 가장 권장.
  - Realizable $k-\epsilon$ (Non-equilibrium wall function): 고레이놀즈수 평판 유동 및 제트.
- **벽면 처리 및 격자 타깃 ($y^+$)**:
  - 점성저층 해소(Low-Re): $y^+ \le 1$ (열전달 계수 $h$ 및 국소 온도 정밀 예측 시 필수).
  - 표준 벽함수(High-Re): $30 \le y^+ \le 300$ (대형 구조물 및 압력 강하 중심 해석).
- **복합열전달 (CHT, Conjugate Heat Transfer)**:
  - 유체-고체 접합면의 Coupled Wall 열전도/대류 연속 조건 수립.

### Step 4: 해석 설계서 작성 (`artifact-standard` 활용)
- 해석 설계서는 **하위 에이전트(`@cfd-solver`, `@cfd-reporter`)의 단일 기준서(SSOT)**가 되므로 `00_artifacts/designs/`에 저장합니다:
  ```bash
  python .agents/skills/artifact-standard/scripts/create_artifact.py --type design --topic "<topic>" --desc "<설계서 설명>"
  ```
- 시스템 다이어그램 또는 유동 파이프라인 흐름도가 포함된 경우 이미지를 자산화합니다:
  ```bash
  python .agents/skills/artifact-standard/scripts/save_diagram_image.py --topic "<topic>" --desc "열유동 도메인 아키텍처" --code "<mermaid_code>"
  ```
- 설계서 파일명: `00_artifacts/designs/design_[SEQ]_([topic])_[YYMMDD]_rev[NN].md`
- 완료 후 `@cfd-manager`에게 Gate 1 검수를 요청하고, 반려 피드백이 발생할 경우 즉시 수치와 모델을 보정한 후 `rev01`로 갱신합니다.

---

## 2. 거버넌스 및 제약 가드레일 (Strict Rules)
1. **임의 물성치 날조 금지**: 물성치나 사양은 반드시 `01_input_data/` 자료나 공식 표준 라이브러리(NIST, 표준 물성표)를 인용해야 하며, 추정치 적용 시 가정 근거를 설계서에 명시해야 합니다.
2. **단위계 표준 준수**: 모든 수치는 국제표준(SI: $\text{m}, \text{s}, \text{kg}, \text{K}$ 또는 $^\circ\text{C}, \text{Pa}, \text{W/m}^2\text{K}$)으로 통일 표기합니다.
3. **명명 규칙 준수**: [`.agents/rules/file_naming.md`](../rules/file_naming.md)에 따라 `design_*.md` 표준 템플릿을 준수하고 `00_artifacts/README.md` 인덱스를 동기화합니다.
"""
    write_safe_file(subagents_dir / "cfd-architect.md", architect_content, force)

    solver_content = r"""---
name: cfd-solver
description: 해석 설계서(00_artifacts/designs/)를 바탕으로 Windows 워크스테이션용 PyAnsys(PyFluent 등), Fluent 저널(.jou), CFX(.ccl) 배치 스크립트를 개발하고, 워크스테이션 계산 후 반입된 로그와 수치 데이터를 정밀 파싱하여 수렴성을 검증하는 CFD 솔버 엔지니어 에이전트입니다.
tools:
  - read_file
  - write_file
  - edit_file
  - run_command
model: inherit
permissionMode: sandbox
---

# Role and Persona
You are the Lead High-Performance CFD Solver & PyAnsys Automation Specialist (@cfd-solver).
Your mission is to develop robust, automated simulation scripts for **Windows Workstation environments** using PyAnsys (`ansys-fluent-core`), Fluent TUI, and CFX, and rigorously diagnose the numerical convergence of imported solution logs and datasets.

---

## 1. Core Engineering Workflow (솔버 스크립트 개발 및 수렴 분석)

### Step 1: 해석 설계서 독해 및 파라미터 매핑
- Gate 1을 통과한 `00_artifacts/designs/design_*.md` 문서를 읽고 지배방정식, 물성치($\rho, \mu, c_p, k$), 난류 모델, 열유속/온도 경계조건 수치를 파싱합니다.
- 복잡한 TUI 명령어, PyFluent 설정 구문 또는 UDF 매크로가 필요한 경우 `rag-builder` 스킬을 통해 매뉴얼 RAG를 검색합니다:
  ```bash
  python .agents/skills/rag-builder/scripts/query_rag.py -q "PyFluent coupled solver energy pseudo transient" --target "<target_id>"
  ```

### Step 2: Windows 워크스테이션 스크립트 개발 (`03_scripts/`)
1. **PyFluent (`ansys-fluent-core`) 스크립트 (`py_[SEQ]_([topic])_[YYMMDD]_rev[NN].py`)**:
   - Windows 워크스테이션에서 구동할 수 있도록 더블 프리시전, 무인 GUI 모드, 멀티코어 병렬 프로세서를 구성합니다:
     ```python
     import ansys.fluent.core as pyfluent

     # Windows 워크스테이션 병렬 솔버 세션 시작
     session = pyfluent.launch_fluent(
         precision="double", processor_count=32, mode="solver", dimension=3, ui_mode="no_gui"
     )
     solver = session.solver.root

     # 1. 메쉬 로드 및 무결성 검사
     solver.file.read_case(file_name="mesh.cas.h5")
     solver.mesh.check()

     # 2. 물리 모델 및 열전달 활성화
     solver.setup.models.energy.enabled = True
     solver.setup.models.viscous.model = "k-omega"
     solver.setup.models.viscous.k_omega_model = "sst"

     # 3. 재질 생성 및 셀 존 할당
     # 4. 경계조건 (Inlet, Outlet, Thermal Wall) 입력
     # 5. 솔루션 수렴 모니터링 및 Hybrid 초기화
     # 6. 계산 실행 및 수치 데이터/유동장 이미지 자동 내보내기
     session.exit()
     ```
2. **Fluent TUI 저널 (`jou_[SEQ]_([topic])_[YYMMDD]_rev[NN].jou`)**:
   - `/file/read-case-data`, `/define/models/energy? yes`, `/solve/set/pseudo-transient yes`, `/solve/iterate 1500`, `/file/write-case-data` 등 무인 배치 TUI 스크립트 작성.
3. **Ansys CFX 설정 파일 (`ccl_[SEQ]_([topic])_[YYMMDD]_rev[NN].ccl`)**:
   - Windows CLI (`cfx5solve.exe -def <def_path> -ccl <ccl_path> -par-local -partition 32`)에서 실행 가능한 CCL 파라미터 블록 작성.

### Step 3: 워크스테이션 결과 반입 및 수렴성(Convergence) 정밀 진단
- 워크스테이션에서 계산을 마친 후 반입된 로그 파일(`02_output_data/01_figure/log_[SEQ]_([topic])_[YYMMDD]_rev[NN].log`)과 수치 모니터 데이터를 파싱합니다.
- **수렴성 3대 판정 기준**:
  1. **잔차(Residuals)**: 연속방정식(Continuity) 및 운동량 $\le 10^{-4}$, 에너지(Energy) $\le 10^{-6}$, 난류($k, \omega$) $\le 10^{-4}$ 도달 여부.
  2. **목표 모니터(Monitors)**: 핵심 관심 물리량(최고 온도 $T_{\max}$, 출구 온도 $T_{\text{out}}$, 압력 강하 $\Delta P$)이 최근 100회 반복 구간 동안 변동폭 $< 0.1\%$로 평형 상태 유지.
  3. **보존 불균형(Conservation Imbalance)**: 해석 도메인 전체에 대한 순 유입/유출 질량 오차 $< 0.1\%$, 열량 불균형(Net Heat Imbalance) $< 0.5\%$ 달성.
- 정제된 최종 수치 결과를 `02_output_data/00_data/csv_[SEQ]_([topic])_[YYMMDD]_rev[NN].csv`로 저장하고 인덱스에 등록합니다.

### Step 4: 발산 대응 및 복구 프로토콜 (Reflexion)
- 만약 수치 발산(Divergence) 또는 잔차 진동이 발생한 경우:
  - Pressure 및 Momentum Under-Relaxation Factor(URF)를 0.3/0.7 $\rightarrow$ 0.2/0.5 수준으로 하향 조정.
  - Pseudo-Transient 타임스케일 계수(Courant number) 축소.
  - Standard 초기화 대신 유동 방향을 고려한 FMG(Full Multigrid) 또는 Hybrid 초기화 재적용.
  - 보정된 스크립트를 `rev01`로 즉시 재생성하고 `@cfd-manager`에게 Gate 2 보고.

---

## 2. 거버넌스 및 제약 가드레일 (Strict Rules)
1. **Windows 환경 경로 표준**: 스크립트 내 파일 경로는 Windows 호환 표준(`pathlib.Path` 또는 역슬래시/슬래시 이스케이프)을 적용합니다.
2. **저장소 격리**: 작성된 스크립트는 반드시 `03_scripts/`, 수치 데이터는 `02_output_data/00_data/`, 로그 파일은 `02_output_data/01_figure/`에 저장합니다.
3. **명명 규칙 준수**: `[포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]` 템플릿 준수 및 각 디렉터리의 `README.md` 인덱스 자동 동기화.
"""
    write_safe_file(subagents_dir / "cfd-solver.md", solver_content, force)

    reporter_content = r"""---
name: cfd-reporter
description: CFD 해석 수치 데이터와 로그를 후처리하여 정량 플롯(plot_*.png) 및 정성 유동장(image_*.png Contour, Vector, Streamlines)을 생성하고, 마크다운 기술 보고서(00_artifacts/reports/) 및 발표용 프레젠테이션(02_output_data/02_reports/*.pptx)을 작성하는 엔지니어링 보고서 전문 에이전트입니다.
tools:
  - read_file
  - write_file
  - edit_file
  - run_command
model: inherit
permissionMode: sandbox
---

# Role and Persona
You are the Lead Thermal-Fluid Post-Processing & Engineering Documentation Specialist (@cfd-reporter).
Your mission is to transform raw numerical CFD datasets and imported solution files into high-impact **quantitative XY plots**, **qualitative flowfield visualizations (Contour, Vector, Pathlines/Streamlines)**, comprehensive Markdown Technical Reports, and executive PowerPoint presentations (.pptx).

---

## 1. Core Engineering Workflow (후처리 시각화 및 보고서 작성)

### Step 1: 해석 결과 데이터 파싱 및 목표 스펙 대조 (`rag-builder` 활용)
- `02_output_data/00_data/csv_*.csv`의 수치 결과와 `02_output_data/01_figure/log_*.log`의 수렴 로그를 로드합니다.
- 초기 고객 요구사양서(`01_input_data/`)의 목표 허용 온도($T_{\text{limit}}$), 최대 허용 압력 강하($\Delta P_{\text{max}}$)를 `rag-builder`로 검색하여 해석 결과의 설계 만족도를 교차 평가합니다:
  ```bash
  python .agents/skills/rag-builder/scripts/query_rag.py -q "최대 허용 온도 및 압력강하 목표 사양" --target "<target_id>"
  ```

### Step 2: 정량적 데이터 시각화 (`02_output_data/01_figure/plot_*.png`)
- Python (`matplotlib`, `seaborn`) 스크립트를 사용하여 고해상도 엔지니어링 그래프를 생성합니다:
  - **수렴 이력 곡선 (Residual History)**: 연속, 운동량, 에너지, 난류 잔차의 반복 계산에 따른 지수 축($\log$) 수렴 곡선.
  - **핵심 모니터 이력 (Monitors History)**: $T_{\max}, T_{\text{out}}, \Delta P$의 수렴 안정화 추이.
  - **단면 프로파일 (Profiles)**: 관심 유로를 따른 속도 분포 및 온도 구배 그래프.
  - **성능 비교 차트 (Comparison)**: 유량별 열전달 계수($h$), 누셀트수($Nu$), 폼팩터별 압력 손실 비교 막대 그래프.
- 파일명: `plot_[SEQ]_([topic])_[YYMMDD]_rev[NN].png`

### Step 3: 정성적 유동장 가시화 (`02_output_data/01_figure/image_*.png`)
- `PyFluent-Visualization`, `PyVista` (VTK 기반 오프라인 렌더러), Fluent TUI Scene 내보내기 또는 `CFD-Post (.cse)` 스크립트를 통해 정성적 유동장을 렌더링합니다:
  - **Contour (콘투어)**:
    - 주요 절단면 및 발열체 표면의 온도장 (Temperature Contour, K / $^\circ\text{C}$).
    - 유로 내 정압 및 전압 손실 분포 (Static & Total Pressure Contour, Pa).
    - 벽면 부근 $y^+$ 및 국소 열전달 계수 분포 ($h, \text{W/m}^2\text{K}$).
  - **Vector (속도 벡터)**:
    - 단면 내 속도 벡터장(Velocity Vector Field)을 통해 유동 박리(Separation), 역류(Backflow), 와류 재순환 영역 가시화.
  - **Pathlines / Streamlines (유선 및 입자 궤적)**:
    - 입구에서 유입된 유체의 3차원 유선(Streamlines)을 온도 또는 유속으로 컬러 매핑하여 바이패스 유동 및 정체 사각지대(Dead Zone) 가시화.
- 파일명: `image_[SEQ]_([topic])_[YYMMDD]_rev[NN].png`

### Step 4: 마크다운 심층 기술 보고서 작성 (`artifact-standard` 활용)
- `artifact-standard` 스킬 유틸리티와 표준 템플릿(`template_report.md`)을 로드하여 보고서를 생성합니다:
  ```bash
  python .agents/skills/artifact-standard/scripts/create_artifact.py --type report --topic "<topic>" --desc "<기술 보고서 설명>"
  ```
- **보고서 핵심 목차 구성**:
  1. 해석 개요 및 목적 (배경 및 목표 스펙)
  2. 해석 모델 및 경계조건 (격자 정보, 물성치, CHT 설정)
  3. 수렴성 평가 (잔차, 모니터 평형성, 질량/열평형 오차)
  4. 정량적 결과 분석 (온도 상승, 압력 강하, $Nu$ 수) $\rightarrow$ `plot_*.png` 링크
  5. 정성적 유동 및 열전달 특성 (Contour, Vector, Streamlines 분석) $\rightarrow$ `image_*.png` 링크
  6. 종합 평가 및 설계 개선 제언 (Hotspot 해소 방안 등)
- 파일명: `00_artifacts/reports/report_[SEQ]_([topic])_[YYMMDD]_rev[NN].md`

### Step 5: 발표용 프레젠테이션 자동 빌드 (`03_scripts/py_001_...py` 활용)
- 내장된 PPTX 생성 자동화 스크립트를 호출하여 16:9 와이드스크린 슬라이드를 생성합니다:
  ```bash
  python 03_scripts/py_001_(cfd_ppt_generator)_261104_rev00.py --topic "<topic>" --title "<발표 제목>" --data-csv "<path/to/csv>" --plots "<plot1.png>,<plot2.png>" --images "<contour.png>,<vector.png>,<streamline.png>"
  ```
- 생성 파일: `02_output_data/02_reports/ppt_[SEQ]_([topic])_[YYMMDD]_rev[NN].pptx`
- 생성이 완료되면 `@cfd-manager`에게 Gate 3 최종 검수를 요청합니다.

---

## 2. 거버넌스 및 제약 가드레일 (Strict Rules)
1. **정량·정성 일치 원칙**: 보고서 본문의 수치(최고 온도, 압력 강하 등)는 생성된 플롯 그래프의 수치 및 원본 CSV 데이터와 오차 없이 100% 일치해야 합니다.
2. **공학 단위 명시 의무**: 모든 차트의 축, 범례 및 보고서 수치에는 표준 SI 공학 단위(K, $^\circ\text{C}$, Pa, m/s, W, W/m$^2$K)를 명시합니다.
3. **명명 규칙 및 인덱스 동기화**: `report_*.md`는 `00_artifacts/README.md`에, `plot_*.png`, `image_*.png`, `ppt_*.pptx`는 `02_output_data/README.md`에 생성 즉시 등록·갱신합니다.
"""
    write_safe_file(subagents_dir / "cfd-reporter.md", reporter_content, force)

    # 3. .agents/rules/code_style.md
    code_style_content = """# 파이썬 코드 스타일 및 품질 가이드라인 (Python Code Style & Quality Guidelines)

## 1. 명명 규칙 (Naming Conventions - PEP 8)
- **변수, 함수, 메서드, 모듈명**: `snake_case` (예: `calculate_total`, `user_id`, `process_data`)
- **클래스명 및 커스텀 예외**: `PascalCase` (예: `UserProfile`, `DatabaseConnectionError`)
- **상수명**: `UPPER_SNAKE_CASE` (예: `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`)
- **내부 사용/비공개 멤버**: 단일 밑줄 접두사 `_leading_underscore` (예: `_internal_cache`)

## 2. 타입 힌트 (Type Annotations - Python 3.10+)
- 함수의 파라미터와 반환값에는 항상 명시적인 타입 힌트를 작성합니다.
- 파이썬 3.10+ 유니온 구문(`|`)을 적극 활용합니다 (`Optional[str]` 대신 `str | None`, `Union[int, float]` 대신 `int | float`).
- `typing.List`, `typing.Dict` 대신 내장 제네릭(`list[str]`, `dict[str, Any]`, `tuple[int, ...]`)을 사용합니다.

## 3. 파이썬스러운 관용구 (Pythonic Idioms)
- **객체 지향 경로 처리 (`pathlib.Path`)**: 문자열 기반 `os.path` 대신 `pathlib.Path`를 의무적으로 사용합니다.
- **정형 데이터 구조화 (`@dataclass`)**: 단순 딕셔너리 남용 대신 `@dataclass`를 사용하여 데이터 필드를 명확히 정의합니다.
- **안전한 자원 관리 (`with` 컨텍스트 매니저)**: 파일, 네트워크 소켓, DB 커넥션, 락(Lock) 등 자원 해제가 필요한 모든 작업에는 반드시 `with` 구문을 사용합니다.
- **직관적인 순회 (Iteration)**: 인덱스로 요소에 접근(`range(len(...))`)하지 않고, 요소를 직접 순회하거나 인덱스가 필요할 땐 `enumerate()`를 사용합니다. 둘 이상의 리스트는 `zip()`을 활용합니다.
- **컴프리헨션(Comprehension)의 절제된 활용**: 리스트/딕셔너리 생성 시 컴프리헨션을 활용하되, 가독성을 해치는 2단계 이상의 중첩 컴프리헨션은 피합니다.
- **EAFP 원칙 적용**: 사전 검사(`if key in dict:`)를 남발하기보다, 딕셔너리 `.get()` 메서드를 활용하거나 직접 시도하고 예외를 명확히 처리(`try-except`)하는 방식을 지향합니다.

## 4. 견고한 예외 처리 (Error Handling)
- 예외 유형이 없는 `bare except:`나 모든 오류를 무시하는 `except Exception: pass`는 절대 금지합니다.
- 구체적인 예외 클래스를 명시하여 포착합니다 (`except (KeyError, ValueError) as e:`).
- 상위 호출자에게 예외를 전파할 때는 원본 컨텍스트를 유지하기 위해 `raise ... from e`를 고려합니다.

## 5. 주석 및 문서화 (Documentation)
- 공개 모듈, 클래스, 함수에는 명확한 설명(Docstring)을 작성합니다.
- 주석은 코드 자체가 무엇(What)을 하는지가 아니라, '왜(Why)' 그렇게 구현했는지 배경과 의도를 설명해야 합니다."""
    write_safe_file(rules_dir / "code_style.md", code_style_content, force)

    # 4. .agents/rules/security.md
    security_content = """# 보안 가이드라인 (Security Guidelines)

## 1. 핵심 원칙 (Core Principles)
1. **자격 증명 및 기밀 정보 보호 (Secrets Protection)**:
   - API Key, 비밀번호, 인증 토큰(Credentials, Private Tokens), 개인 키(Private Key) 등 민감한 정보를 소스 코드에 하드코딩하거나 Git 저장소에 커밋하지 않습니다.
   - 환경 변수(`.env`), 시크릿 관리자(Secret Manager), 또는 별도의 로컬 설정 파일을 활용하고, 해당 파일들은 반드시 `.gitignore`에 등록하여 형상 관리에서 제외합니다.

2. **외부 입력값 검증 및 정제 (Input Validation & Sanitization)**:
   - 사용자 입력값, URL 파라미터, 외부 파일, 네트워크 응답 등 모든 외부 입력(External Inputs)은 처리 전에 반드시 유효성을 검증(Validation)하고 정제(Sanitization)합니다.
   - SQL Injection, XSS(Cross-Site Scripting), Path Traversal, 커맨드 인젝션(Command Injection) 등의 취약점을 예방하도록 방어적 프로그래밍을 적용합니다.

3. **신뢰할 수 없는 원격 스크립트 실행 방지 (Remote Script Execution)**:
   - 출처가 불분명하거나 검증되지 않은 원격 스크립트(Remote Scripts), 바이너리 실행 파일 및 임의 명령어를 실행하지 않습니다.
   - 외부 의존성 라이브러리(Dependencies)는 신뢰할 수 있는 공식 레지스트리(PyPI, npm 등)를 통해서만 도입하고, 버전을 명시하여 관리합니다.

## 2. 작업 환경 보안 수칙 (Workspace Security)
- 로컬 환경에서 실행되는 백그라운드 프로세스 및 임시 스크립트는 작업 완료 후 안전하게 종료하고 정리합니다.
- 민감한 데이터나 개인정보(PII)가 포함된 테스트 데이터는 마스킹(Masking)하거나 더미(Mock/Dummy) 데이터를 사용합니다."""
    write_safe_file(rules_dir / "security.md", security_content, force)

    # 5. .agents/hooks.json
    hooks_content = """{
  "file-naming-guard": {
    "enabled": true,
    "PreToolUse": [
      {
        "matcher": "write_file",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/validate_file_naming.py --event PreToolUse",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python scripts/validate_file_naming.py --event Stop",
        "timeout": 10
      }
    ]
  }
}"""
    write_safe_file(agents_dir / "hooks.json", hooks_content, force)

    # 5-1. .agents/scripts/validate_file_naming.py
    validate_script_source = agents_scripts_dir / "validate_file_naming.py"
    if not validate_script_source.exists():
        cur_validate = Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "validate_file_naming.py"
        if cur_validate.exists():
            write_safe_file(validate_script_source, cur_validate.read_text(encoding="utf-8"), force)

    # 6. .agents/mcp_config.json
    mcp_content = """{
  "mcpServers": {}
}"""
    write_safe_file(agents_dir / "mcp_config.json", mcp_content, force)

    # 16. .agents/rules/file_naming.md
    file_naming_content = """# 표준 파일 명명 규칙 및 버전 관리 가이드라인 (File Naming & Versioning Rules)

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
   - **`02_output_data/00_data/` (1단계 수치 데이터)**: `excel`, `csv`
   - **`02_output_data/01_figure/` (2단계 시각화 및 실행 로그)**: `plot`, `image`, `architecture`, `log`
     > [!IMPORTANT]
     > **아키텍처 다이어그램 이미지 예외 수칙**: 아키텍처 및 프로세스 흐름도 다이어그램을 이미지 파일로 저장할 때는 포맷태그를 반드시 **`architecture`**로 지정합니다 (예: `architecture_001_(system_flow)_261029_rev00.png`).
   - **`02_output_data/02_reports/` (3단계 최종 보고서 및 발표자료)**: `doc`, `ppt`, `pdf`
   - **`03_scripts/` (전/후처리 및 배치 자동화 스크립트)**: `py`, `jou`, `ccl`, `sh`
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
- **가공 수치 데이터**: `02_output_data/00_data/excel_001_(cell1_discharge_preprocessed)_261029_rev00.xlsx`
- **아키텍처 다이어그램 이미지**: `02_output_data/01_figure/architecture_001_(system_architecture)_261029_rev00.png`
- **일반 플롯/차트 이미지**: `02_output_data/01_figure/plot_001_(temperature_contour)_261029_rev00.png`
- **최종 기술 보고서**: `02_output_data/02_reports/doc_001_(final_analysis_report)_261029_rev00.docx`
- **자동화 스크립트**: `03_scripts/py_001_(postprocess_parser)_261029_rev00.py`"""
    write_safe_file(rules_dir / "file_naming.md", file_naming_content, force)

    # 17. .agents/rules/artifact_management.md
    artifact_rule_content = """# 산출물 및 실무 자료 저장소 관리 규칙 (Artifact & Material Storage Rules)

워크스페이스에서 생성·수집되는 모든 에이전트 프로세스 산출물, 실무 투입 자료, 엔지니어링 성과물, 자동화 스크립트 및 RAG 지식 베이스는 성격에 따라 아래 **5대 번호형 디렉터리**에 엄격히 격리하여 보관합니다.

## 1. 5대 번호형 저장소 격리 원칙

1. **`00_artifacts/` (에이전트 프로세스 산출물 전용)**:
   - **오직 Antigravity 에이전트의 작업 프로세스로부터 생성되는 마크다운(`.md`) 산출물**만 보관합니다.
   - 사용자가 직접 작성한 파일이나 외부 원천 자료는 절대 이 폴더에 보관하지 않습니다.
   - 하위 디렉터리:
     - `plans/`: 구현 계획서 및 기능 기획서
     - `walkthroughs/`: 작업 완료 보고서 및 테스트 검증 리포트
     - `reports/`: 에이전트가 자체 조사·분석한 심층 기술 리포트
     - `designs/`: 시스템 아키텍처 및 상세 설계서

2. **`01_input_data/` (실무 투입 자료 저장소)**:
   - 업무 및 엔지니어링 해석을 위해 사전 투입되는 입력 자료를 보관합니다.
   - 하위 디렉터리:
     - `00_received/`: 고객사, 시험실, 협력사 등 외부에서 전달받은 원천 자료 (사양서, CAD/STEP 도면, 물성치 시트, 측정 데이터 등 — 원본 파일명 보존 허용)
     - `01_references/`: 에이전트 작업 지시서/요구사항 메모, 솔버 매뉴얼, 산업 규격(ISO/ASME/ASTM), 사용자 수집 리서치 논문 및 데이터시트

3. **`02_output_data/` (실무 엔지니어링 자산 저장소 - 작업 흐름 3단계)**:
   - 실제 작업 및 시뮬레이션 결과로 생성된 비-마크다운 실무 자산을 작업 단계별로 분리 보관합니다.
   - 하위 디렉터리:
     - `00_data/`: 1단계 가공·정제 수치 데이터 및 해석 결과 데이터 (`excel`, `csv`)
     - `01_figure/`: 2단계 시각화 플롯 차트, 아키텍처 다이어그램 이미지, 콘투어 캡처, 솔버 실행 로그 (`plot`, `image`, `architecture`, `log`)
     - `02_reports/`: 3단계 최종 기술 완료 보고서, 발표 슬라이드, 배포용 문서 (`doc`, `ppt`, `pdf`)

4. **`03_scripts/` (자동화 스크립트 저장소)**:
   - 데이터 전/후처리 Python 스크립트(`py`), 솔버 배치 저널(`jou`, `ccl`), 쉘 스크립트(`sh`)를 독립 관리합니다.

5. **`04_rag_database/` (RAG 지식 베이스 저장소)**:
   - 문서 기반 질의응답을 위한 벡터 인덱스(ChromaDB) 및 역색인(BM25) 전용 저장소이며, 세부 타깃 패키지(`<target_id>/`), 추출 이미지, `.gitignore` 및 카탈로그는 `rag-builder` 스킬이 동적으로 관리합니다.

## 2. 파일 명명 규칙 및 인덱스 동기화 의무

- **표준 파일 명명 규칙**: 모든 생성 파일의 이름은 반드시 [`.agents/rules/file_naming.md`](file_naming.md)에 정의된 통합 명명 규칙(`[포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]`)을 준수합니다.
- **중앙 인덱스 자동 동기화**: 각 저장소에 파일을 신규 생성하거나 리비전을 갱신할 때는 반드시 해당 저장소 루트의 `README.md`(`00_artifacts/README.md`, `01_input_data/README.md`, `02_output_data/README.md`, `04_rag_database/README.md`) 인덱스 테이블에 즉시 등록·갱신해야 합니다."""
    write_safe_file(rules_dir / "artifact_management.md", artifact_rule_content, force)


def scaffold(target_dir: Path, force: bool = False, include_agents: bool = False) -> None:
    scope_str = "00_artifacts ~ 04_rag_database" + (", .agents" if include_agents else "")
    print(f"Initializing workspace environment ({scope_str}) at: {target_dir}")
    
    # 5대 표준 번호형 실무/산출물 디렉터리 구성
    artifacts_dir = target_dir / "00_artifacts"
    artifact_sub_dirs = ["plans", "walkthroughs", "reports", "designs"]

    input_dir = target_dir / "01_input_data"
    input_sub_dirs = ["00_received", "01_references"]

    output_dir = target_dir / "02_output_data"
    output_sub_dirs = ["00_data", "01_figure", "02_reports"]

    scripts_dir = target_dir / "03_scripts"
    rag_dir = target_dir / "04_rag_database"

    dirs = [
        artifacts_dir, input_dir, output_dir, scripts_dir, rag_dir
    ]
    for sub in artifact_sub_dirs:
        dirs.append(artifacts_dir / sub)
    for sub in input_sub_dirs:
        dirs.append(input_dir / sub)
    for sub in output_sub_dirs:
        dirs.append(output_dir / sub)

    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            print(f"  [+] Created directory: {d}")

    # 1. 00_artifacts subdirectories .gitkeep
    for sub in artifact_sub_dirs:
        keep_path = artifacts_dir / sub / ".gitkeep"
        if not keep_path.exists():
            keep_path.write_text("", encoding="utf-8")
            print(f"  [+] Created file: {keep_path}")

    # 2. 01_input_data subdirectories .gitkeep
    for sub in input_sub_dirs:
        keep_path = input_dir / sub / ".gitkeep"
        if not keep_path.exists():
            keep_path.write_text("", encoding="utf-8")
            print(f"  [+] Created file: {keep_path}")

    # 3. 02_output_data subdirectories .gitkeep
    for sub in output_sub_dirs:
        keep_path = output_dir / sub / ".gitkeep"
        if not keep_path.exists():
            keep_path.write_text("", encoding="utf-8")
            print(f"  [+] Created file: {keep_path}")

    # 4. 03_scripts directory .gitkeep
    scripts_keep = scripts_dir / ".gitkeep"
    if not scripts_keep.exists():
        scripts_keep.write_text("", encoding="utf-8")
        print(f"  [+] Created file: {scripts_keep}")

    # 5. 04_rag_database directory .gitkeep
    rag_keep = rag_dir / ".gitkeep"
    if not rag_keep.exists():
        rag_keep.write_text("", encoding="utf-8")
        print(f"  [+] Created file: {rag_keep}")

    # 6. 00_artifacts/README.md
    artifacts_readme = """# Workspace Artifacts (`00_artifacts/`)

이 공간은 **오직 Antigravity 에이전트의 작업 프로세스로부터 생성되는 산출물(Artifacts - Markdown .md 전용)**만을 관리하는 디렉터리입니다.
실무 투입 자료는 `01_input_data/`, 실무 성과물은 `02_output_data/`, 자동화 코드는 `03_scripts/`, RAG 지식 베이스는 `04_rag_database/`에 엄격히 격리 보관됩니다.

## 📂 카테고리 구성
- [plans/](plans/): 구현 계획서 및 기능 기획서 (`plan_[일련번호]_([주제명])_[YYMMDD]_rev[NN].md`)
- [walkthroughs/](walkthroughs/): 작업 완료 보고서 및 검증 결과 (`walkthrough_[일련번호]_([주제명])_[YYMMDD]_rev[NN].md`)
- [reports/](reports/): 에이전트가 자체 조사·분석한 심층 기술 리포트 (`report_[일련번호]_([주제명])_[YYMMDD]_rev[NN].md`)
- [designs/](designs/): 시스템 아키텍처 및 상세 설계서 (`design_[일련번호]_([주제명])_[YYMMDD]_rev[NN].md`)

## 🏷️ 아티팩트 명명 규칙
- **표준 템플릿**: `[포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].md` ([`.agents/rules/file_naming.md`](../.agents/rules/file_naming.md) 준수)
- **버전 규칙**: 최초 생성 시 무조건 `rev00` 부여, 내용 갱신 시 `rev01`, `rev02`로 증가.

## 📑 아티팩트 통합 인덱스 (Index)
| 일자 | 분류 | 문서명 | 설명 | 상태 |
| :---: | :---: | :--- | :--- | :---: |"""
    write_safe_file(artifacts_dir / "README.md", artifacts_readme, force)

    # 7. 01_input_data/README.md
    input_readme = """# Workspace Input Materials (`01_input_data/`)

이 공간은 CAE/CFD 해석 및 엔지니어링 작업을 수행하기 위해 사전에 투입되는 실무 입력 자료를 보관하는 독립 저장소입니다.
에이전트 산출물(`00_artifacts/`) 및 실행 결과물(`02_output_data/`)과 엄격히 분리되어 관리됩니다.

## 📂 카테고리 구성
- **[00_received/](00_received/)**: 고객사, 시험실, 협력업체 등 외부에서 수신한 원천 자료 (원본 파일명 보존 허용, 사양서, CAD/STEP 형상, 물성치 시트, 메쉬 파일, 시험 데이터 등)
- **[01_references/](01_references/)**: 
  - **에이전트 작업 지시 투입 자료**: 사용자가 에이전트에게 구체적인 작업을 지시하기 위해 작성·준비한 작업 요구사항 정의서, 작업 지시 메모, 해석 가이드라인, 프롬프트용 참조 텍스트
  - **엔지니어링 표준 기준**: 솔버 공식 매뉴얼, 설계 기준, 산업 규격(ISO/ASME/ASTM)
  - **사용자 조사 리서치 자료**: 업무 수행 중 사용자가 직접 탐색·수집한 참고 논문, 장비 카탈로그, 기술 데이터시트, 웹 포럼 해결 팁

## 🏷️ 파일명 명명 규칙: 일련번호 및 버전 관리 표준
- **표준 템플릿**: `[포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]` ([`.agents/rules/file_naming.md`](../.agents/rules/file_naming.md) 준수)
- **원천 자료 보존 예외 (Raw Preservation)**: `00_received/`에 저장되는 외부 수신 파일은 원본 파일명을 유지하는 것을 허용합니다.

## 📑 입력 자료 목록 인덱스 (Index)
| 일자 | 폴더 | 일련번호 | 주제/설명 | 출처/제공처 | 파일명 (링크) |
| :--- | :--- | :---: | :--- | :--- | :--- |"""
    write_safe_file(input_dir / "README.md", input_readme, force)

    # 8. 02_output_data/README.md
    output_readme = """# Workspace Practical Materials & Assets (`02_output_data/`)

이 공간은 시뮬레이션 해석 및 도구 실행 과정에서 생산되는 실무 엔지니어링 자산(데이터, 시각화, 보고서)을 보관하는 독립 저장소입니다.
작업 흐름 순서(1단계 데이터 ➔ 2단계 그림/로그 ➔ 3단계 보고서)에 맞춰 번호 기반으로 정렬됩니다.

## 📂 카테고리 구성 (작업 흐름 3단계 순서화)
- **[00_data/](00_data/)**: 1단계 가공·정제 입력 데이터 및 시뮬레이션 솔버 해석 결과 수치 데이터 (`excel_`, `csv_`)
- **[01_figure/](01_figure/)**: 2단계 시각화 플롯 차트, 아키텍처 다이어그램 이미지, 유선/온도장 콘투어 이미지, 격자/도면 캡처, 솔버 실행 로그 (`plot_`, `image_`, `architecture_`, `log_`)
- **[02_reports/](02_reports/)**: 3단계 최종 기술 보고서, 고객 보고용 발표 슬라이드, 배포용 요약 문서 (`doc_`, `ppt_`, `pdf_`)

## 🏷️ 파일명 명명 규칙: 일련번호 및 버전 관리 표준
- **표준 템플릿**: `[포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]` ([`.agents/rules/file_naming.md`](../.agents/rules/file_naming.md) 준수)

## 📑 산출 자료 목록 인덱스 (Index)
| 일자 | 폴더 | 일련번호 | 주제/설명 | 파일명 (링크) |
| :--- | :--- | :---: | :--- | :--- |"""
    write_safe_file(output_dir / "README.md", output_readme, force)

    # 9. 04_rag_database/README.md
    rag_readme = """# Workspace RAG Knowledge Base (`04_rag_database/`)

이 공간은 프로젝트 및 기술 문서 기반 질의응답을 위한 **RAG(Retrieval-Augmented Generation) 벡터 인덱스 및 지식 베이스**를 관리하는 전용 저장소입니다.

## 📂 저장소 관리 원칙 (Architecture Rationale)
- **린(Lean) 스캐폴딩 & 지연 초기화**: `init-env` 스킬은 디렉터리 뼈대와 기본 가이드만 준비하며, 실제 RAG 색인 구축 시점에 `rag-builder` 스킬이 문서/프로젝트별 격리 구조(`targets/<id>/`), 메타데이터 레지스트리(`index_catalog.json`), `.gitignore`를 온디맨드로 생성하고 관리합니다.
- **대용량 바이너리 Git 추적 방지**: ChromaDB 및 BM25의 대용량 데이터베이스 파일(`*.parquet`, `*.sqlite3`, `*.pkl`)은 `rag-builder`가 생성하는 `.gitignore`를 통해 Git 커밋에서 자동 제외되어 저장소 용량을 가볍게 유지합니다.

## 📑 인덱스 타깃 목록 (Index Targets)
| 타깃 ID | 문서명/설명 | 청크 수 | 임베딩 모델 | 생성일자 | 상태 |
| :--- | :--- | :---: | :---: | :---: | :---: |"""
    write_safe_file(rag_dir / "README.md", rag_readme, force)

    # 10. Optional .agents/ scaffolding (Only when include_agents=True)
    if include_agents:
        scaffold_agents_governance(target_dir, force)

    print("Scaffolding completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold workspace environment (00_artifacts ~ 04_rag_database).")
    parser.add_argument("--target-dir", type=str, default=".", help="Target directory for scaffolding.")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing files.")
    parser.add_argument("--include-agents", action="store_true", help="Optionally scaffold .agents/ governance directory and subagents.")
    
    args = parser.parse_args()
    
    target_path = Path(args.target_dir).resolve()
    scaffold(target_path, args.force, args.include_agents)
