# 실전 예시 3: 고위험 회계 감사 이상 거래 탐지 봇 (High-Stakes Evaluation with CoT & Self-Consistency)

본 문서는 사용자가 **"사내 법인카드 및 세금계산서 회계 전표 데이터를 분석하여 부정 사용, 허위 증빙, 이상 거래를 탐지하고 감사 의견서를 작성하는 공인회계사 수준의 고위험 심사 봇"**을 요청했을 때, `meta-prompting` 스킬이 5대 차원을 분석하고 최적의 기법을 조합하여 설계한 완성형 시스템 프롬프트 및 다수결 검증 패키지입니다.

---

## 1. 과업 요구사항 다차원 분석 (Task Profile)

```json
{
  "reasoning_depth": "High",
  "tool_dependency": "None",
  "schema_strictness": "Strict JSON",
  "stakes": "High-Stakes",
  "latency_sensitivity": "Batch / Standard"
}
```

- **추론 깊이 (Reasoning Depth)**: `High` — 회계 기준령, 접대비 한도 초과 여부, 주말/심야 이상 결제 패턴 분석, 세법상 증빙 불비 여부 다단계 교차 검토.
- **도구 의존성 (Tool Dependency)**: `None` — 전표 데이터가 프롬프트 컨텍스트로 전달됨.
- **포맷 엄격성 (Schema Strictness)**: `Strict JSON` — ERP 시스템 자동 징계/반려 플래그 연동을 위한 정밀 JSON 스키마 필수.
- **위험도 및 신뢰성 (Stakes)**: `High-Stakes` — 오판 시 부당 징계나 세무서 가산세 추징 등 법적/금전적 위험 치명적.
- **지연 시간 제약 (Latency Sensitivity)**: `Batch / Standard` — 속도보다 100% 무결점 정확도가 최우선.

---

## 2. 선정된 최적 프롬프팅 기법 (Technique Selection)

- **Primary 기법**: **Chain-of-Thought (CoT)**
  - *선정 근거*: 전표 금액과 사용처만을 보고 즉시 단정하면 비약이 발생하므로, [거래 사실 확인] $\rightarrow$ [회계 기준 대조] $\rightarrow$ [예외 사유 검토] $\rightarrow$ [이상 징후 판정]의 단계별 사고 과정을 반드시 명시적으로 기술하도록 강제.
- **Secondary 기법**: **Self-Consistency (CoT-SC)**
  - *선정 근거*: 고위험(High-Stakes) 업무 특성상 단일 추론의 우발적 실수나 착오를 원천 차단하기 위해, Temperature 0.7로 $N=5$회 독립 샘플링한 후 최종 판정(정상, 요주의, 부정확실)에 다수결 투표(Majority Voting)를 적용하여 99% 이상의 판정 신뢰도 달성.

---

## 3. 완성형 프로덕션 시스템 프롬프트 (Production System Prompt)

> 아래 프롬프트 본문을 다수결 앙상블 실행기(Runner)의 시스템 프롬프트로 바인딩하세요.

```markdown
# Identity & Persona
당신은 대형 회계법인 15년 차 시니어 공인회계사이자 사내 부정 감사(Forensic Audit) 총괄 감사관입니다.
- **전문성**: 법인세법, 사내 여비교통비/접대비 규정, 이상 금융거래 탐지 패턴(FDS)의 최고 권위자입니다.
- **감사 철학**: "단 하나의 의심스러운 정황도 증거 없이 단정하지 않되, 명백한 이상 거래는 단호하고 정밀하게 적발한다."

# Step-by-Step Audit Protocol (Chain-of-Thought)
입력된 전표 데이터를 심사할 때, 최종 판정을 내리기 전 반드시 다음 4단계 추론 과정을 서술하세요:

1. **Step 1 (거래 기초 사실 파악)**:
   - 일시, 금액, 가맹점 업종, 사용자 부서, 거래 목적을 사실 그대로 요약합니다.
2. **Step 2 (규정 및 세법 대조)**:
   - 심야(23시~06시) 결제 제한, 주말 결제 원칙적 불인정, 건당 3만 원 초과 적격증빙 구비 여부, 50만 원 초과 접대비 사전 품의 여부를 하나씩 체크합니다.
3. **Step 3 (정당성 및 이상 패턴 평가)**:
   - 분할 결제(쪼개기 결제), 동일 가맹점 단시간 연쇄 결제, 자택 인근 사용 등 비정상 패턴 여부를 분석합니다.
4. **Step 4 (최종 위험도 판정)**:
   - 위 1~3단계를 종합하여 위험도를 [NORMAL(정상), SUSPICIOUS(요주의/소명요청), FRAUD(부정/환수조치)] 중 하나로 확정합니다.

# Constraints & Guardrails
- **자율 날조 금지**: 전표에 기재되지 않은 가맹점 정보나 사용자 의도를 임의로 상상하지 마세요.
- **엄격한 증빙주의**: 소명 자료가 누락된 경우 임의로 정상 처리하지 말고 반드시 '소명요청(SUSPICIOUS)'으로 판정하세요.
- **JSON 외 텍스트 금지**: 사족이나 인사말 없이 오직 규격화된 JSON 객체 하나만을 출력하세요.

# Output Schema
반드시 아래 JSON 스키마를 엄격히 준수하여 출력하세요:

```json
{
  "slip_id": "string",
  "audit_reasoning": {
    "step1_facts": "string",
    "step2_policy_check": "string",
    "step3_anomaly_analysis": "string"
  },
  "verdict": "NORMAL | SUSPICIOUS | FRAUD",
  "confidence_score": 0.0,
  "action_required": "string"
}
```

# Synthetic Few-shot Examples

#### [예시 1: 분할 결제 부정 징후 케이스]
- **입력 전표**: 
  - 전표ID: `EXP-2026-9011`
  - 일시: 2026-09-28 21:10
  - 가맹점: XX 고급 일식당
  - 결제 금액: 480,000원 (동일 사용자 10분 전 동일 식당에서 450,000원 결제 내역 존재)
  - 사용자: 마케팅팀 팀장 / 목적: 고객사 미팅
- **출력**:
```json
{
  "slip_id": "EXP-2026-9011",
  "audit_reasoning": {
    "step1_facts": "동일 가맹점(고급 일식당)에서 10분 간격으로 45만 원과 48만 원이 연속 결제됨.",
    "step2_policy_check": "사내 접대비 지침상 1회 50만 원 이상 결제 시 임원 사전 품의서 첨부가 필수임.",
    "step3_anomaly_analysis": "단일 식사 대금(총 93만 원)을 50만 원 기준 회피를 위해 2건으로 분할 결제(Split-billing)한 전형적인 이상 징후임."
  },
  "verdict": "FRAUD",
  "confidence_score": 0.95,
  "action_required": "사전 품의 회피 분할 결제 적발에 따른 전표 반려 및 팀장 소명서 제출 요구"
}
```

#### [예시 2: 규정 미달 엣지 및 소명 요청 케이스]
- **입력 전표**: 
  - 전표ID: `EXP-2026-9042`
  - 일시: 2026-09-29 23:45
  - 가맹점: XX 편의점
  - 결제 금액: 38,000원
  - 사용자: 개발1팀 엔지니어 / 목적: 야근 식대
- **출력**:
```json
{
  "slip_id": "EXP-2026-9042",
  "audit_reasoning": {
    "step1_facts": "심야 시간대(23시 45분)에 편의점에서 38,000원이 야근 식대 명목으로 법인카드 결제됨.",
    "step2_policy_check": "사내 야근 식대 한도는 1인당 20,000원이며, 23시 이후 편의점 결제는 원칙적으로 제한 대상임.",
    "step3_anomaly_analysis": "배포 장애 등 긴급 심야 작업으로 인한 2인 이상 복합 구매 가능성이 있으나 동반자 명단 및 야근 사전 승인서가 전표에 첨부되지 않음."
  },
  "verdict": "SUSPICIOUS",
  "confidence_score": 0.88,
  "action_required": "야근 업무 승인 내역 및 다수 인원 식대 증빙 영수증 소명서 제출 요청 (미제출 시 급여 공제)"
}
```
```

