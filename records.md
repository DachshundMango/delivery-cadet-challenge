# 컬럼 큰따옴표 때문에 힘들었다.

Ask questions (enter q if you want to exit): Which country generates the highest total revenue? Show all countries ranked by revenue?

Processing...

Generated SQL:
------------------------------------------------------------
SELECT 
    s.country,
    SUM(st.totalPrice) AS total_revenue
FROM 
    sales_transactions st
JOIN 
    sales_franchises sf ON st.franchiseID = sf.franchiseID
JOIN 
    sales_suppliers ss ON sf.supplierID = ss.supplierID
JOIN 
    sales_customers sc ON st.customerID = sc.customerID
GROUP BY 
    s.country
ORDER BY 
    total_revenue DESC
------------------------------------------------------------
WARNING [cadet.nodes] Database error: (psycopg2.errors.UndefinedColumn) column st.franchiseid does not exist
LINE 7:     sales_franchises sf ON st.franchiseID = sf.franchiseID
                                   ^
HINT:  Perhaps you meant to reference the column "st.franchiseID".

[SQL: SELECT 
    s.country,
    SUM(st.totalPrice) AS total_revenue
FROM 
    sales_transactions st
JOIN 
    sales_franchises sf ON st.franchiseID = sf.franchiseID
JOIN 
    sales_suppliers ss ON sf.supplierID = ss.supplierID
JOIN 
    sales_customers sc ON st.customerID = sc.customerID
GROUP BY 
    s.country
ORDER BY 
    total_revenue DESC]
