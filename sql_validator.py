import sqlparse
from sqlparse.sql import IdentifierList, Identifier, TokenList
from sqlparse.tokens import Keyword, DML, Name
from typing import Tuple, List, Set

class SQLValidator:
    """Validates and sanitizes T-SQL queries for MSSQL."""
    
    # Use whole-word matching to avoid blocking columns like "created_at"
    DANGEROUS_KEYWORDS = {
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 
        'INSERT', 'UPDATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'INTO'
    }
    
    def __init__(self, allowed_tables: List[str] = None):
        self.allowed_tables = {t.lower() for t in allowed_tables} if allowed_tables else None
    
    def validate(self, query: str) -> Tuple[bool, str]:
        # 1. Basic Syntax & Semicolon check
        if query.count(';') > 1 or (';' in query and not query.strip().endswith(';')):
            return False, "Multiple statements or mid-query semicolons detected"
            
        try:
            parsed = sqlparse.parse(query)
            if not parsed:
                return False, "Invalid SQL syntax"
            statement = parsed[0]
        except Exception as e:
            return False, f"Parse error: {str(e)}"

        # 2. Keyword Check (Token-based to avoid substring issues)
        for token in statement.flatten():
            if token.ttype in Keyword or token.ttype in DML:
                val = token.value.upper()
                if val in self.DANGEROUS_KEYWORDS:
                    return False, f"Dangerous operation detected: {val}"

        # 3. Ensure SELECT or WITH (for CTEs)
        st_type = statement.get_type()
        if st_type not in ['SELECT', 'UNKNOWN']: # CTEs often show as UNKNOWN
            return False, f"Only SELECT queries are allowed (Detected: {st_type})"
        
        # 4. Extract and Validate Tables (Handles JOINs)
        if self.allowed_tables:
            found_tables = self._extract_tables(statement)
            for table in found_tables:
                if table.lower() not in self.allowed_tables:
                    return False, f"Access denied to table: {table}"
        
        return True, "Valid"

    def _extract_tables(self, statement) -> Set[str]:
        """Extracts tables from FROM and JOIN clauses, cleaning T-SQL brackets."""
        tables = set()
        from_seen = False
        for token in statement.tokens:
            # Look for tables after FROM or JOIN
            if token.ttype is Keyword and token.value.upper() in ('FROM', 'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN'):
                from_seen = True
                continue
            
            if from_seen:
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        tables.add(self._clean_name(identifier.get_real_name()))
                    from_seen = False
                elif isinstance(token, Identifier):
                    tables.add(self._clean_name(token.get_real_name()))
                    from_seen = False
                elif token.ttype is Keyword: # End of table list
                    from_seen = False

        return {t for t in tables if t}

    def _clean_name(self, name: str) -> str:
        """Removes MSSQL square brackets [table]."""
        if not name: return name
        return name.strip('[]').strip('"')

    def format_query(self, query: str) -> str:
        return sqlparse.format(query, reindent=True, keyword_case='upper')