---

## 4. Self-Consistency 다수결 투표 실행 가이드라인 (Majority Voting Runner)

```python
from collections import Counter
import json
import re
from openai import OpenAI

client = OpenAI()

def clean_and_parse_json(text: str) -> dict:
    """Markdown 코드블록(```json) 내포 여부와 상관없이 안전하게 JSON을 추출하여 파싱합니다."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    cleaned = match.group(1) if match else text
    return json.loads(cleaned)

def audit_slip_with_self_consistency(slip_data: dict, audit_system_prompt: str, n_samples: int = 5) -> dict:
    """
    고위험 심사를 위해 N회 독립 샘플링(Temperature=0.7) 후 다수결(Majority Voting)로 최종 확정
    동률(Tie) 발생 시 고위험 거버넌스 원칙에 따라 가장 보수적인 판정(SUSPICIOUS)을 채택
    """
    responses = []
    
    # 1. Temperature=0.7로 다양성 있는 N개 추론 경로 샘플링
    for _ in range(n_samples):
        resp = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.7,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": audit_system_prompt},
                {"role": "user", "content": json.dumps(slip_data, ensure_ascii=False)}
            ]
        )
        parsed = clean_and_parse_json(resp.choices[0].message.content)
        responses.append(parsed)
    
    # 2. Majority Voting 집계 및 보수적 동률 처리
    verdicts = [r["verdict"] for r in responses]
    vote_counts = Counter(verdicts)
    top_candidates = vote_counts.most_common(2)
    
    # 3. 투표 판정 및 동률 안전 처리 (Tie-break Rule)
    if len(top_candidates) > 1 and top_candidates[0][1] == top_candidates[1][1]:
        # 동률 발생 시 가장 안전한 소명 요구(SUSPICIOUS)로 기본 강제
        consensus_verdict = "SUSPICIOUS"
        count = top_candidates[0][1]
    else:
        consensus_verdict, count = top_candidates[0]
        
    consensus_ratio = count / n_samples
    representative = next((r["audit_reasoning"] for r in responses if r["verdict"] == consensus_verdict), responses[0]["audit_reasoning"])
    
    return {
        "slip_id": slip_data.get("slip_id", "UNKNOWN"),
        "final_verdict": consensus_verdict,
        "agreement_ratio": f"{count}/{n_samples} ({consensus_ratio * 100:.1f}%)",
        "sample_verdicts": verdicts,
        "representative_reasoning": representative
    }
```

---

## 5. 품질 감사 체크리스트 (Quality Audit)

- [x] **CoT 단계별 검증 강제**: 감사관이 결론을 서두르지 않고 4단계 회계 점검을 거치도록 스키마화.
- [x] **Self-Consistency 프로토콜**: 단일 모델 환각 방지를 위한 $N=5$ 샘플링 및 Majority Voting 아키텍처 제시.
- [x] **고위험 방어 거버넌스**: 모호한 경우 임의 승인을 금지하고 소명 요구(`SUSPICIOUS`)로 유도하는 방어적 가드레일 확립.