(Background on this error at: https://sqlalche.me/e/20/f405)
WARNING [cadet.graph] SQL error detected, retry 1/3
Query error: Error: (psycopg2.errors.UndefinedColumn) column st.franchiseid does not exist
LINE 7:     sales_franchises sf ON st.franchiseID = sf.franchiseID
                                   ^
HINT:  Perhaps you meant to reference the column "st.franchiseID".

[SQL: SELECT 
    s.country,
    SUM(st.totalPrice) AS total_revenue
FROM 
    sales_transactions st
JOIN 
    sales_franchises sf ON st.franchiseID = sf.franchiseID
JOIN 
    sales_suppliers ss ON sf.supplierID = ss.supplierID
JOIN 
    sales_customers sc ON st.customerID = sc.customerID
GROUP BY 
    s.country
ORDER BY 
    total_revenue DESC]
(Background on this error at: https://sqlalche.me/e/20/f405)

Generated SQL:
------------------------------------------------------------
SELECT 
    s.country, 
    SUM(st.totalPrice) AS total_revenue
FROM 
    sales_transactions st
JOIN 
    sales_franchises sf ON st.franchiseID = sf.franchiseID
JOIN 
    sales_suppliers ss ON sf.supplierID = ss.supplierID
JOIN 
    sales_customers sc ON st.customerID = sc.customerID
GROUP BY 
    s.country
ORDER BY 
    total_revenue DESC;
------------------------------------------------------------
WARNING [cadet.nodes] Database error: (psycopg2.errors.UndefinedColumn) column st.franchiseid does not exist
LINE 7:     sales_franchises sf ON st.franchiseID = sf.franchiseID
                                   ^
HINT:  Perhaps you meant to reference the column "st.franchiseID".

[SQL: SELECT 
    s.country, 
    SUM(st.totalPrice) AS total_revenue
FROM 
    sales_transactions st
JOIN 
    sales_franchises sf ON st.franchiseID = sf.franchiseID
JOIN 
    sales_suppliers ss ON sf.supplierID = ss.supplierID
JOIN 
    sales_customers sc ON st.customerID = sc.customerID
GROUP BY 
    s.country
ORDER BY 
    total_revenue DESC;]
(Background on this error at: https://sqlalche.me/e/20/f405)
WARNING [cadet.graph] SQL error detected, retry 1/3
Query error: Error: (psycopg2.errors.UndefinedColumn) column st.franchiseid does not exist
LINE 7:     sales_franchises sf ON st.franchiseID = sf.franchiseID
                                   ^
HINT:  Perhaps you meant to reference the column "st.franchiseID".

[SQL: SELECT 
    s.country, 
    SUM(st.totalPrice) AS total_revenue
FROM 
    sales_transactions st
JOIN 
    sales_franchises sf ON st.franchiseID = sf.franchiseID
JOIN 
    sales_suppliers ss ON sf.supplierID = ss.supplierID
JOIN 
    sales_customers sc ON st.customerID = sc.customerID
GROUP BY 
    s.country
ORDER BY 
    total_revenue DESC;]
(Background on this error at: https://sqlalche.me/e/20/f405)

Generated SQL:
------------------------------------------------------------
SELECT 
    COALESCE(s.country, 'Unknown') AS country,
    COALESCE(SUM(st.totalPrice), 0) AS revenue
FROM 
    sales_transactions st
    JOIN sales_suppliers s ON st.franchiseID = s.supplierID
GROUP BY 
    COALESCE(s.country, 'Unknown')
ORDER BY 
    revenue DESC
------------------------------------------------------------
WARNING [cadet.nodes] Database error: (psycopg2.errors.UndefinedColumn) column st.franchiseid does not exist
LINE 6:     JOIN sales_suppliers s ON st.franchiseID = s.supplierID
                                      ^
HINT:  Perhaps you meant to reference the column "st.franchiseID".

[SQL: SELECT 
    COALESCE(s.country, 'Unknown') AS country,
    COALESCE(SUM(st.totalPrice), 0) AS revenue
FROM 
    sales_transactions st
    JOIN sales_suppliers s ON st.franchiseID = s.supplierID
GROUP BY 
    COALESCE(s.country, 'Unknown')
ORDER BY 
    revenue DESC]
(Background on this error at: https://sqlalche.me/e/20/f405)
WARNING [cadet.graph] SQL error detected, retry 1/3
Query error: Error: (psycopg2.errors.UndefinedColumn) column st.franchiseid does not exist
LINE 6:     JOIN sales_suppliers s ON st.franchiseID = s.supplierID
                                      ^
HINT:  Perhaps you meant to reference the column "st.franchiseID".

[SQL: SELECT 
    COALESCE(s.country, 'Unknown') AS country,
    COALESCE(SUM(st.totalPrice), 0) AS revenue
FROM 
    sales_transactions st
    JOIN sales_suppliers s ON st.franchiseID = s.supplierID
GROUP BY 
    COALESCE(s.country, 'Unknown')
ORDER BY 
    revenue DESC]
(Background on this error at: https://sqlalche.me/e/20/f405)

Generated SQL:
------------------------------------------------------------
SELECT DISTINCT T1.country, SUM(T2.totalPrice) AS total_revenue
FROM sales_suppliers AS T1
JOIN sales_franchises AS T2 ON T1.supplierID = T2.supplierID
JOIN sales_transactions AS T3 ON T2.franchiseID = T3.franchiseID
GROUP BY T1.country
ORDER BY total_revenue DESC;
------------------------------------------------------------
WARNING [cadet.nodes] Database error: (psycopg2.errors.UndefinedColumn) column t1.supplierid does not exist
LINE 3: JOIN sales_franchises AS T2 ON T1.supplierID = T2.supplierID
                                       ^
HINT:  Perhaps you meant to reference the column "t1.supplierID".

[SQL: SELECT DISTINCT T1.country, SUM(T2.totalPrice) AS total_revenue
FROM sales_suppliers AS T1
JOIN sales_franchises AS T2 ON T1.supplierID = T2.supplierID
JOIN sales_transactions AS T3 ON T2.franchiseID = T3.franchiseID
GROUP BY T1.country
ORDER BY total_revenue DESC;]
(Background on this error at: https://sqlalche.me/e/20/f405)
WARNING [cadet.graph] SQL error detected, retry 1/3
Query error: Error: (psycopg2.errors.UndefinedColumn) column t1.supplierid does not exist
LINE 3: JOIN sales_franchises AS T2 ON T1.supplierID = T2.supplierID
                                       ^
HINT:  Perhaps you meant to reference the column "t1.supplierID".

[SQL: SELECT DISTINCT T1.country, SUM(T2.totalPrice) AS total_revenue
FROM sales_suppliers AS T1
JOIN sales_franchises AS T2 ON T1.supplierID = T2.supplierID
JOIN sales_transactions AS T3 ON T2.franchiseID = T3.franchiseID
GROUP BY T1.country
ORDER BY total_revenue DESC;]
(Background on this error at: https://sqlalche.me/e/20/f405)

Generated SQL:
------------------------------------------------------------
SELECT 
    s.country, 
    SUM(st.totalPrice) AS total_revenue
FROM 
    sales_transactions st
JOIN 
    sales_franchises sf ON st.franchiseID = sf.franchiseID
JOIN 
    sales_suppliers ss ON sf.supplierID = ss.supplierID
JOIN 
    sales_customers sc ON st.customerID = sc.customerID
GROUP BY 
    s.country
ORDER BY 
    total_revenue DESC
------------------------------------------------------------
WARNING [cadet.nodes] Database error: (psycopg2.errors.UndefinedColumn) column st.franchiseid does not exist
LINE 7:     sales_franchises sf ON st.franchiseID = sf.franchiseID
                                   ^
HINT:  Perhaps you meant to reference the column "st.franchiseID".

[SQL: SELECT 
    s.country, 
    SUM(st.totalPrice) AS total_revenue
FROM 
    sales_transactions st
JOIN 
    sales_franchises sf ON st.franchiseID = sf.franchiseID
JOIN 
    sales_suppliers ss ON sf.supplierID = ss.supplierID
JOIN 
    sales_customers sc ON st.customerID = sc.customerID
GROUP BY 
    s.country
ORDER BY 
    total_revenue DESC]
(Background on this error at: https://sqlalche.me/e/20/f405)
WARNING [cadet.graph] SQL error detected, retry 1/3
Query error: Error: (psycopg2.errors.UndefinedColumn) column st.franchiseid does not exist
LINE 7:     sales_franchises sf ON st.franchiseID = sf.franchiseID
                                   ^
HINT:  Perhaps you meant to reference the column "st.franchiseID".

[SQL: SELECT 
    s.country, 
    SUM(st.totalPrice) AS total_revenue
FROM 
    sales_transactions st
JOIN 
    sales_franchises sf ON st.franchiseID = sf.franchiseID
JOIN 
    sales_suppliers ss ON sf.supplierID = ss.supplierID
JOIN 
    sales_customers sc ON st.customerID = sc.customerID
GROUP BY 
    s.country
ORDER BY 
    total_revenue DESC]
(Background on this error at: https://sqlalche.me/e/20/f405)

Generated SQL:
------------------------------------------------------------
SELECT 
  s.country, 
  SUM(st.totalPrice) AS total_revenue
FROM 
  sales_transactions st
JOIN 
  sales_customers sc ON st.customerID = sc.customerID
JOIN 
  sales_franchises sf ON st.franchiseID = sf.franchiseID
JOIN 
  sales_suppliers ss ON sf.supplierID = ss.supplierID
GROUP BY 
  s.country
ORDER BY 
  total_revenue DESC;
------------------------------------------------------------
WARNING [cadet.nodes] Database error: (psycopg2.errors.UndefinedColumn) column st.customerid does not exist
LINE 7:   sales_customers sc ON st.customerID = sc.customerID
                                ^
HINT:  Perhaps you meant to reference the column "st.customerID".

[SQL: SELECT 
  s.country, 
  SUM(st.totalPrice) AS total_revenue
FROM 
  sales_transactions st
JOIN 
  sales_customers sc ON st.customerID = sc.customerID
JOIN 
  sales_franchises sf ON st.franchiseID = sf.franchiseID
JOIN 
  sales_suppliers ss ON sf.supplierID = ss.supplierID
GROUP BY 
  s.country
ORDER BY 
  total_revenue DESC;]
(Background on this error at: https://sqlalche.me/e/20/f405)
WARNING [cadet.graph] SQL error detected, retry 1/3
Query error: Error: (psycopg2.errors.UndefinedColumn) column st.customerid does not exist
LINE 7:   sales_customers sc ON st.customerID = sc.customerID
                                ^
HINT:  Perhaps you meant to reference the column "st.customerID".

[SQL: SELECT 
  s.country, 
  SUM(st.totalPrice) AS total_revenue
FROM 
  sales_transactions st
JOIN 
  sales_customers sc ON st.customerID = sc.customerID
JOIN 
  sales_franchises sf ON st.franchiseID = sf.franchiseID
JOIN 
  sales_suppliers ss ON sf.supplierID = ss.supplierID
GROUP BY 
  s.country
ORDER BY 
  total_revenue DESC;]
(Background on this error at: https://sqlalche.me/e/20/f405)

Generated SQL:
------------------------------------------------------------
SELECT 
    T2.country, 
    SUM(T1.totalPrice) AS total_revenue
FROM 
    sales_transactions AS T1
JOIN 
    sales_customers AS T2 ON T1.customerID = T2.customerID
JOIN 
    sales_franchises AS T3 ON T1.franchiseID = T3.franchiseID
GROUP BY 
    T2.country
ORDER BY 
    total_revenue DESC
------------------------------------------------------------
WARNING [cadet.nodes] Database error: (psycopg2.errors.UndefinedColumn) column t1.customerid does not exist
LINE 7:     sales_customers AS T2 ON T1.customerID = T2.customerID
                                     ^
HINT:  Perhaps you meant to reference the column "t1.customerID".

[SQL: SELECT 
    T2.country, 
    SUM(T1.totalPrice) AS total_revenue
FROM 
    sales_transactions AS T1
JOIN 
    sales_customers AS T2 ON T1.customerID = T2.customerID
JOIN 
    sales_franchises AS T3 ON T1.franchiseID = T3.franchiseID
GROUP BY 
    T2.country
ORDER BY 
    total_revenue DESC]
(Background on this error at: https://sqlalche.me/e/20/f405)
WARNING [cadet.graph] SQL error detected, retry 1/3
Query error: Error: (psycopg2.errors.UndefinedColumn) column t1.customerid does not exist
LINE 7:     sales_customers AS T2 ON T1.customerID = T2.customerID
                                     ^
HINT:  Perhaps you meant to reference the column "t1.customerID".

[SQL: SELECT 
    T2.country, 
    SUM(T1.totalPrice) AS total_revenue
FROM 
    sales_transactions AS T1
JOIN 
    sales_customers AS T2 ON T1.customerID = T2.customerID
JOIN 
    sales_franchises AS T3 ON T1.franchiseID = T3.franchiseID
GROUP BY 
    T2.country
ORDER BY 
    total_revenue DESC]
(Background on this error at: https://sqlalche.me/e/20/f405)

Generated SQL:
------------------------------------------------------------
SELECT 
    s.country, 
    SUM(st.totalPrice) AS total_revenue
FROM 
    sales_franchises sf
JOIN 
    sales_transactions st ON sf.franchiseID = st.franchiseID
JOIN 
    sales_customers sc ON st.customerID = sc.customerID
JOIN 
    sales_suppliers ss ON sf.supplierID = ss.supplierID
GROUP BY 
    s.country
ORDER BY 
    total_revenue DESC;
------------------------------------------------------------
WARNING [cadet.nodes] Database error: (psycopg2.errors.UndefinedColumn) column sf.franchiseid does not exist
LINE 7:     sales_transactions st ON sf.franchiseID = st.franchiseID
                                     ^
HINT:  Perhaps you meant to reference the column "sf.franchiseID".

[SQL: SELECT 
    s.country, 
    SUM(st.totalPrice) AS total_revenue
FROM 
    sales_franchises sf
JOIN 
    sales_transactions st ON sf.franchiseID = st.franchiseID
JOIN 
    sales_customers sc ON st.customerID = sc.customerID
JOIN 
    sales_suppliers ss ON sf.supplierID = ss.supplierID
GROUP BY 
    s.country
ORDER BY 
    total_revenue DESC;]
(Background on this error at: https://sqlalche.me/e/20/f405)
WARNING [cadet.graph] SQL error detected, retry 1/3
Query error: Error: (psycopg2.errors.UndefinedColumn) column sf.franchiseid does not exist
LINE 7:     sales_transactions st ON sf.franchiseID = st.franchiseID
                                     ^
HINT:  Perhaps you meant to reference the column "sf.franchiseID".

[SQL: SELECT 
    s.country, 
    SUM(st.totalPrice) AS total_revenue
FROM 
    sales_franchises sf
JOIN 
    sales_transactions st ON sf.franchiseID = st.franchiseID
JOIN 
    sales_customers sc ON st.customerID = sc.customerID
JOIN 
    sales_suppliers ss ON sf.supplierID = ss.supplierID
GROUP BY 
    s.country
ORDER BY 
    total_revenue DESC;]
(Background on this error at: https://sqlalche.me/e/20/f405)

Generated SQL:
------------------------------------------------------------
SELECT 
  T1.country, 
  SUM(T2.totalPrice) AS revenue
FROM 
  sales_suppliers T1
JOIN 
  sales_franchises T2 ON T1.supplierID = T2.supplierID
JOIN 
  sales_transactions T3 ON T2.franchiseID = T3.franchiseID
GROUP BY 
  T1.country
ORDER BY 
  revenue DESC;
------------------------------------------------------------
WARNING [cadet.nodes] Database error: (psycopg2.errors.UndefinedColumn) column t1.supplierid does not exist
LINE 7:   sales_franchises T2 ON T1.supplierID = T2.supplierID
                                 ^
HINT:  Perhaps you meant to reference the column "t1.supplierID".

[SQL: SELECT 
  T1.country, 
  SUM(T2.totalPrice) AS revenue
FROM 
  sales_suppliers T1
JOIN 
  sales_franchises T2 ON T1.supplierID = T2.supplierID
JOIN 
  sales_transactions T3 ON T2.franchiseID = T3.franchiseID
GROUP BY 
  T1.country
ORDER BY 
  revenue DESC;]
(Background on this error at: https://sqlalche.me/e/20/f405)
WARNING [cadet.graph] SQL error detected, retry 1/3
Query error: Error: (psycopg2.errors.UndefinedColumn) column t1.supplierid does not exist
LINE 7:   sales_franchises T2 ON T1.supplierID = T2.supplierID
                                 ^
HINT:  Perhaps you meant to reference the column "t1.supplierID".

[SQL: SELECT 
  T1.country, 
  SUM(T2.totalPrice) AS revenue
FROM 
  sales_suppliers T1
JOIN 
  sales_franchises T2 ON T1.supplierID = T2.supplierID
JOIN 
  sales_transactions T3 ON T2.franchiseID = T3.franchiseID
GROUP BY 
  T1.country
ORDER BY 
  revenue DESC;]
(Background on this error at: https://sqlalche.me/e/20/f405)

Generated SQL:
------------------------------------------------------------
SELECT 
  t2.country, 
  SUM(t1.totalPrice) AS revenue
FROM 
  sales_transactions t1
JOIN 
  sales_customers t2 ON t1.customerID = t2.customerID
GROUP BY 
  t2.country
ORDER BY 
  revenue DESC
------------------------------------------------------------
WARNING [cadet.nodes] Database error: (psycopg2.errors.UndefinedColumn) column t1.customerid does not exist
LINE 7:   sales_customers t2 ON t1.customerID = t2.customerID
                                ^
HINT:  Perhaps you meant to reference the column "t1.customerID".

[SQL: SELECT 
  t2.country, 
  SUM(t1.totalPrice) AS revenue
FROM 
  sales_transactions t1
JOIN 
  sales_customers t2 ON t1.customerID = t2.customerID
GROUP BY 
  t2.country
ORDER BY 
  revenue DESC]
(Background on this error at: https://sqlalche.me/e/20/f405)
WARNING [cadet.graph] SQL error detected, retry 1/3
Query error: Error: (psycopg2.errors.UndefinedColumn) column t1.customerid does not exist
LINE 7:   sales_customers t2 ON t1.customerID = t2.customerID
                                ^
HINT:  Perhaps you meant to reference the column "t1.customerID".

[SQL: SELECT 
  t2.country, 
  SUM(t1.totalPrice) AS revenue
FROM 
  sales_transactions t1
JOIN 
  sales_customers t2 ON t1.customerID = t2.customerID
GROUP BY 
  t2.country
ORDER BY 
  revenue DESC]
(Background on this error at: https://sqlalche.me/e/20/f405)

Generated SQL:
------------------------------------------------------------
SELECT 
  t1.country, 
  SUM(t4.totalPrice) AS total_revenue
FROM 
  sales_suppliers t1
  JOIN sales_franchises t2 ON t1.supplierID = t2.supplierID
  JOIN sales_transactions t3 ON t2.franchiseID = t3.franchiseID
  JOIN sales_customers t4 ON t3.customerID = t4.customerID
GROUP BY 
  t1.country
ORDER BY 
  total_revenue DESC
------------------------------------------------------------
WARNING [cadet.nodes] Database error: (psycopg2.errors.UndefinedColumn) column t1.supplierid does not exist
LINE 6:   JOIN sales_franchises t2 ON t1.supplierID = t2.supplierID
                                      ^
HINT:  Perhaps you meant to reference the column "t1.supplierID".

[SQL: SELECT 
  t1.country, 
  SUM(t4.totalPrice) AS total_revenue
FROM 
  sales_suppliers t1
  JOIN sales_franchises t2 ON t1.supplierID = t2.supplierID
  JOIN sales_transactions t3 ON t2.franchiseID = t3.franchiseID
  JOIN sales_customers t4 ON t3.customerID = t4.customerID
GROUP BY 
  t1.country
ORDER BY 
  total_revenue DESC]
(Background on this error at: https://sqlalche.me/e/20/f405)
WARNING [cadet.graph] SQL error detected, retry 1/3
Query error: Error: (psycopg2.errors.UndefinedColumn) column t1.supplierid does not exist
LINE 6:   JOIN sales_franchises t2 ON t1.supplierID = t2.supplierID
                                      ^
HINT:  Perhaps you meant to reference the column "t1.supplierID".

[SQL: SELECT 
  t1.country, 
  SUM(t4.totalPrice) AS total_revenue
FROM 
  sales_suppliers t1
  JOIN sales_franchises t2 ON t1.supplierID = t2.supplierID
  JOIN sales_transactions t3 ON t2.franchiseID = t3.franchiseID
  JOIN sales_customers t4 ON t3.customerID = t4.customerID
GROUP BY 
  t1.country
ORDER BY 
  total_revenue DESC]
(Background on this error at: https://sqlalche.me/e/20/f405)

Generated SQL:
------------------------------------------------------------
SELECT 
    s.country, 
    SUM(st.totalPrice) AS total_revenue
FROM 
    sales_transactions st
INNER JOIN 
    sales_customers sc ON st.customerID = sc.customerID
INNER JOIN 
    sales_franchises sf ON st.franchiseID = sf.franchiseID
INNER JOIN 
    sales_suppliers ss ON sf.supplierID = ss.supplierID
GROUP BY 
    s.country
ORDER BY 
    total_revenue DESC;
------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/chanwoobae/Desktop/cadet/src/cli.py", line 26, in <module>
    for output in app.stream(inputs):
                  ^^^^^^^^^^^^^^^^^^
  File "/Users/chanwoobae/miniforge3/envs/cadet/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2671, in stream
    raise GraphRecursionError(msg)
langgraph.errors.GraphRecursionError: Recursion limit of 25 reached without hitting a stop condition. You can increase the limit by setting the `recursion_limit` config key.
For troubleshooting, visit: https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT


# 프롬프트 스크립트를 따로 빼넀다. 
# 현재 로직이 LLM 기반이다 -> 즉 어떤걸 프롬프트로 하고 어떤걸 내부 백엔드로 로직으로 짯는지 그 구분과 이유를 설명해야함
# 시각화 여부 너무 경직된 키워드 -> 좀더 자연스럽게 해야한다는걸 깨달음