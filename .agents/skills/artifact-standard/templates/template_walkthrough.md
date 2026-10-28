# [Walkthrough] [작업 완료 주제명을 명사형으로 명확히 작성]

> **문서 메타데이터**  
> - **완료일**: YYYY-MM-DD | **작업자**: [작성자/에이전트명]  
> - **기준 계획서**: [plan_001_([주제명])_[YYMMDD]_rev00.md](../plans/plan_001_([주제명])_[YYMMDD]_rev00.md)  
> - **선행 리포트**: [report_001_([주제명])_[YYMMDD]_rev00.md](../reports/report_001_([주제명])_[YYMMDD]_rev00.md) <!-- 선행 분석 리포트가 있을 경우 링크 -->  
> - **커밋 / PR**: [Git Commit Hash 또는 PR 링크]  
> - **달성도**: 100% 완료 <!-- 또는 진행 중(WIP), N% 완료 -->  
> - **문서 모드**: Standard (전체 보고) <!-- 또는 Lightweight (소규모 패치 보고) -->  
> - **문서 상태**: Final (확정) <!-- 또는 Draft (검증 대기 중) -->

---

## 1. 작업 개요 (Executive Summary)
*완료된 작업의 핵심 내용과 계획 대비 달성 성과를 2~3줄로 명확히 요약합니다.*

- **작업 목적**: [기준 계획서에서 정의된 주요 목표 재확인]
- **주요 성과**:
  - [성과 1: 구현 완료된 기능 또는 성능 개선 수치]
  - [성과 2: 계획 대비 예외 처리 또는 특이사항 대응 결과]
- **계획 대비 달성률**: 100% (모든 필수 요구사항 및 검증 시나리오 통과)

---

## 2. 핵심 변경 내역 (Key Implementation Changes)
*실제 코드베이스 및 시스템에 적용된 변경 사항을 파일 단위와 핵심 로직 단위로 기술합니다.*

### 1) 변경된 파일 목록 (File Change List)
| 구분 (신규/수정/삭제) | 파일/리소스 경로 | 주요 변경 역할 |
| :---: | :--- | :--- |
| 신규 | `src/services/new_feature.py` | [신규 비즈니스 서비스 로직 레이어 구현] |
| 수정 | `src/api/routes.py` | [신규 엔드포인트 라우팅 및 파라미터 매핑] |
| 수정 | `src/core/config.py` | [환경변수 및 기본 설정값 확장] |
| 삭제 | `src/legacy/old_module.py` | [사용 중단된 레거시 모듈 안전 제거] |

