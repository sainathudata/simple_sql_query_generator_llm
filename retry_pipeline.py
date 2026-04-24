# retry_pipeline.py
from dataclasses import dataclass, field
from typing import Optional
from schema_extractor import SchemaExtractor
from simple_query_generator import SimpleSQLQueryGenerator
from sql_validator import SQLValidator
from sql_executor import execute_query, ExecutionResult
from sql_corrector import correct_sql


@dataclass
class AttemptLog:
    attempt: int
    sql: str
    validation_passed: bool
    execution_success: bool
    error_message: Optional[str] = None


@dataclass
class PipelineResult:
    success: bool
    final_sql: Optional[str] = None
    execution_result: Optional[ExecutionResult] = None
    total_attempts: int = 0
    attempts: list[AttemptLog] = field(default_factory=list)
    failure_reason: Optional[str] = None


def run_with_retry(
    user_question: str,
    db_params: dict,
    tables: list[str],
    max_retries: int = 3
) -> PipelineResult:
    """
    Runs the full NL → SQL → validate → execute pipeline with
    automatic self-correction on execution failure.

    Returns a PipelineResult with the full attempt log.
    """
    # One-time setup
    extractor = SchemaExtractor(db_params)
    schema_md = extractor.format_schema_for_llm(tables)

    generator = SimpleSQLQueryGenerator()
    validator = SQLValidator()

    attempt_logs = []
    current_sql = None
    last_error = None

    for attempt in range(1, max_retries + 1):
        print(f"\n{'='*60}")
        print(f"ATTEMPT {attempt} of {max_retries}")
        print(f"{'='*60}")

        # Generate or correct
        if attempt == 1:
            print("\n[GENERATE] Sending question to LLM...")
            current_sql = generator.generate_query(user_question, schema_md)
        else:
            # Feed the previous error back to the LLM
            current_sql = correct_sql(
                original_sql=current_sql,
                error_message=last_error,
                schema_md=schema_md,
                attempt=attempt
            )

        print(f"\n--- SQL (Attempt {attempt}) ---")
        print(current_sql)

        # Validate
        is_valid, reason = validator.validate(current_sql)
        if not is_valid:
            log = AttemptLog(
                attempt=attempt,
                sql=current_sql,
                validation_passed=False,
                execution_success=False,
                error_message=f"Validation blocked: {reason}"
            )
            attempt_logs.append(log)
            print(f"\n[BLOCKED] Validator rejected query: {reason}")
            # Dangerous SQL shouldn't be retried — stop immediately
            return PipelineResult(
                success=False,
                total_attempts=attempt,
                attempts=attempt_logs,
                failure_reason=f"Query blocked by validator: {reason}"
            )

        print("\n[VALID] Query passed validation.")

        # Execute
        result = execute_query(current_sql, db_params)

        log = AttemptLog(
            attempt=attempt,
            sql=current_sql,
            validation_passed=True,
            execution_success=result.success,
            error_message=result.error_message if not result.success else None
        )
        attempt_logs.append(log)

        if result.success:
            print(f"\n[SUCCESS] Query executed successfully on attempt {attempt}.")
            return PipelineResult(
                success=True,
                final_sql=current_sql,
                execution_result=result,
                total_attempts=attempt,
                attempts=attempt_logs
            )

        # Execution failed — prepare for retry
        last_error = result.error_message
        print(f"\n[FAILED] Execution error: {last_error}")

        if attempt < max_retries:
            print(f"[RETRY] Will attempt self-correction...")
        else:
            print(f"\n[EXHAUSTED] All {max_retries} attempts failed.")

    return PipelineResult(
        success=False,
        final_sql=current_sql,
        total_attempts=max_retries,
        attempts=attempt_logs,
        failure_reason=f"Max retries ({max_retries}) exhausted. Last error: {last_error}"
    )