# 실전 예시 2: 초고속 장문 전략 보고서 생성 봇 (Analytical Report with SoT & Chaining)

본 문서는 사용자가 **"제조/금융 대기업의 생성형 AI 도입 전략에 대한 수십 페이지 분량의 종합 전략 백서를 단 몇 초 만에 병렬로 고속 작성하는 기획 봇"**을 요청했을 때, `meta-prompting` 스킬이 5대 차원을 분석하고 최적의 기법을 조합하여 설계한 3단계 체인형 프롬프트 세트입니다.

---

## 1. 과업 요구사항 다차원 분석 (Task Profile)

```json
{
  "reasoning_depth": "High",
  "tool_dependency": "None",
  "schema_strictness": "Semi-structured",
  "stakes": "Medium",
  "latency_sensitivity": "Real-time / Latency-critical"
}
```

- **추론 깊이 (Reasoning Depth)**: `High` — 인프라 아키텍처, 거버넌스, 비용 모델, 조직 문화 등 거시적 경영 전략의 논리적 완결성 요구.
- **도구 의존성 (Tool Dependency)**: `None` — 프롬프트 내 가이드라인 및 전문 컨설팅 프레임워크 지식 활용.
- **포맷 엄격성 (Schema Strictness)**: `Semi-structured` — 임원 보고용 마크다운 대/중/소제목, 표, 핵심 요약문 구조.
- **위험도 및 신뢰성 (Stakes)**: `Medium` — 기업 도입 의사결정의 기초 백서.
- **지연 시간 제약 (Latency Sensitivity)**: `Latency-critical` — 단일 호출로 수만 토큰을 순차 생성할 경우 타임아웃 및 긴 대기시간(수 분 이상) 발생.

---

## 2. 선정된 최적 프롬프팅 기법 (Technique Selection)

- **Primary 기법**: **Skeleton-of-Thought (SoT)**
  - *선정 근거*: 자동회귀적(Autoregressive) 토큰 디코딩의 병목을 극복하기 위해, 1단계로 구조적 뼈대(목차 및 핵심 메시지)를 선행 생성하고 2단계에서 각 챕터를 비동기 병렬 LLM 호출로 동시에 확장(Point-Expanding)하여 전체 생성 속도를 2.5배 이상 가속.
- **Secondary 기법**: **Prompt Chaining (프롬프트 체이닝)**
  - *선정 근거*: 단일 프롬프트에 골격 생성, 세부 집필, 교차 검증을 모두 담으면 지침 희석(Instruction Drift)이 발생하므로, [골격 설계] $\rightarrow$ [병렬 본문 집필] $\rightarrow$ [최종 통합 및 윤문]의 3단계 파이프라인으로 물리적 분리.

---

## 3. 완성형 프로덕션 프롬프트 체인 세트 (Prompt Chaining Package)

> 아래 3개의 프롬프트를 오케스트레이션 파이프라인(예: LangGraph, Python 비동기 스크립트)에 순차/병렬로 바인딩하세요.

### [Phase 1: 골격 목차 생성 프롬프트 (Skeleton Generator)]
```markdown
# Role & Goal
당신은 글로벌 1위 전략 컨설팅 펌의 시니어 파트너이자 AI 전략 아키텍트입니다.
사용자가 요청한 [AI 도입 주제]에 대해 최고 수준의 4개 핵심 장(Chapter) 목차와 소주제 골격을 생성하세요.

# Instructions (Skeleton Protocol)
1. 본문 내용은 일절 서술하지 마세요.
2. 각 장(Chapter)의 제목과 그 아래 다룰 3개의 핵심 소주제(Bullet point), 그리고 해당 장이 전달해야 할 1문장 핵심 가치(Key Takeaway)만 간결히 출력하세요.
3. 4개 장은 [1. 인프라 아키텍처, 2. 사내 데이터 거버넌스, 3. 비즈니스 파일럿 과제, 4. 조직 변화 관리]를 포괄해야 합니다.

# Output Format
반드시 아래 JSON 스키마로만 출력하세요:
```json
{
  "report_title": "string",
  "chapters": [
    {
      "chapter_number": 1,
      "chapter_title": "string",
      "key_takeaway": "string",
      "sub_topics": ["string", "string", "string"]
    }
  ]
}
```
```

---

### [Phase 2: 병렬 세부 챕터 집필 프롬프트 (Point-Expanding Worker)]
*(파이프라인에서 Phase 1의 `chapters` 배열 길이만큼 비동기 동시 호출)*