### 2) 주요 구현 및 아키텍처 변경 상세
- **[`ClassName`](file:///path/to/file.py#L10-L45)**:
  - [핵심 로직 변경점 설명, 사용된 디자인 패턴 또는 알고리즘 개선 내역]
- **인터페이스 및 데이터 구조**:
  - [입출력 DTO 변경, DB 스키마 마이그레이션 또는 API 스펙 변경점]

---

## 3. 검증 결과 및 증적 (Verification Evidence)
*변경 사항이 의도대로 동작하며 부작용이 없음을 입증하는 객관적인 증적(로그, 수치, 테스트 결과)을 제시합니다.*

### 1) 테스트 실행 커맨드 및 터미널 출력
```bash
# 실행한 테스트 명령어
pytest tests/unit/test_feature.py -v
```
```text
============================= test session starts =============================
collected 6 items

tests/unit/test_feature.py::test_normal_case PASSED                      [ 16%]
tests/unit/test_feature.py::test_missing_param_validation PASSED         [ 33%]
tests/unit/test_feature.py::test_boundary_value_handling PASSED          [ 50%]
tests/unit/test_feature.py::test_concurrent_requests PASSED              [ 66%]
tests/unit/test_feature.py::test_error_fallback_recovery PASSED          [ 83%]
tests/unit/test_feature.py::test_performance_threshold PASSED           [100%]

============================== 6 passed in 0.84s ==============================
```

### 2) 정상 및 엣지 케이스 검증 매트릭스
| 검증 시나리오 | 입력 조건 / 테스트 데이터 | 기대 결과 | 실제 결과 | 판정 |
| :--- | :--- | :--- | :--- | :---: |
| **정상 처리 흐름** | 유효한 페이로드 요청 전송 | 200 OK & 응답 데이터 일치 | 정상 반환 확인 | **PASS** |
| **필수값 누락 예외** | `required_id` 누락 | 400 Bad Request & 에러 메시지 | 400 에러 포맷 확인 | **PASS** |
| **경계값 처리** | 허용 최대치 `limit=10,000` | OOM 없이 페이징 정상 처리 | 120ms 내 반환 확인 | **PASS** |
| **장애 롤백 복구** | 강제 네트워크 타임아웃 주입 | 트랜잭션 롤백 및 오류 로그 | DB 롤백 무결성 확인 | **PASS** |

---

## 4. 실무 산출물 연계 (Deliverables & Assets)
*작업 과정에서 생성된 비-마크다운 실무 자산(`02_output_data/`)을 링크하여 추적성을 보장합니다.*

<!-- 해당 작업에서 생성된 파일 링크만 남기고 나머지는 제거합니다 -->
- **1단계 가공·해석 데이터 (`00_data/`)**:
  - CSV 데이터셋: [`02_output_data/00_data/csv_001_([주제명])_[YYMMDD]_rev00.csv`](../../02_output_data/00_data/)
  - Excel 스프레드시트: [`02_output_data/00_data/excel_001_([주제명])_[YYMMDD]_rev00.xlsx`](../../02_output_data/00_data/)
- **2단계 시각화·로그 (`01_figure/`)**:
  - 다이어그램 / 화면 이미지: [`02_output_data/01_figure/image_001_([주제명])_[YYMMDD]_rev00.png`](../../02_output_data/01_figure/)
  - 시각화 플롯 차트: [`02_output_data/01_figure/plot_001_([주제명])_[YYMMDD]_rev00.png`](../../02_output_data/01_figure/)
  - 솔버 실행 로그: [`02_output_data/01_figure/log_001_([주제명])_[YYMMDD]_rev00.trn`](../../02_output_data/01_figure/)
- **3단계 최종 보고서 (`02_reports/`)**:
  - 기술 보고서 / 슬라이드: [`02_output_data/02_reports/pdf_001_([주제명])_[YYMMDD]_rev00.pdf`](../../02_output_data/02_reports/)

---

## 5. 배포 및 엔지니어링 가이드 (Deployment Notes)
*작업 내용을 실제 운영/배포 환경에 적용할 때 엔지니어가 반드시 알아야 할 주의사항입니다.*

> [!NOTE]  
> - **신규 환경변수**: `.env` 파일에 `NEW_FEATURE_ENABLED=true` 추가 필요  
> - **의존성 라이브러리**: `pip install -r requirements.txt` (신규 패키지 추가 여부)  
> - **DB 마이그레이션**: `alembic upgrade head` 실행 필수  
> - **하위 호환성 (Breaking Changes)**: 없음 (기존 API 엔드포인트 100% 하위 호환 유지)

---

<!-- 
[예외 처리 가이드]
1. 대체 증적 (Alternative Evidence):
   단위 테스트 프레임워크가 없는 환경일 경우, 아래와 같이 수동 실행 로그 및 화면 스크린샷으로 대체합니다:
   > [!NOTE]
   > 대체 증적 적용: 자동화 단위 테스트 미구축 환경으로, 수동 CLI 실행 터미널 출력 및 UI 스크린샷(02_output_data/01_figure/)으로 검증 대체.
2. Lightweight 모드 (소규모 패치):
   긴급 핫픽스나 단일 파일 패치일 경우, 1. 작업 개요, 2. 변경된 파일 목록, 3. 검증 결과의 3개 섹션으로 압축 작성합니다.
3. Draft / WIP 상태 (장시간 연산):
   배치/시뮬레이션 연산 중일 경우 상태를 Draft로 표기하고 <!-- TODO: 연산 완료 후 P-Q 수치 갱신 --> 처리합니다.
-->
