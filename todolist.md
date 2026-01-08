# To Do

## High Priority

- [ ] 바 차트만 생성되는 문제 해결 (line/pie 차트 선택 로직 개선)
- [ ] pyodide 확인

## Future Improvements

- [ ] 데이터 파이프라인 자동화 개선 (취소/롤백 기능)
- [ ] Data-agnostic 원칙 위반 사항 전체 점검 (prompts.py 예시 일반화)

---

# Completed

- [x] Plotly 차트 디테일 개선 (동적 제목/축 레이블, 헤더 숨김, 60자 제한)
- [x] LLM Provider 변경 (Groq → Cerebras, llama-3.3-70b)
- [x] 시각화 과도 생성 문제 수정 (명시적 키워드 기반 판단)
- [x] LaTeX 렌더링 이슈 수정 (달러 사인 이스케이프)
- [x] Insight 항상 생성되도록 수정
- [x] CoT + XML 구조화 + Temperature 튜닝 적용
- [x] 불필요한 예외처리 정리 (11개 수정 완료)
- [x] 프롬프트 토큰 최적화 (20-25% 토큰 절감 완료)
- [x] 추가 데이터 적용하기
- [x] plotly 비주얼 변화 에러 수정
- [x] Unknown tables in query 이슈
- [x] insights.json 제거
- [x] 주석 정리 및 코드 문서화
