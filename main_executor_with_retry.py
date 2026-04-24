# main_executor_with_retry.py
import os
from dotenv import load_dotenv
from retry_pipeline import run_with_retry
from result_formatter import format_as_table, format_as_csv

load_dotenv(override=True)

DB_PARAMS = {
    "SERVER": "(localdb)\\MSSQLLocalDB",
    "DATABASE": "master",
    "Trusted_Connection": "yes",
    "Encrypt": "no"
}
TABLES = ["customers", "orders"]


def run_and_display(question: str, max_retries: int = 3) -> None:
    print(f"\nQuestion: {question}")

    pipeline_result = run_with_retry(
        user_question=question,
        db_params=DB_PARAMS,
        tables=TABLES,
        max_retries=max_retries
    )

    print(f"\n{'='*60}")
    print("PIPELINE SUMMARY")
    print(f"{'='*60}")
    print(f"  Status        : {'SUCCESS' if pipeline_result.success else 'FAILED'}")
    print(f"  Total attempts: {pipeline_result.total_attempts}")

    for log in pipeline_result.attempts:
        status = "✓" if log.execution_success else "✗"
        print(f"  Attempt {log.attempt}     : {status}  {log.error_message or 'OK'}")

    if pipeline_result.success:
        print(format_as_table(pipeline_result.execution_result))

        if pipeline_result.execution_result.row_count > 0:
            csv_output = format_as_csv(pipeline_result.execution_result)
            with open("query_results.csv", "w", newline="") as f:
                f.write(csv_output)
            print("[INFO] Results saved to query_results.csv")

        if pipeline_result.total_attempts > 1:
            print(f"\n[NOTE] Required {pipeline_result.total_attempts} attempts.")
            print(f"Final SQL:\n{pipeline_result.final_sql}")
    else:
        print(f"\n  Failure reason: {pipeline_result.failure_reason}")


def main():
    # Test 1: Query that succeeds first time
    run_and_display("Show me the top 5 customers by total order amount.")

    # Test 2: Query that initially fails (wrong alias) — self-corrects
    run_and_display("Show total revenue per customer, sorted by highest spender.")

    # Test 3: Deliberately dangerous — should be blocked, no retry
    run_and_display("Delete all orders placed today.")


if __name__ == "__main__":
    main()