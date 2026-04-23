# sql_executor.py
import pyodbc
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ExecutionResult:
    success: bool
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    row_count: int = 0
    error_message: Optional[str] = None


def execute_query(sql: str, db_params: dict) -> ExecutionResult:
    """
    Executes a validated SQL query against MS SQL Server.
    Returns an ExecutionResult dataclass — never raises.

    db_params keys:
      - SERVER, DATABASE, Trusted_Connection, Encrypt  (local dev)
      - or SERVER, DATABASE, UID, PWD                  (server auth)
    """
    conn = None
    try:
        # Build connection string dynamically from db_params
        conn_parts = [f"DRIVER={{ODBC Driver 17 for SQL Server}}"]
        conn_parts.append(f"SERVER={db_params['SERVER']}")
        conn_parts.append(f"DATABASE={db_params['DATABASE']}")

        if db_params.get("Trusted_Connection"):
            conn_parts.append(f"Trusted_Connection={db_params['Trusted_Connection']}")
        if db_params.get("Encrypt"):
            conn_parts.append(f"Encrypt={db_params['Encrypt']}")
        if db_params.get("UID"):
            conn_parts.append(f"UID={db_params['UID']}")
        if db_params.get("PWD"):
            conn_parts.append(f"PWD={db_params['PWD']}")

        conn_str = ";".join(conn_parts)

        conn = pyodbc.connect(conn_str, autocommit=False)
        cursor = conn.cursor()

        cursor.execute(sql)

        # Extract column names from cursor description
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()

        return ExecutionResult(
            success=True,
            columns=columns,
            rows=[tuple(row) for row in rows],
            row_count=len(rows)
        )

    except pyodbc.ProgrammingError as e:
        return ExecutionResult(success=False, error_message=f"SQL error: {str(e)}")

    except pyodbc.OperationalError as e:
        return ExecutionResult(success=False, error_message=f"Connection error: {str(e)}")

    except Exception as e:
        return ExecutionResult(success=False, error_message=f"Unexpected error: {str(e)}")

    finally:
        if conn:
            conn.close()