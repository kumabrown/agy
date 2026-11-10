"""
Workspace Environment Scaffolding Script.

Scaffolds standard 5 numbered workspace repositories (00_artifacts to 04_rag_database)
and their respective directory structures, .gitkeep, and README.md files.
This script strictly focuses on workspace practical directories and never touches .agents/.
"""

import argparse
from pathlib import Path


def write_safe_file(file_path: Path, content: str, force: bool = False) -> None:
    """Write content to file safely, skipping existing files unless force=True."""
    if file_path.exists() and not force:
        print(f"  [!] Skipped existing file: {file_path}")
        return
    file_path.write_text(content, encoding="utf-8")
    print(f"  [+] Created file: {file_path}")


def scaffold(target_dir: Path | str, force: bool = False) -> None:
    """Scaffold the 5 standard numbered workspace repositories."""
    target_dir = Path(target_dir).resolve()
    print(f"Initializing workspace environment (00_artifacts ~ 04_rag_database) at: {target_dir}")
    
    # 5 standard numbered repositories configuration
    artifacts_dir = target_dir / "00_artifacts"
    artifact_sub_dirs = ["plans", "walkthroughs", "reports", "designs"]

    input_dir = target_dir / "01_input_data"
    input_sub_dirs = ["00_received", "01_references"]

    output_dir = target_dir / "02_output_data"
    output_sub_dirs = ["00_data", "01_figure", "02_reports"]

    scripts_dir = target_dir / "03_scripts"
    scripts_sub_dirs = ["python", "script"]

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
    for sub in scripts_sub_dirs:
        dirs.append(scripts_dir / sub)

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

    # 4. 03_scripts subdirectories .gitkeep
    for sub in scripts_sub_dirs:
        keep_path = scripts_dir / sub / ".gitkeep"
        if not keep_path.exists():
            keep_path.write_text("", encoding="utf-8")
            print(f"  [+] Created file: {keep_path}")

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
- **[00_data/](00_data/)**: 1단계 정형 설계/결과 스펙(JSON), 가공·정제 입력 데이터 및 시뮬레이션 솔버 해석 결과 수치 데이터 (`json_`, `excel_`, `csv_`)
- **[01_figure/](01_figure/)**: 2단계 시각화 플롯 차트, 아키텍처 다이어그램 이미지, 유선/온도장 콘투어 이미지, 격자/도면 캡처, 솔버 실행 로그 (`plot_`, `image_`, `architecture_`, `log_`)
- **[02_reports/](02_reports/)**: 3단계 최종 기술 보고서, 고객 보고용 발표 슬라이드, 배포용 요약 문서 (`doc_`, `ppt_`, `pdf_`)

## 🏷️ 파일명 명명 규칙: 일련번호 및 버전 관리 표준
- **표준 템플릿**: `[포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]` ([`.agents/rules/file_naming.md`](../.agents/rules/file_naming.md) 준수)

## 📑 산출 자료 목록 인덱스 (Index)
| 일자 | 폴더 | 일련번호 | 주제/설명 | 파일명 (링크) |
| :--- | :--- | :---: | :--- | :--- |"""
    write_safe_file(output_dir / "README.md", output_readme, force)

    # 9. 03_scripts/README.md
    scripts_readme = """# Workspace Automation Scripts (`03_scripts/`)

이 공간은 CAE/CFD 해석 자동화, 데이터 전/후처리, 솔버 배치 실행 및 유틸리티 스크립트/실행 파일을 관리하는 전용 저장소입니다.
스크립트 언어 및 도구 성격에 따라 하위 디렉터리를 엄격히 분리하여 보관합니다.

## 📂 카테고리 구성
- **[python/](python/)**: 데이터 가공·정제, 수치 연산, 시뮬레이션 파이프라인 등 **Python 스크립트 전용 (`py_*.py`)**
- **[script/](script/)**: Ansys Fluent 저널(`jou_*.jou`), CFX 커맨드 파일(`ccl_*.ccl`), CFD-Post 세션 파일(`cse_*.cse`), Windows 배치 파일(`bat_*.bat`), **독립 실행 파일(`exe_*.exe`)** 등 **솔버 배치 및 실행 파일 전용**

## 🏷️ 스크립트 명명 규칙: 일련번호 및 버전 관리 표준
- **표준 템플릿**: `[포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]` ([`.agents/rules/file_naming.md`](../.agents/rules/file_naming.md) 준수)
- **포맷 태그 규칙**:
  - `python/`: `py` (예: `py_001_(postprocess_parser)_261110_rev00.py`)
  - `script/`: `jou`, `ccl`, `cse`, `bat`, `exe` (예: `jou_001_(fluent_batch_solve)_261110_rev00.jou`, `exe_001_(custom_mesh_converter)_261110_rev00.exe`)

## 📑 자동화 스크립트 목록 인덱스 (Index)
| 일자 | 폴더 | 일련번호 | 주제/설명 | 실행 환경 / 솔버 | 파일명 (링크) |
| :--- | :--- | :---: | :--- | :--- | :--- |"""
    write_safe_file(scripts_dir / "README.md", scripts_readme, force)

    # 10. 04_rag_database/README.md
    rag_readme = """# Workspace RAG Knowledge Base (`04_rag_database/`)

이 공간은 프로젝트 및 기술 문서 기반 질의응답을 위한 **RAG(Retrieval-Augmented Generation) 벡터 인덱스 및 지식 베이스**를 관리하는 전용 저장소입니다.

## 📂 저장소 관리 원칙 (Architecture Rationale)
- **린(Lean) 스캐폴딩 & 지연 초기화**: `init-env` 스킬은 디렉터리 뼈대와 기본 가이드만 준비하며, 실제 RAG 색인 구축 시점에 `rag-builder` 스킬이 문서/프로젝트별 격리 구조(`targets/<id>/`), 메타데이터 레지스트리(`index_catalog.json`), `.gitignore`를 온디맨드로 생성하고 관리합니다.
- **대용량 바이너리 Git 추적 방지**: ChromaDB 및 BM25의 대용량 데이터베이스 파일(`*.parquet`, `*.sqlite3`, `*.pkl`)은 `rag-builder`가 생성하는 `.gitignore`를 통해 Git 커밋에서 자동 제외되어 저장소 용량을 가볍게 유지합니다.

## 📑 인덱스 타깃 목록 (Index Targets)
| 타깃 ID | 문서명/설명 | 청크 수 | 임베딩 모델 | 생성일자 | 상태 |
| :--- | :--- | :---: | :--- | :---: | :---: |"""
    write_safe_file(rag_dir / "README.md", rag_readme, force)

    print("Scaffolding completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold workspace environment (00_artifacts ~ 04_rag_database).")
    parser.add_argument("--target-dir", type=str, default=".", help="Target directory for scaffolding.")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing files.")
    
    args = parser.parse_args()
    
    target_path = Path(args.target_dir).resolve()
    scaffold(target_path, args.force)
