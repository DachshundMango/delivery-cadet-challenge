# Easy Questions:
What are the top 3 most popular products by total quantity sold?
How many customers are there in each continent?
What payment methods are used and how often is each one used?

# Medium Questions:
Which country generates the highest total revenue? Show all countries ranked by revenue?
Who are the top 5 customers by total spending? Show their names and total amount spent?
Which franchises have received the most customer reviews? List the top 5 franchise names with their review counts?

# Hard Questions (Multi-Table Joins + Visualizations)
Create a bar chart showing total revenue by supplier ingredient. Which ingredients are associated with the highest-selling franchises?
Visualize daily sales trends over time. Create a line chart showing total revenue per day and identify any patterns.
Create a visualization comparing revenue by franchise size (S, M, L, XL, XXL). Also show the average transaction value for each size category.

# Expert Questions (Window Functions with PARTITION BY)
For each country, rank the products by total revenue and show only the top-selling product in each country. Use a window function with PARTITION BY.
Calculate the running cumulative revenue per day, and create a visualization showing both daily revenue and the cumulative total over time.
For each transaction, calculate how its total price compares to the average transaction value for that franchise (as a percentage). Show the top 10 transactions that most exceeded their franchise average.