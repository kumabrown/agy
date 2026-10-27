---
name: rag-builder
description: 01_input_data 멀티포맷(PDF, Word, PPT, Excel, Text) 실무 자료를 자동 스캔하여 문서별 전용 디렉터리(04_rag_database/<target_id>/)에 ChromaDB 및 BM25 하이브리드 RAG를 자가 완결형으로 구축하고, 질문에 대한 근거 출처 및 추출 도면/그래프 링크를 인용하여 답변을 생성합니다. 사용자가 "RAG 만들어줘", "자료 색인해줘", 또는 01_input_data 자료에 대한 기술적 질의를 할 때 활성화합니다.
---

# RAG Builder Skill (LangChain · ChromaDB · BGE-M3)

이 스킬은 `01_input_data/`(`00_received/`, `01_references/`) 내 다양한 실무 엔지니어링 자료(PDF 매뉴얼, 구매사양서 Word, 발표자료 PPTX, 데이터 시트 Excel, 스크립트 Text)를 구조적으로 파싱 및 색인하고, **`04_rag_database/<target_id>/` 전용 디렉터리 내에 벡터 DB, BM25 인덱스, 매니페스트, 그리고 추출된 도면/차트 이미지(`images/`)를 하나의 패키지로 완전 격리 구축**합니다. 질의응답 시에는 **정확한 원천 출처 표기**와 **자가 완결형 도면/차트 이미지 링크**를 함께 렌더링합니다.

---

## 🎯 발동 조건 (Trigger Conditions)

1. **RAG 구축/갱신 요청**:
   - 사용자가 *"RAG 만들어줘"*, *"문서 색인해줘"*, *"자료 인덱싱해줘"*, *"RAG 빌드해줘"* 등의 명령을 내릴 때
   - `01_input_data/`에 새로운 문서가 추가되었거나 변경되어 특정 문서에 대한 RAG 인덱스를 생성/업데이트해야 할 때
2. **실무 자료 기반 질의응답**:
   - `01_input_data/`에 저장된 사양서, Fluent 매뉴얼, UDF 가이드, PPT 템플릿, Excel 데이터에 대한 구체적인 기술 질문이 들어올 때

---

## 📂 저장소 구조 (문서별 캡슐화 격리 표준)

모든 RAG 지식 자산은 `04_rag_database/` 하위에 문서(타깃)별로 독립 패키지화되어 영속화됩니다:

```text
04_rag_database/
├── README.md                      # 전체 RAG 타깃 인덱스 테이블 (자동 동기화)
├── index_catalog.json             # 중앙 레지스트리 (타깃 ID, 메타데이터, 청크 수)
├── file_cache.json                # 01_input_data/ 원천 파일들의 SHA-256 증분 캐시
├── .gitignore                     # 대용량 바이너리 DB(*.sqlite3, *.parquet, *.pkl) 자동 제외
│
├── [문서_타깃_A_디렉터리]/             # 문서 A 전용 독립 RAG 패키지
│   ├── chroma/                    # 해당 문서의 ChromaDB 벡터 컬렉션
│   ├── bm25_index.pkl             # 해당 문서의 BM25 키워드 역색인 인덱스
│   ├── manifest.json              # 청크 메타데이터, 원천 파일 목록, 파싱 통계
│   └── images/                    # 해당 문서에서 추출된 고해상도 도면/차트 이미지 자산
│       ├── image_001_(...)_rev00.png
│       └── image_002_(...)_rev00.png
│
└── [문서_타깃_B_디렉터리]/             # 문서 B 전용 독립 RAG 패키지
    ├── chroma/
    ├── bm25_index.pkl
    ├── manifest.json
    └── images/
```

---

## 🔄 워크플로우 (Workflow Steps)

### Step 1. RAG 타깃 확인 및 독립 구축 (Build / Multi-Target Build)
인덱스가 구축되어 있지 않거나 특정 파일/주제별로 독립 RAG 생성을 원할 때 CLI를 사용합니다:

