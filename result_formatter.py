# result_formatter.py
import csv
import io
from sql_executor import ExecutionResult


def format_as_table(result: ExecutionResult, max_col_width: int = 30) -> str:
    """
    Formats an ExecutionResult into a readable terminal table.
    Returns a plain string — no external dependencies.
    """
    if not result.success:
        return f"\n[ERROR] {result.error_message}\n"

    if result.row_count == 0:
        return "\n[INFO] Query executed successfully. No rows returned.\n"

    # Determine column widths: max of header length and longest value
    col_widths = []
    for i, col in enumerate(result.columns):
        col_values = [str(row[i]) if row[i] is not None else "NULL" for row in result.rows]
        max_val_width = max((len(v) for v in col_values), default=0)
        col_widths.append(min(max(len(col), max_val_width), max_col_width))

    # Build separator line
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    # Build header row
    header = "|" + "|".join(
        f" {col:<{col_widths[i]}} " for i, col in enumerate(result.columns)
    ) + "|"

    # Build data rows
    data_rows = []
    for row in result.rows:
        formatted = "|" + "|".join(
            f" {str(val)[:col_widths[i]] if val is not None else 'NULL':<{col_widths[i]}} "
            for i, val in enumerate(row)
        ) + "|"
        data_rows.append(formatted)

    lines = [
        "",
        separator,
        header,
        separator,
        *data_rows,
        separator,
        f"\n{result.row_count} row(s) returned.",
        ""
    ]
    return "\n".join(lines)


def format_as_csv(result: ExecutionResult) -> str:
    """
    Returns result as a CSV string.
    Useful for piping to a file or downstream processing.
    """
    if not result.success or result.row_count == 0:
        return ""

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(result.columns)
    for row in result.rows:
        writer.writerow(["NULL" if v is None else v for v in row])
    return output.getvalue()