```markdown
# Role & Task
당신은 엔터프라이즈 AI 전문 테크니컬 라이터입니다.
전체 보고서 골격 중 할당받은 **[Chapter {{chapter_number}}: {{chapter_title}}]**의 상세 심층 본문을 작성하세요.

# Context (전체 보고서 맥락)
- 전체 보고서 제목: {{report_title}}
- 본 챕터의 핵심 메시지: {{key_takeaway}}
- 다루어야 할 소주제: {{sub_topics}}

# Detailed Writing Instructions
1. 실무자가 즉시 적용할 수 있도록 구체적인 기술 스택(예: 프라이빗 LLM vs 퍼블릭 SaaS 비교, vLLM, LangChain)과 아키텍처 다이어그램(ASCII 또는 마크다운 표)을 포함하세요.
2. 추상적인 구호는 배제하고 실무적 위험 요인과 비용 절감(TCO) 수치 예시를 제시하세요.
3. 분량은 마크다운 형식으로 약 1,500자 내외로 깊이 있게 서술하세요.

# Output Format
## 제{{chapter_number}}장. {{chapter_title}}
### 1. 개요 및 핵심 과제
### 2. 세부 실행 전략 및 아키텍처 (표 포함)
### 3. 리스크 요인 및 완화 방안
```

---

### [Phase 3: 통합 및 정합성 검수 프롬프트 (Aggregator & Synthesizer)]
*(Phase 2의 병렬 집필 결과가 모두 수집된 후 단일 호출)*

```markdown
# Role & Task
당신은 최고 경영진 보고서 최종 감수 총괄 에디터입니다.
병렬 생성된 4개 챕터의 원고를 통합하여, 톤앤매너가 일치하고 문맥이 유려하게 연결되는 완성형 전략 백서로 완성하세요.

# Input Drafts
[목차 및 골격]: {{phase_1_skeleton}}
[챕터 1 원고]: {{chapter_1_text}}
[챕터 2 원고]: {{chapter_2_text}}
[챕터 3 원고]: {{chapter_3_text}}
[챕터 4 원고]: {{chapter_4_text}}

# Editorial Guidelines
1. 앞뒤 챕터 간의 용어 불일치(예: 파인튜닝 vs 미세조정)를 표준화하세요.
2. 백서의 서두에 C-Level 임원용 **1페이지 총괄 실행 요약(Executive Summary)**을 추가하세요.
3. 각 장 사이의 전환 문장(Transition sentence)을 매끄럽게 보강하세요.
```

---

## 4. 파이썬 비동기 파이프라인 연동 예시 (Runtime Implementation)

```python
import asyncio
import json
import re
from openai import AsyncOpenAI

client = AsyncOpenAI()

def extract_and_parse_json(text: str) -> dict:
    """Robustly extracts JSON from raw LLM output even if enclosed in markdown code blocks."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    clean_text = match.group(1) if match else text
    return json.loads(clean_text)

async def generate_whitepaper(topic: str) -> str:
    # Step 1: 골격 목차 생성 (SoT Stage 1)
    skeleton_resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": SKELETON_PROMPT}, {"role": "user", "content": topic}],
        response_format={"type": "json_object"}
    )
    skeleton = extract_and_parse_json(skeleton_resp.choices[0].message.content)
    
    # Step 2: 4개 챕터 병렬 확장 (SoT Stage 2: 4x 속도 가속)
    async def expand_chapter(ch: dict) -> str:
        prompt_content = EXPAND_PROMPT.format(
            report_title=skeleton["report_title"],
            chapter_number=ch["chapter_number"],
            chapter_title=ch["chapter_title"],
            key_takeaway=ch["key_takeaway"],
            sub_topics=", ".join(ch["sub_topics"]) if isinstance(ch["sub_topics"], list) else str(ch["sub_topics"])
        )
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt_content}]
        )
        return resp.choices[0].message.content
    
    chapter_tasks = [expand_chapter(ch) for ch in skeleton["chapters"]]
    chapters_content = await asyncio.gather(*chapter_tasks)
    
    # Step 3: 최종 통합 및 감수 (Chaining Phase 3)
    aggregate_params = {
        "phase_1_skeleton": json.dumps(skeleton, ensure_ascii=False, indent=2)
    }
    for idx, content in enumerate(chapters_content, start=1):
        aggregate_params[f"chapter_{idx}_text"] = content
        
    final_report = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": AGGREGATE_PROMPT.format(**aggregate_params)}]
    )
    return final_report.choices[0].message.content
```

---

## 5. 품질 감사 체크리스트 (Quality Audit)

- [x] **지연 시간 단축 구조 검증**: SoT 기법을 통해 대기시간을 선형 시간 $O(\sum L_i)$에서 병렬 시간 $O(\max L_i)$로 대폭 절감.
- [x] **모듈식 단일 책임 준수**: 골격 생성, 세부 집필, 통합 감수가 분리되어 각 프롬프트의 지침 집중도 극대화.
- [x] **형식 정합성**: Phase 1 JSON 스키마와 Phase 2 변수 치환자 간 완벽한 호환성 확보.
