# Easy Questions:

- What are the top 3 most popular products by total quantity sold?
- How many customers are there in each continent?
- What payment methods are used and how often is each one used?

# Medium Questions:

- Which country generates the highest total revenue? Show all countries ranked by revenue?
- Who are the top 5 customers by total spending? Show their names and total amount spent?
- Which franchises have received the most customer reviews? List the top 5 franchise names with their review counts?

# Hard Questions (Multi-Table Joins + Visualizations)

- Create a bar chart showing total revenue by supplier ingredient. Which ingredients are associated with the highest-selling franchises?
- Visualize daily sales trends over time. Create a line chart showing total revenue per day and identify any patterns.
- Create a visualization comparing revenue by franchise size (S, M, L, XL, XXL). Also show the average transaction value for each size category.

# Expert Questions (Window Functions with PARTITION BY)

- For each country, rank the products by total revenue and show only the top-selling product in each country. Use a window function with PARTITION BY.
- Calculate the running cumulative revenue per day, and create a visualization showing both daily revenue and the cumulative total over time.
- For each transaction, calculate how its total price compares to the average transaction value for that franchise (as a percentage). Show the top 10 transactions that most exceeded their franchise average.

---

### 1. 매장 규모별 매출 분포 (Boxplot 스타일 통계)
> **질문:**
> **"Analyze the statistical distribution of TotalPrice for each franchise size. Calculate mean, median, and standard deviation for each group."**

*   **포인트:** 매장 크기(S/M/L)에 따른 매출 성과 차이를 평균뿐만 아니라 '변동성(표준편차)'까지 비교합니다.
*   **예상 결과:** "대형 매장은 매출이 높지만 편차도 크다" 같은 인사이트 발견 가능.

### 2. 결제 수단별 객단가 비교 (통계적 차이)
> **질문:**
> **"Analyze the statistical difference in TotalPrice between different payment methods. Is there a significant variance in spending behavior?"**

*   **포인트:** "현금 낸 사람 vs 카드 낸 사람" 누가 더 비싼 걸 샀는지, 그 차이가 유의미한지 확인합니다.
*   **예상 결과:** 카드 결제 고객의 객단가가 더 높다는 식의 패턴 확인.

### 3. 요일별 판매 패턴 분석 (시계열/트렌드)
> **질문:**
> **"Perform a time series analysis on sales transactions. Analyze the transaction count distribution by day of the week."**

*   **포인트:** 날짜 데이터에서 요일을 추출하여 "무슨 요일에 장사가 제일 잘 되는지" 파악합니다.
*   **예상 결과:** "금요일 저녁이 피크다" 같은 시계열 인사이트.

### 4. 메뉴별 가격 분포와 이상치 탐지 (Anomaly Detection)
> **질문:**
> **"Analyze the price distribution of products sold. Identify any potential outliers in UnitPrice and calculate skewness."**

*   **포인트:** 가격이 비정상적으로 높거나 낮은 메뉴가 있는지(이상치), 가격대가 저가 위주인지 고가 위주인지(왜도) 분석합니다.
*   **예상 결과:** "대부분 5~10달러인데, 특정 메뉴만 100달러다" 같은 이상치 발견.

---

**추천:**
1번과 2번은 이미 시도해 보셨거나 데이터 타입 이슈를 해결한 상태입니다.
**3번 (요일별 분석)**이나 **4번 (이상치 탐지)**를 테스트해 보시면 색다른 분석 결과를 보실 수 있을 겁니다.