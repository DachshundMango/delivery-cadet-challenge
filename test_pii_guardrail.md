# PII Guardrail Test Plan

## Test Cases

### 1. 이름이 포함된 쿼리
```bash
python3 src/main.py
> What are the first and last names of customers in the database?
```
**Expected**: `[NAME_REDACTED]`가 표시되어야 함

### 2. 집계 쿼리 (이름 없음)
```bash
> How many transactions were there in total?
```
**Expected**: 정상 숫자 응답 (마스킹 없음)

### 3. Join 쿼리
```bash
> Show me customer names who made purchases
```
**Expected**: `[NAME_REDACTED]`로 마스킹

## LangSmith 확인

1. https://smith.langchain.com/ 접속
2. `delivery-cadet-challenge` 프로젝트 선택
3. 각 쿼리별 trace 확인:
   - `mask_pii_in_query_result` 출력
   - `generate_response` 최종 응답

## Dataset-Agnostic 검증

새로운 데이터셋으로 교체 시:
- `keys.json` 수정만으로 작동
- `nodes.py` 수정 불필요