```bash
# [단일 문서 전용 RAG 타깃 구축]
python .agents/skills/rag-builder/scripts/build_rag.py --file "Theory_Guide" --target "fluent_theory_guide" --name "Fluent Theory Guide 2024"

# [특정 구매사양서 Word 문서 전용 RAG 구축]
python .agents/skills/rag-builder/scripts/build_rag.py --file "구매사양서" --target "procurement_spec_boiler" --name "포항 형산발전 보일러 구매사양서"

# [등록된 타깃 목록 확인 및 무결성 점검]
python .agents/skills/rag-builder/scripts/manage_rag.py list
```

---

### Step 2. 정밀 타깃 검색 및 연합 검색 (Query Execution)
사용자의 자연어 질문 목적에 따라 타깃 정밀 검색 또는 전체 연합 횡단 검색을 실행합니다:

```bash
# 1. 특정 문서 타깃 대상 정밀 검색 (0.05초 초고속, 노이즈 0%)
python .agents/skills/rag-builder/scripts/query_rag.py -q "discrete ordinates radiation model equations" --target "fluent_theory_guide"

# 2. 전체 타깃 횡단 연합 검색 (Federated Cross-Target Search)
python .agents/skills/rag-builder/scripts/query_rag.py -q "UDF DEFINE_PROFILE macro boundary condition" --federated

# 3. 기본 검색 (Top-K 지정)
python .agents/skills/rag-builder/scripts/query_rag.py -q "형산발전 12호기 복사열전달 모델링 격자망 요구조건" -k 3
```

- 검색 결과로 전달되는 상위 청크 내용, 출처 파일명, 페이지/슬라이드 위치, 인접 도면 이미지 링크를 취합합니다.

---

### Step 3. 신뢰도 높은 답변 및 출처·도면 링크 렌더링 (Response Generation)
사용자에게 답변할 때는 **반드시 검색된 컨텍스트만을 근거로 작성**하며, 답변 하단에 아래 표준 양식에 맞추어 **해당 문서 전용 디렉터리(`04_rag_database/<target_id>/images/`) 내 추출 도면/차트 이미지 파일 링크**와 **근거 자료 출처**를 명시합니다:

```markdown
포항 형산발전 12호기 보일러 연소 및 복사열전달 수치해석 용역의 주요 격자망 요구조건은 다음과 같습니다:
- **격자수**: 최소 1,200만 노드 이상의 정밀 격자망 구성
- **화염 및 노벽 부근**: 복사열전달 특성을 정확히 모사하기 위해 국소 격자 조밀화 적용
- **형상 모델링**: 버너 노즐 및 과열기 튜브 번들 정밀 반영

📌 **[관련 도면 및 그래프 자산]**
- 연소로 형상 및 격자 배치도: [image_001_(procurement_spec_p5_img01)_261028_rev00.png](file:///c:/work_dir/my_agy/04_rag_database/procurement_spec_boiler/images/image_001_(procurement_spec_p5_img01)_261028_rev00.png)

📌 **[근거 자료 출처]**
- 문서: `01_input_data/00_received/261001_연구지원_구매사양서 (외주용역, 복사열전달).docx` [Page 5] (2.2 과업 범위 및 격자 사양)
```

---

## ⚠️ 주의사항 및 가이드라인
1. **외부 API 호출 금지**: 임베딩은 100% 로컬 구동되는 `BGE-M3 (1024차원)`를 사용하므로 API Rate Limit이나 토큰 비용 걱정 없이 대량 문서를 안전하게 처리합니다.
2. **원천 자료 불변성 보존**: `01_input_data/`(`00_received/`, `01_references/`) 내부의 원본 파일은 절대 임의로 수정하거나 삭제하지 않습니다.
3. **완전 격리 원칙**: RAG 인덱스와 추출 이미지는 오직 **`04_rag_database/<target_id>/`** 내부에 완결형으로 저장되며, `04_rag_database/README.md` 인덱스에 타깃이 자동 등록·동기화됩니다.
