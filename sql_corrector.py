# sql_corrector.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)


def build_correction_prompt(original_sql: str, error_message: str, schema_md: str) -> str:
    return f"""You are an expert MS SQL Server engineer.

            A SQL query was generated from a user's question but failed when executed.
            Your task is to fix the SQL so it runs correctly.

            ## Database Schema
            {schema_md}

            ## Original SQL (failed)
            ```sql
            {original_sql}
            ```

            ## Error Message from SQL Server
            {error_message}

            ## Instructions
            - Fix ONLY the part of the query causing the error.
            - Do NOT change the intent of the query.
            - Do NOT use any tables or columns not in the schema above.
            - Return ONLY the corrected SQL query. No explanation, no markdown fences, no preamble.
            """


def correct_sql(
    original_sql: str,
    error_message: str,
    schema_md: str,
    attempt: int
) -> str:
    """
    Asks the LLM to fix a failed SQL query given its error message.
    Returns the corrected SQL string.
    """
    client = OpenAI(
        api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    )

    prompt = build_correction_prompt(original_sql, error_message, schema_md)

    print(f"\n[CORRECTION ATTEMPT {attempt}] Sending error feedback to LLM...")

    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0  # Zero temperature for deterministic fixes
    )

    corrected = response.choices[0].message.content.strip()

    # Strip markdown fences if the LLM adds them despite instructions
    if corrected.startswith("```"):
        lines = corrected.split("\n")
        corrected = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    return corrected