# Proactive Insights 기능 아이디어 검토 요청

## 배경

저는 LangGraph 기반 데이터 분석 에이전트를 개발하고 있습니다. 챌린지 요구사항 중 하나가 "**A feature where the agent proactively uncovers and presents interesting insights about the dataset**"입니다.

현재 시스템은 **reactive**(반응형)로 작동합니다:
- 사용자가 질문 → SQL 생성 → 실행 → 답변 반환
- 사용자가 요청한 것만 처리

## 요구사항 해석

챌린지 문서에서:
1. **"proactively"** = 사용자가 요청하지 않아도 자동으로
2. **"uncovers"** = 데이터에서 패턴/이상치를 발견
3. **"interesting insights"** = 단순 통계가 아닌 의미있는 발견
4. **"Optional examples of insights discovered by the agent"** (데모 비디오 요구사항)

평가 기준:
- "engineering judgment and curiosity"
- "how you think, structure problems, and evolve solutions"

## 제약 조건

1. **Dataset-agnostic**: 데이터셋이 바뀌어도 작동해야 함 (하드코딩 불가)
2. **Schema-driven**: `schema_info.json`과 `data_profile.json` 활용
3. **LangGraph 워크플로우**: 기존 그래프에 노드 추가 필요
4. **구현 시간**: 2-4시간 내 구현 가능해야 함

## 현재 고민 중인 구현 옵션

### 옵션 A: 첫 접속 시 자동 실행
**트리거**: 사용자가 "Hello" 또는 첫 질문 입력 시

**동작**:
```
사용자: "안녕하세요"
에이전트:
  "👋 안녕하세요! 데이터셋을 분석한 결과:

  📊 데이터 개요:
  - 1,247건 거래, 328명 고객, 58개 매장
  - 기간: 2024년 1월~12월

  💡 주요 발견:
  1. 12월 매출이 평균 대비 284% 급증 (계절성 패턴)
  2. 상위 20% 고객이 전체의 78% 차지 (파레토)
  3. XXL 매장이 평균 거래액 3.2배 높음
  4. 3건의 이상 고액 거래 발견 (평균의 50배)

  무엇이든 물어보세요!"
```

**장점**:
- 진짜 "proactive" (자동 실행)
- 구현 간단
- 첫인상 강렬

**단점**:
- 한 번만 실행
- 사용자가 관심 없을 수도

---

### 옵션 B: 맥락 기반 연관 인사이트
**트리거**: 사용자 질문에 답변 후, 관련 추가 인사이트 제공

**동작**:
```
사용자: "상위 5개 고객 보여줘"
에이전트:
  [테이블 표시]

  💡 연관 인사이트:
  "상위 5명이 전체 매출의 67%를 차지합니다.
   이 중 3명은 XXL 매장에서만 구매했습니다.
   구매 빈도가 일반 고객의 8배입니다."
```

**장점**:
- 맥락 관련성 높음
- 자연스러운 대화
- 여러 번 기회

**단점**:
- 언제 추가할지 판단 로직 복잡
- 과도하면 annoying
- 구현 시간 오래 걸림

---

### 옵션 C: 하이브리드 (A + 명시적 트리거)
**트리거 1**: 첫 접속 시 자동
**트리거 2**: "인사이트 보여줘", "뭐 재미있는 거 없어?" 등 입력 시

**동작**: 옵션 A와 동일하지만, 나중에도 다시 볼 수 있음

**장점**:
- proactive + 사용자 제어권
- 유연함

**단점**:
- 명시적 요청은 완전히 "proactive"는 아님

---

### 옵션 D: N번째 질문마다 주기적 제안
**트리거**: 사용자가 3번 질문할 때마다 자동으로 전체 인사이트 제공

**장점**:
- 주기적으로 상기
- 너무 자주 안 나옴

**단점**:
- 타이밍이 부자연스러울 수 있음
- 맥락 무관

---

## 인사이트 탐지 방법 (Dataset-Agnostic)

### 1. 통계 기반 패턴 탐지
```python
def detect_insights(schema_info, data_profile):
    insights = []

    # 1. 이상치 (Outliers): Z-score > 3
    # 2. 급증/급락: 시간 데이터에서 >200% 변화
    # 3. 파레토 법칙: 상위 20%가 80% 차지
    # 4. 카테고리별 큰 차이: >3x 표준편차
    # 5. 결측치/데이터 품질 이슈

    return insights
```

**장점**:
- 완전히 dataset-agnostic
- 수학적으로 객관적
- 빠른 실행

**단점**:
- 비즈니스 의미 부족
- 모든 패턴이 "흥미로운" 건 아님

### 2. LLM 기반 해석 추가
```python
# 통계 패턴 발견 후
llm_prompt = f"""
다음 통계 패턴을 분석하고 비즈니스 인사이트로 변환하세요:
{statistical_patterns}

다음 형식으로 답변:
- 발견 내용
- 가능한 원인
- 비즈니스 의미
"""
```

**장점**:
- 비즈니스 맥락 추가
- 해석이 풍부함

**단점**:
- LLM 호출 비용/시간
- 환각 가능성

---

## 구현 복잡도 비교

| 옵션 | 구현 시간 | 코드 복잡도 | Dataset-Agnostic | Proactive 정도 |
|------|----------|------------|-----------------|---------------|
| A (첫 접속) | 2시간 | 낮음 | ✅ 가능 | ⭐⭐⭐ 높음 |
| B (맥락 기반) | 4-6시간 | 높음 | ✅ 가능 | ⭐⭐ 중간 |
| C (하이브리드) | 2-3시간 | 중간 | ✅ 가능 | ⭐⭐ 중간 |
| D (주기적) | 2시간 | 낮음 | ✅ 가능 | ⭐⭐ 중간 |

---

## 질문

다음 관점에서 조언을 부탁드립니다:

1. **요구사항 해석**: 제가 "proactively uncovers and presents interesting insights"를 올바르게 이해했나요? 다른 해석 가능성은 없나요?

2. **구현 방향**: 위 옵션 중 어떤 것이 요구사항의 의도에 가장 부합할까요?

3. **차별화**: 평가자가 "engineering judgment and curiosity"를 보기 위해서는 어떤 요소가 중요할까요?

4. **개선 아이디어**: 제가 고려하지 못한 다른 접근 방법이 있을까요?

5. **우선순위**: 시간 제약(2-4시간)을 고려할 때, 최소한 구현해야 할 핵심 기능은 무엇일까요?

---

## 추가 정보

**현재 시스템 구조**:
- LangGraph StateGraph 기반
- 노드: intent_classification → generate_SQL → execute_SQL → visualisation → pyodide → generate_response
- 데이터: CSV 파일 → PostgreSQL
- 메타데이터: schema_info.json, data_profile.json 활용 가능

**평가 기준 (PDF에서)**:
- "Design and build robust, innovative agentic systems"
- "Solve real engineering problems"
- "Demonstrate strong engineering judgment"

감사합니다!
