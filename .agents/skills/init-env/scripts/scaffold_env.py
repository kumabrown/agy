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
    agents_scripts_dir = agents_dir / "scripts"
    
    artifacts_dir = target_dir / "00_artifacts"
    artifact_sub_dirs = ["plans", "walkthroughs", "reports", "designs"]

    input_dir = target_dir / "01_input_data"
    input_sub_dirs = ["00_received", "01_references"]
    
    output_dir = target_dir / "02_output_data"
    output_sub_dirs = ["00_data", "01_figure", "02_reports"]

    scripts_dir = target_dir / "03_scripts"
    rag_dir = target_dir / "04_rag_database"
    
    dirs = [
        agents_dir, rules_dir, skills_dir, agents_scripts_dir,
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
- **rules/**: Coding standards, architecture constraints, file naming conventions, and security guidelines.
- **skills/**: Specialized multi-step workflows, runbooks, and task automation.
- **agents.md**: Custom subagent personas and tool permission mappings.
- **hooks.json**: Lifecycle automation hooks (linter, formatting, verification).
- **mcp_config.json**: Model Context Protocol (MCP) server integrations."""
    write_safe_file(agents_dir / "README.md", readme_content, force)

    # 2. .agents/agents.md
    agents_content = """# 커스텀 서브에이전트 페르소나 (Custom Subagent Personas)

페어 프로그래밍(Pair programming) 및 작업 위임(Task delegation)을 위한 특화된 에이전트 페르소나 정의입니다.

## @reviewer
- **Role**: 코드 품질 및 보안 감사관 (Code Quality & Security Auditor)
- **System Prompt**: 보안 취약점(Security vulnerabilities), 로직 오류 및 프로젝트 규칙 준수 여부를 확인하기 위해 코드 diff(Code diffs)를 면밀히 검토합니다.

## @architect
- **Role**: 시스템 및 API 설계자 (System & API Designer)
- **System Prompt**: 확장 가능한 모듈형 시스템을 설계하고, API 명세서(API specifications)를 작성하며, 데이터베이스 스키마(Database schemas)를 제안합니다.

## @tester
- **Role**: QA 및 테스트 자동화 엔지니어 (QA & Test Automation Engineer)
- **System Prompt**: 새로 추가된 기능에 대해 철저한 단위 테스트(Unit tests), 통합 테스트(Integration tests) 및 엔드투엔드 테스트(End-to-end tests)를 작성합니다."""
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
    if not (agents_scripts_dir / "validate_file_naming.py").exists():
        # Keep existing validate script if present, otherwise read current script
        cur_validate = Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "validate_file_naming.py"
        if cur_validate.exists():
            write_safe_file(agents_scripts_dir / "validate_file_naming.py", cur_validate.read_text(encoding="utf-8"), force)

    # 6. .agents/mcp_config.json
    mcp_content = """{
  "mcpServers": {}
}"""
    write_safe_file(agents_dir / "mcp_config.json", mcp_content, force)

    # 7. 00_artifacts subdirectories .gitkeep
    for sub in artifact_sub_dirs:
        keep_path = artifacts_dir / sub / ".gitkeep"
        if not keep_path.exists():
            keep_path.write_text("", encoding="utf-8")
            print(f"  [+] Created file: {keep_path}")

    # 8. 01_input_data subdirectories .gitkeep
    for sub in input_sub_dirs:
        keep_path = input_dir / sub / ".gitkeep"
        if not keep_path.exists():
            keep_path.write_text("", encoding="utf-8")
            print(f"  [+] Created file: {keep_path}")

    # 9. 02_output_data subdirectories .gitkeep
    for sub in output_sub_dirs:
        keep_path = output_dir / sub / ".gitkeep"
        if not keep_path.exists():
            keep_path.write_text("", encoding="utf-8")
            print(f"  [+] Created file: {keep_path}")

    # 10. 03_scripts directory .gitkeep
    scripts_keep = scripts_dir / ".gitkeep"
    if not scripts_keep.exists():
        scripts_keep.write_text("", encoding="utf-8")
        print(f"  [+] Created file: {scripts_keep}")

    # 11. 04_rag_database directory .gitkeep
    rag_keep = rag_dir / ".gitkeep"
    if not rag_keep.exists():
        rag_keep.write_text("", encoding="utf-8")
        print(f"  [+] Created file: {rag_keep}")

    # 12. 00_artifacts/README.md
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

    # 13. 01_input_data/README.md
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

    # 14. 02_output_data/README.md
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

    # 15. 04_rag_database/README.md
    rag_readme = """# Workspace RAG Knowledge Base (`04_rag_database/`)

이 공간은 프로젝트 및 기술 문서 기반 질의응답을 위한 **RAG(Retrieval-Augmented Generation) 벡터 인덱스 및 지식 베이스**를 관리하는 전용 저장소입니다.

## 📂 저장소 관리 원칙 (Architecture Rationale)
- **린(Lean) 스캐폴딩 & 지연 초기화**: `init-env` 스킬은 디렉터리 뼈대와 기본 가이드만 준비하며, 실제 RAG 색인 구축 시점에 `rag-builder` 스킬이 문서/프로젝트별 격리 구조(`targets/<id>/`), 메타데이터 레지스트리(`index_catalog.json`), `.gitignore`를 온디맨드로 생성하고 관리합니다.
- **대용량 바이너리 Git 추적 방지**: ChromaDB 및 BM25의 대용량 데이터베이스 파일(`*.parquet`, `*.sqlite3`, `*.pkl`)은 `rag-builder`가 생성하는 `.gitignore`를 통해 Git 커밋에서 자동 제외되어 저장소 용량을 가볍게 유지합니다.

## 📑 인덱스 타깃 목록 (Index Targets)
| 타깃 ID | 문서명/설명 | 청크 수 | 임베딩 모델 | 생성일자 | 상태 |
| :--- | :--- | :---: | :---: | :---: | :---: |"""
    write_safe_file(rag_dir / "README.md", rag_readme, force)

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

    print("Scaffolding completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold workspace environment.")
    parser.add_argument("--target-dir", type=str, default=".", help="Target directory for scaffolding.")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing files.")
    
    args = parser.parse_args()
    
    target_path = Path(args.target_dir).resolve()
    scaffold(target_path, args.force)
