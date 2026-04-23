# main_executor.py
import os
from dotenv import load_dotenv
from schema_extractor import SchemaExtractor
from simple_query_generator import SimpleSQLQueryGenerator
from sql_validator import SQLValidator
from sql_executor import execute_query
from result_formatter import format_as_table, format_as_csv

load_dotenv(override=True)


def run_pipeline(user_question: str, db_params: dict, tables: list[str]) -> None:
    print(f"\nUser Question: {user_question}")
    print("-" * 60)

    # Step 1: Extract schema
    extractor = SchemaExtractor(db_params)
    schema_md = extractor.format_schema_for_llm(tables)
    print("\n--- Database Schema ---")
    print(schema_md)

    # Step 2: Generate SQL
    generator = SimpleSQLQueryGenerator()
    generated_sql = generator.generate_query(user_question, schema_md)
    print("\n--- Generated SQL ---")
    print(generated_sql)

    # Step 3: Validate
    validator = SQLValidator()
    is_valid, reason = validator.validate(generated_sql)
    print("\n--- Validation Result ---")

    if not is_valid:
        print(f"Invalid: {reason}")
        print("\n[STOPPED] Query blocked by validator. Not executed.")
        return

    print("Valid: Query passed all safety checks.")

    # Step 4: Execute
    print("\n--- Executing Query ---")
    result = execute_query(generated_sql, db_params)

    # Step 5: Format and display
    print(format_as_table(result))

    # Optional: save to CSV
    if result.success and result.row_count > 0:
        csv_output = format_as_csv(result)
        output_file = "query_results.csv"
        with open(output_file, "w", newline="") as f:
            f.write(csv_output)
        print(f"[INFO] Results also saved to {output_file}")


def main():
    db_params = {
        "SERVER": "(localdb)\\MSSQLLocalDB",
        "DATABASE": "master",
        "Trusted_Connection": "yes",
        "Encrypt": "no"
    }
    my_tables = ["customers", "orders"]

    # --- Test 1: Valid analytical query ---
    run_pipeline(
        user_question="Show me the top 5 customers by total order amount.",
        db_params=db_params,
        tables=my_tables
    )

    # --- Test 2: Query blocked by validator ---
    run_pipeline(
        user_question="Delete all orders placed today.",
        db_params=db_params,
        tables=my_tables
    )

    # --- Test 3: Empty result set ---
    run_pipeline(
        user_question="Show customers who joined after January 1, 2030.",
        db_params=db_params,
        tables=my_tables
    )


if __name__ == "__main__":
    main()