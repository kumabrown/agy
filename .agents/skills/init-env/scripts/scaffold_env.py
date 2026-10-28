import argparse
import sys
from pathlib import Path

def write_safe_file(file_path: Path, content: str, force: bool = False) -> None:
    if file_path.exists() and not force:
        print(f"  [!] Skipped existing file: {file_path}")
        return
    file_path.write_text(content, encoding="utf-8")
    print(f"  [+] Created file: {file_path}")

def scaffold(target_dir: Path, force: bool = False) -> None:
    print(f"Initializing workspace environment (.agents, 00_artifacts ~ 04_rag_database) at: {target_dir}")
    
    agents_dir = target_dir / ".agents"
    rules_dir = agents_dir / "rules"
    skills_dir = agents_dir / "skills"
    example_skill_dir = skills_dir / "example-workflow"
    
    artifacts_dir = target_dir / "00_artifacts"
    artifact_sub_dirs = ["plans", "walkthroughs", "reports", "designs"]

    input_dir = target_dir / "01_input_data"
    input_sub_dirs = ["00_received", "01_references"]
    
    output_dir = target_dir / "02_output_data"
    output_sub_dirs = ["00_data", "01_figure", "02_reports"]

    scripts_dir = target_dir / "03_scripts"
    rag_dir = target_dir / "04_rag_database"
    
    dirs = [
        agents_dir, rules_dir, skills_dir, example_skill_dir,
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
            
    # 1. .agents/README.md
    readme_content = """# Project Antigravity Customizations

This directory contains workspace-level customizations for Google Antigravity agents, shared across the team.

## Directory Structure
- **rules/**: Coding standards, architecture constraints, and security guidelines.
- **skills/**: Specialized multi-step workflows, runbooks, and task automation.
- **agents.md**: Custom subagent personas and tool permission mappings.
- **hooks.json**: Lifecycle automation hooks (linter, formatting, verification).
- **mcp_config.json**: Model Context Protocol (MCP) server integrations."""
    write_safe_file(agents_dir / "README.md", readme_content, force)

    # 2. .agents/agents.md
    agents_content = """# Custom Subagent Personas

Define specialized agent personas for pair programming and task delegation.

## @reviewer
- **Role**: Code Quality & Security Auditor
- **System Prompt**: Review code diffs for security vulnerabilities, logic errors, and adherence to project rules.

## @architect
- **Role**: System & API Designer
- **System Prompt**: Design scalable modular systems, draft API specifications, and propose database schemas.

## @tester
- **Role**: QA & Test Automation Engineer
- **System Prompt**: Write thorough unit, integration, and end-to-end tests for newly added features."""
    write_safe_file(agents_dir / "agents.md", agents_content, force)

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
    security_content = """# Security Guidelines

## Principles
1. Never commit API keys, secrets, credentials, or private tokens.
2. Validate and sanitize all external inputs before processing.
3. Avoid executing arbitrary, unverified remote scripts."""
    write_safe_file(rules_dir / "security.md", security_content, force)

    # 5. .agents/skills/example-workflow/SKILL.md
    example_skill_content = """---
name: example-workflow
description: An example custom skill demonstrating multi-step automation in this project.
---

# Example Custom Workflow

This is a starter template for writing project-specific skills.

## Workflow Steps
1. Review task requirements.
2. Run project linter and unit tests.
3. Verify build output."""
    write_safe_file(example_skill_dir / "SKILL.md", example_skill_content, force)

    # 6. .agents/hooks.json
    hooks_content = """{
  "project-linter": {
    "enabled": false,
    "PostToolUse": [
      {
        "matcher": "replace_file_content",
        "hooks": [
          {
            "type": "command",
            "command": "npm run lint --if-present",
            "timeout": 15
          }
        ]
      }
    ]
  }
}"""
    write_safe_file(agents_dir / "hooks.json", hooks_content, force)

    # 7. .agents/mcp_config.json
    mcp_content = """{
  "mcpServers": {}
}"""
    write_safe_file(agents_dir / "mcp_config.json", mcp_content, force)

    # 8. 00_artifacts subdirectories .gitkeep
    for sub in artifact_sub_dirs:
        keep_path = artifacts_dir / sub / ".gitkeep"
        if not keep_path.exists():
            keep_path.write_text("", encoding="utf-8")
            print(f"  [+] Created file: {keep_path}")

    # 9. 01_input_data subdirectories .gitkeep
    for sub in input_sub_dirs:
        keep_path = input_dir / sub / ".gitkeep"
        if not keep_path.exists():
            keep_path.write_text("", encoding="utf-8")
            print(f"  [+] Created file: {keep_path}")

    # 10. 02_output_data subdirectories .gitkeep
    for sub in output_sub_dirs:
        keep_path = output_dir / sub / ".gitkeep"
        if not keep_path.exists():
            keep_path.write_text("", encoding="utf-8")
            print(f"  [+] Created file: {keep_path}")

    # 11. 03_scripts directory .gitkeep
    scripts_keep = scripts_dir / ".gitkeep"
    if not scripts_keep.exists():
        scripts_keep.write_text("", encoding="utf-8")
        print(f"  [+] Created file: {scripts_keep}")

    # 12. 04_rag_database directory .gitkeep
    rag_keep = rag_dir / ".gitkeep"
    if not rag_keep.exists():
        rag_keep.write_text("", encoding="utf-8")
        print(f"  [+] Created file: {rag_keep}")

    # 13. 00_artifacts/README.md
    artifacts_readme = """# Workspace Artifacts (`00_artifacts/`)

이 공간은 **오직 Antigravity 에이전트의 작업 프로세스로부터 생성되는 산출물(Artifacts - Markdown .md 전용)**만을 관리하는 디렉터리입니다.
실무 투입 자료는 `01_input_data/`, 실무 성과물은 `02_output_data/`, 자동화 코드는 `03_scripts/`, RAG 지식 베이스는 `04_rag_database/`에 엄격히 격리 보관됩니다.

## 📂 카테고리 구성
- [plans/](plans/): 구현 계획서 및 기능 기획서 (`plan_([주제명])_[YYMMDD]_rev[NN].md`)
- [walkthroughs/](walkthroughs/): 작업 완료 보고서 및 검증 결과 (`walkthrough_([주제명])_[YYMMDD]_rev[NN].md`)
- [reports/](reports/): 에이전트가 자체 조사·분석한 심층 기술 리포트 (`report_([주제명])_[YYMMDD]_rev[NN].md`)
- [designs/](designs/): 시스템 아키텍처 및 상세 설계서 (`design_([주제명])_[YYMMDD]_rev[NN].md`)

## 🏷️ 아티팩트 명명 규칙
- **형식**: `[카테고리]_([주제명])_[YYMMDD]_rev[NN].md`
- **버전 규칙**: 최초 생성 시 무조건 `rev00` 부여, 내용 갱신 시 `rev01`, `rev02`로 증가.

## 📑 아티팩트 통합 인덱스 (Index)
| 일자 | 분류 | 문서명 | 설명 | 상태 |
| :---: | :---: | :--- | :--- | :---: |"""
    write_safe_file(artifacts_dir / "README.md", artifacts_readme, force)

    # 14. 01_input_data/README.md
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
- **표준 템플릿**: `[포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]`
- **일련번호**: 3자리 문서번호 (`001`, `002`, ... `999`)
- **버전 관리**: 최초 생성 시 무조건 **`rev00`**, 내용 갱신 시 **`rev01`**, **`rev02`**로 번호 증가.
- **원천 자료 보존 예외 (Raw Preservation)**: `00_received/`에 저장되는 외부 수신 파일은 원본 파일명을 유지하는 것을 허용합니다.

## 📑 입력 자료 목록 인덱스 (Index)
| 일자 | 폴더 | 일련번호 | 주제/설명 | 출처/제공처 | 파일명 (링크) |
| :--- | :--- | :---: | :--- | :--- | :--- |"""
    write_safe_file(input_dir / "README.md", input_readme, force)

    # 15. 02_output_data/README.md
    output_readme = """# Workspace Practical Materials & Assets (`02_output_data/`)

이 공간은 시뮬레이션 해석 및 도구 실행 과정에서 생산되는 실무 엔지니어링 자산(데이터, 시각화, 보고서)을 보관하는 독립 저장소입니다.
작업 흐름 순서(1단계 데이터 ➔ 2단계 그림/로그 ➔ 3단계 보고서)에 맞춰 번호 기반으로 정렬됩니다.

## 📂 카테고리 구성 (작업 흐름 3단계 순서화)
- **[00_data/](00_data/)**: 1단계 가공·정제 입력 데이터 및 시뮬레이션 솔버 해석 결과 수치 데이터 (`excel_`, `csv_`)
- **[01_figure/](01_figure/)**: 2단계 시각화 플롯 차트, 유선/온도장 콘투어 이미지, 격자/도면 캡처, 솔버 실행 로그 (`plot_`, `image_`, `log_`)
- **[02_reports/](02_reports/)**: 3단계 최종 기술 보고서, 고객 보고용 발표 슬라이드, 배포용 요약 문서 (`doc_`, `ppt_`, `pdf_`)

## 🏷️ 파일명 명명 규칙: 일련번호 및 버전 관리 표준
하루에 수십~수백 개의 결과 파일이 생성되어도 순서와 버전을 파악할 수 있도록 3자리 일련번호(`001`~)와 리비전(`rev00`~)을 필수로 결합합니다:
- **표준 템플릿**: `[포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]`
  - 예: `excel_001_(cell1_discharge_preprocessed)_261027_rev00.xlsx`
  - 수정 시: `excel_001_(cell1_discharge_preprocessed)_261027_rev01.xlsx`
  - 신규 생성: `excel_002_(cell2_discharge_preprocessed)_261027_rev00.xlsx`

## 📑 산출 자료 목록 인덱스 (Index)
| 일자 | 폴더 | 일련번호 | 주제/설명 | 파일명 (링크) |
| :--- | :--- | :---: | :--- | :--- |"""
    write_safe_file(output_dir / "README.md", output_readme, force)

    # 16. 04_rag_database/README.md
    rag_readme = """# Workspace RAG Knowledge Base (`04_rag_database/`)

이 공간은 프로젝트 및 기술 문서 기반 질의응답을 위한 **RAG(Retrieval-Augmented Generation) 벡터 인덱스 및 지식 베이스**를 관리하는 전용 저장소입니다.

## 📂 저장소 관리 원칙 (Architecture Rationale)
- **린(Lean) 스캐폴딩 & 지연 초기화**: `init-env` 스킬은 디렉터리 뼈대와 기본 가이드만 준비하며, 실제 RAG 색인 구축 시점에 `rag-builder` 스킬이 문서/프로젝트별 격리 구조(`targets/<id>/`), 메타데이터 레지스트리(`index_catalog.json`), `.gitignore`를 온디맨드로 생성하고 관리합니다.
- **대용량 바이너리 Git 추적 방지**: ChromaDB 및 BM25의 대용량 데이터베이스 파일(`*.parquet`, `*.sqlite3`, `*.pkl`)은 `rag-builder`가 생성하는 `.gitignore`를 통해 Git 커밋에서 자동 제외되어 저장소 용량을 가볍게 유지합니다.

## 📑 인덱스 타깃 목록 (Index Targets)
| 타깃 ID | 문서명/설명 | 청크 수 | 임베딩 모델 | 생성일자 | 상태 |
| :--- | :--- | :---: | :---: | :---: | :---: |"""
    write_safe_file(rag_dir / "README.md", rag_readme, force)

    # 17. .agents/rules/artifact_management.md
    artifact_rule_content = """# Artifact and Material Management Rule

All generated markdown process artifacts, operational inputs, practical outputs, scripts, and RAG databases must be preserved under their respective 5 numbered directories:

1. **Process Artifacts (`00_artifacts/`)**:
   - Exclusively for Antigravity agent process outputs (.md only).
   - Plans: `00_artifacts/plans/plan_([topic])_[YYMMDD]_rev[NN].md`
   - Walkthroughs: `00_artifacts/walkthroughs/walkthrough_([topic])_[YYMMDD]_rev[NN].md`
   - Reports: `00_artifacts/reports/report_([topic])_[YYMMDD]_rev[NN].md`
   - Designs: `00_artifacts/designs/design_([topic])_[YYMMDD]_rev[NN].md`

2. **Input Materials (`01_input_data/`)**:
   - Received (`00_received/`): External provenance materials (spec sheets, CAD, raw data, test telemetry). Raw filenames preserved if required.
   - References (`01_references/`):
     - Agent task instructions, user guidelines, prompt context notes.
     - Engineering standards, solver manuals, user-researched papers.
     - Standard template: `[format]_[seq]_([topic])_[YYMMDD]_rev[NN].[ext]`

3. **Practical Outputs (`02_output_data/`)**:
   - Data (`00_data/`): `excel_[seq]_([topic])_[YYMMDD]_rev[NN].xlsx`, `csv_[seq]_([topic])_[YYMMDD]_rev[NN].csv`
   - Figure & Logs (`01_figure/`): `plot_[seq]_([topic])_[YYMMDD]_rev[NN].png`, `image_[seq]_([topic])_[YYMMDD]_rev[NN].png`, `log_[seq]_([topic])_[YYMMDD]_rev[NN].trn`
   - Reports & Slides (`02_reports/`): `doc_[seq]_([topic])_[YYMMDD]_rev[NN].docx`, `ppt_[seq]_([topic])_[YYMMDD]_rev[NN].pptx`, `pdf_[seq]_([topic])_[YYMMDD]_rev[NN].pdf`

4. **Automation Scripts (`03_scripts/`)**:
   - Pre/post processing Python: `py_[seq]_([topic])_[YYMMDD]_rev[NN].py`
   - Solver batch journal: `jou_[seq]_([topic])_[YYMMDD]_rev[NN].jou`

5. **RAG Knowledge Base (`04_rag_database/`)**:
   - Dedicated storage for RAG indexes and vector databases.
   - Targets, .gitignore, and catalog are dynamically managed on-demand by `rag-builder`.

- Underscores only (`_`), no hyphens (`-`).
- Topic enclosed in parentheses `(` `)`.
- Sequence: 3-digit serial number (`001`, `002`, ... `999`).
- Versioning: `rev00` default on creation; increment (`rev01`, `rev02`) on modification.
- Always update index tables in the respective `README.md` files."""
    write_safe_file(rules_dir / "artifact_management.md", artifact_rule_content, force)

    print("Scaffolding completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold workspace environment.")
    parser.add_argument("--target-dir", type=str, default=".", help="Target directory for scaffolding.")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing files.")
    
    args = parser.parse_args()
    
    target_path = Path(args.target_dir).resolve()
    scaffold(target_path, args.force)
