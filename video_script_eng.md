Hello, I'm Chanwoo Bae, and my preferred name is Ted. I applied for the insightfactory.ai Cadet challenge.
Today, I'll show you my AI-based database LLM agent, from database setup to query execution.

My product has two main parts: database setup and the agent chat UI.

For database setup, I designed it around user interaction rather than full LLM automation. Let me walk you through the setup process and explain my design choices.

When you run ./start.sh, it either starts the UI directly or begins database setup, depending on whether a schema file exists.

Since I need to show you everything from scratch, let's start with database setup.

When setup begins, you'll see six steps on the screen:

  1. Profiler - Analyze CSV files
  2. Relationship Discovery - Configure PK/FK (interactive)
  3. Load Data - Load to PostgreSQL (may fail initially)
  4. Integrity Checker - Validate data integrity
  5. Transform Data - Fix issues (interactive)
  6. Generate Schema - Create schema with PII detection

Let's start with step one. The first step profiles all the data.

[Shows data_profile.json]

It scans basic information for each dataset and column characteristics that we'll use in later steps. This step automatically creates data_profile.json from the CSV files.

Starting from Relationship Discovery, users interact with the system to configure settings.

Actually, I first tried to make the LLM set up keys automatically.

But that came with risks if I wanted to keep it data-agnostic. There are just too many variables, starting with column naming. Plus, CSV data doesn't always guarantee 100% integrity. If the LLM makes wrong decisions or if I write my own key detection logic, even one bad connection could break the entire database build.

So I designed it with the assumption that users are data managers. They configure keys by following the CLI interface prompts.

[Starts primary key setup]

First, we set primary keys for each table.
Even though it's interactive, I built a recommendation system to help users. It suggests the most likely columns. Users can look at the data samples on screen and decide which one should be the primary key.

[Starts foreign key setup]

Same for foreign keys and external references for each table. First you pick which foreign key to set, then you choose which table it references. The recommendation system suggests likely candidates.

This approach minimizes data integrity risks compared to depending on LLM agents or automated logic.

Once key setup is done, the system automatically loads data into PostgreSQL.

[Shows CLI output after data loading]

But if you look at the screen, CSV data integrity issues mean the data doesn't load perfectly with the keys you just set. The system automatically runs an integrity check and reports what's wrong.

This is where users interact with the system again. I thought a lot about this part, but I decided that for data integrity, users need to handle it directly.
So you type SQL commands directly in the CLI to fix database integrity issues. For example, you DELETE records that violate foreign key constraints, or UPDATE values to maintain referential integrity.

[Shows SQL input]

After that, it automatically checks integrity again and moves on to PII detection.

[Shows red markings]

Here, the LLM steps in to detect columns that might contain personal information and marks them in red. Users review this report and confirm which personal information is marked.

But if the detection is wrong, the system tells you to edit the schema JSON file directly. I figured this was the simplest way to handle it.

[Shows src/config/schema_info.json file]

Once schema generation is complete, the server starts automatically and the UI launches.

By the way, this project uses Cerebras's llama-3.3-70b model with temperature settings tuned for each task. For example, intent classification uses 0.0 for deterministic results, SQL generation uses 0.1 for accuracy, and natural language responses use 0.7 for more natural output.

Alright, let's start with some simple questions.

[Runs three questions]

The agent generates natural language responses for each query result and shows them to users. For each question, the agent also creates interesting insights about the query results.

Now let's try more complex questions.

[Runs three questions]

The masking we set during data setup hides personal names with numbering like Person #1, Person #2.

Now let's try requesting Plotly charts. The system supports five chart types: bar, line, pie, scatter, and area. The agent analyzes the question content and automatically picks the most appropriate chart type. Until now, it decided no visualization was needed, so it only generated text responses.

[Runs three questions]

As you can see, this time it generates a chart along with the text response when you request one. Now let's try more complex questions using PARTITION and other advanced features.

[Runs three questions]

You can see it generates responses smoothly. Now let's try even more advanced questions that generate Pyodide code for data analysis. The agent also decides whether to generate Pyodide based on the user's question.

[Runs time series question]

This time I asked a simple time series question and it generated Pyodide code. Since Pyodide code generates its own output, the natural language response just gives a brief metadata summary.
I want to add that Pyodide serves two purposes. First, it's a Python code execution environment for complex data analysis that's hard to do in SQL, like time series or statistical analysis. Second, if SQL queries fail three times in a row, it automatically switches to Pyodide mode. This fallback mechanism makes answer generation more stable. It really improved the success rate for complex questions.

Now let me briefly explain why I chose these technologies, the system's limitations, and ideas for improvement.

First, why I chose these technologies.

I chose Cerebras's llama-3.3-70b model because it's fast and reasonably priced. Cost per token is cheaper than OpenAI or Anthropic, and it performs well enough for SQL generation and natural language responses.

I chose PostgreSQL because relational data integrity was important. It handles complex queries and JSON support better than MySQL, and has better concurrency than SQLite, making it better for production.

I chose Plotly because it provides interactive charts and various chart types out of the box. It offers more chart options than Chart.js, and it's simpler to implement than D3.js while still producing professional visualizations.

Finally, I chose Pyodide because it runs Python directly in the browser. It's more secure than running on the server side, and users can see and trust the generated code.

Now for the system's current limitations.

The biggest limitation is that it treats each question independently. For example, if you ask "show me the top 5 products" and then follow up with "how about the bottom 5?", it won't understand the previous context. The current architecture only reads the last message for each question, so conversation context isn't maintained.

Finally, future improvements.

In the future, I plan to add multi-turn conversation functionality that includes conversation history along with the schema in the prompt. This will make natural follow-up questions possible, like "show me that result as a chart" or "show me other columns with the same conditions."

Alright, that's it for the basic demo video. The demo focused on showing you how it works. I've documented the detailed architecture and workflow in the docs folder. Thanks for watching.