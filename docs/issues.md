순서,이슈 (Issue),원인 (Cause),해결책 (Solution),상태
1,DB 접속 불가,Docker 컨테이너 중지됨,컨테이너 재가동 및 .env 설정 확인,✅ 완료
2,컬럼 환각 (Hallucination),LLM이 없는 productID 컬럼을 자꾸 사용,nodes.py에 실제 스키마(product) 명시 및 프롬프트 강화,✅ 완료
3,SQL 문법 에러,LLM이 SQL을 마크다운(```)으로 감싸서 반환,파이썬 코드로 포장지(```sql) 강제 제거 로직 추가,✅ 완료
4,데이터 증발 (0 rows),"CSV 데이터의 ID 불일치로 인해, 적재 시 FK 제약조건 위반 데이터를 자동 삭제함",load_data.py에서 삭제(DELETE) 로직 비활성화,✅ 완료

이 요청은 **"Intent Classification(의도 분류)"** 작업에 해당합니다. LLM이 사용자의 입력이 데이터베이스 조회를 위한 것인지, 아니면 일반적인 대화인지를 판단하여 라우팅(Routing)할 수 있도록 돕는 프롬프트입니다.

사용 목적과 환경에 따라 선택할 수 있도록 세 가지 버전을 준비했습니다.

---

### Option 1: JSON 형식 (API 연동에 최적화)

이 프롬프트는 시스템이 결과를 파싱하기 쉽게 **JSON** 포맷으로 결과를 출력합니다. 또한 `confidence`(확신도)와 `reasoning`(판단 이유)을 포함하여 디버깅을 용이하게 합니다.

```markdown
### System Prompt

You are an expert intent classifier. Your job is to analyze the user's input and determine if the request requires executing a SQL query to retrieve specific data from a database or if it is a general conversation.

**Classification Criteria:**
1. **SQL_REQUEST**:
   - The user asks to retrieve, filter, aggregate, or list data (e.g., "Show me top sales," "List users in Seoul").
   - The user asks for statistics, counts, or specific records.
   - The input implies querying a structured dataset.

2. **GENERAL_CONVERSATION**:
   - The user greets, asks for definitions, or engages in small talk (e.g., "Hello," "What is SQL?").
   - The user asks questions that do not pertain to retrieving data from a database.
   - Commands unrelated to data retrieval (e.g., "Translate this").

**Output Format:**
You must respond with a JSON object containing the following keys:
- "intent": Either "SQL_REQUEST" or "GENERAL_CONVERSATION"
- "confidence": A score between 0.0 and 1.0
- "reasoning": A brief explanation of why you classified it this way.

**Example 1:**
Input: "How many users signed up last week?"
Output: {"intent": "SQL_REQUEST", "confidence": 0.99, "reasoning": "User is asking for an aggregation (count) of user records filtered by a specific time range."}

**Example 2:**
Input: "Hi, can you help me?"
Output: {"intent": "GENERAL_CONVERSATION", "confidence": 0.98, "reasoning": "This is a standard greeting and offer for help, not a data retrieval request."}

**Constraint:** Do not output any text other than the JSON object.

```

---

### Option 2: 심플/직관적 버전 (토큰 절약형)

단순히 흐름을 제어(If/Else)하기 위해 딱 **라벨만** 필요한 경우에 적합합니다. 군더더기 없이 결과만 출력합니다.

```markdown
### System Prompt

Analyze the following input and classify it into one of two categories:

[SQL] - If the user wants to fetch, count, analyze, or look up specific data from a database.
[GENERAL] - If the input is a greeting, a clarifying question, a coding request, or casual chat.

**Rules:**
- Even if the user does not use the word "SQL", if the intent requires data retrieval (e.g., "Who bought the most items?"), classify as [SQL].
- If the request is ambiguous but leans towards asking for information likely stored in a table, classify as [SQL].

**Output:**
Return ONLY the class label `[SQL]` or `[GENERAL]`. Do not provide explanations.

```

---

### Option 3: Few-Shot Prompting (높은 정확도)

모델이 헷갈려할 수 있는 애매한 상황을 예시(Few-shot)로 학습시켜 정확도를 높인 버전입니다.

```markdown
### System Prompt

You are a routing agent. Determine whether the user's message is a request for a database query (SQL_Generating) or a non-database related chat (General_Chat).

Here are examples of how to classify:

User: "Hello, who are you?"
Class: General_Chat

User: "List all employees who joined in 2023."
Class: SQL_Generating

User: "What does the 'status' column mean?"
Class: General_Chat (Note: Asking for metadata explanation, not data retrieval)

User: "Show me the average revenue by region."
Class: SQL_Generating

User: "Can you write a python script to calculate pi?"
Class: General_Chat

User: "I need to find the customer with ID 1234."
Class: SQL_Generating

**Task:**
Classify the following user input.
Output ONLY the class name.

User: {{User_Input_Here}}
Class:

```

---

### 💡 Tip: 프롬프트 적용 시 고려사항

1. **스키마 정보 (선택 사항):**
만약 에이전트가 특정 데이터베이스(예: 쇼핑몰 DB)에 특화되어 있다면, System Prompt의 시작 부분에 *"You are an assistant with access to a database containing [Orders, Users, Products] tables."*라고 명시해주면 `SQL_REQUEST` 판단 능력이 더 좋아집니다.
2. **모호한 질문:**
"배송 상태가 뭐야?" 같은 질문은 DB 조회일 수도 있고, 용어 설명일 수도 있습니다. 이런 경우를 대비해 **Option 1**을 사용하여 `reasoning`을 확인하거나, 프롬프트 규칙(Rules)에 "모호하면 General로 분류하라"는 지침을 추가하는 것이 안전합니다.

**어떤 환경(예: LangChain, 단순 API 호출 등)에서 사용하실 예정인가요?** 환경에 맞춰 더 구체적인 파이썬 코드 예시나 연동 방법을 제안해 드릴 수 있습니다.


2. **CRITICAL**: The product column is named 'product', NOT 'productID'.

<-- ⭐ IMPORTANT: Use this for product names. There is NO 'productID'.


SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'sales_transactions';