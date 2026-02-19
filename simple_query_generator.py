import os
from typing import Optional
from openai import OpenAI

class SimpleSQLQueryGenerator:
    def __init__(self, provider: str = "ollama", model: str = None):
        """
        Initialize the query generator.
        
        Args:
            provider: "ollama"
            model: Model name (optional, uses defaults)
        """
        self.provider = provider
        
        if provider == "ollama":
            self.client = OpenAI(api_key=os.getenv("OLLAMA_API_KEY"), base_url=os.getenv("OLLAMA_BASE_URL"))
            self.model = model or "llama3.2"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    
    def create_system_prompt(self, schema: str, dialect: str = "postgresql") -> str:
        """Create a detailed system prompt for the LLM."""
        return f"""You are an expert T-SQL (Microsoft SQL Server) query generator. Your task is to convert natural language questions into accurate, high-performance MSSQL queries.

            Database Schema:
            {schema}

            SQL Dialect: {dialect} (T-SQL / SQL Server)

            Rules:
            1. Generate ONLY the SQL query. No explanations, no markdown code blocks, and no backticks.
            2. Use proper JOIN syntax (INNER, LEFT) and always use table aliases (e.g., `customers AS c`).
            3. Use TOP for limiting results instead of LIMIT (e.g., `SELECT TOP 10 ...`).
            4. For date filtering/extraction, use T-SQL functions like `GETDATE()`, `DATEPART()`, `DATEDIFF()`, and `FORMAT()`.
            5. Use `COALESCE` to handle NULL values in calculations or concatenations.
            6. When comparing strings, use the `LIKE` operator with `%` wildcards if partial matches are implied.
            7. Use `ISNULL()` or `COALESCE()` for NULL-safe aggregations.
            8. Follow T-SQL best practices: Use `QUOTED_IDENTIFIER` logic (square brackets `[ ]`) if table or column names contain spaces or are reserved keywords.
            9. For pagination/offset, use `OFFSET 0 ROWS FETCH NEXT N ROWS ONLY` if `TOP` is not suitable.
            10. Ensure all column names and table names match the provided schema exactly.

            Important:
            - MS SQL Server is the target; do NOT use `LIMIT`, `ILIKE`, or `TO_TIMESTAMP`.
            - If the question is ambiguous, assume the most common business logic.
            - If the schema lacks necessary information, provide a brief comment starting with `--` explain why.
            - For temporal queries (e.g., "this year"), use `YEAR(order_date) = YEAR(GETDATE())`.
            - Always group by all non-aggregated columns when using `GROUP BY`.
            """
    
    def generate_query(
        self, 
        question: str, 
        schema: str, 
        dialect: str = "mssql"
    ) -> str:
        """
        Generate SQL query from natural language.
        
        Args:
            question: Natural language question
            schema: Database schema
            dialect: SQL dialect (postgresql, mysql, sqlserver)
        
        Returns:
            Generated SQL query
        """
        system_prompt = self.create_system_prompt(schema, dialect)
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": question}
                ]
            )
            query = response.content[0].text.strip()
        
        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.1  # Lower temperature for more consistent output
            )
            query = response.choices[0].message.content.strip()
        elif self.provider == "ollama":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.1
            )
            query = response.choices[0].message.content.strip()

        # Clean up the query (remove markdown if present)
        query = self._clean_query(query)
        return query

    def _clean_query(self, query: str) -> str:
        """Remove markdown formatting and extra whitespace."""
        # Remove SQL markdown blocks
        if query.startswith("```sql"):
            query = query[6:]
        if query.startswith("```"):
            query = query[3:]
        if query.endswith("```"):
            query = query[:-3]
        
        return query.strip()