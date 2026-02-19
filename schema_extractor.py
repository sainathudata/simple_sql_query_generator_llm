from mssql_python import connect
from typing import Dict, List, Optional

class SchemaExtractor:
    def __init__(self, connection_string):
        # Using the mssql-python connect method
        if isinstance(connection_string, dict):
            # Unpacks dict keys into: connect(SERVER='...', DATABASE='...')
            self.conn = connect(**connection_string)
        else:
            # Treats it as a standard connection string
            self.conn = connect(connection_string)

        self.cursor = self.conn.cursor()
    
    def get_tables(self, include_tables: Optional[List[str]] = None) -> List[str]:
        """Get specific or all table names in the database."""
        if include_tables:
            # Format list for T-SQL IN clause: 'table1', 'table2'
            placeholders = ", ".join([f"'{t}'" for t in include_tables])
            filter_clause = f"AND table_name IN ({placeholders})"
        else:
            filter_clause = ""

        query = f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_type = 'BASE TABLE'
            AND table_schema = 'dbo'
            {filter_clause}
            ORDER BY table_name;
        """
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_table_schema(self, table_name: str) -> Dict:
        """Get detailed schema for a specific MSSQL table."""
        # 1. Get Columns
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = ?
            ORDER BY ordinal_position;
        """
        self.cursor.execute(query, (table_name,))
        columns = []
        for row in self.cursor.fetchall():
            columns.append({
                'name': row[0],     # Accessing by index
                'type': row[1],
                'nullable': row[2] == 'YES',
                'default': row[3]
            })
        
        # 2. Get Primary Keys (Improved Query)
        pk_query = """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
            AND TABLE_NAME = ?;
        """
        self.cursor.execute(pk_query, (table_name,))
        # fetchall() returns a list of tuples like [('id',), ('other_pk',)]
        primary_keys = [row[0] for row in self.cursor.fetchall()]
        
        return {
            'table_name': table_name,
            'columns': columns,
            'primary_keys': primary_keys
        }

    def get_foreign_keys(self, table_name: str) -> List[Dict]:
        """Get foreign key relationships in MSSQL."""
        query = """
            SELECT 
                cp.name AS column_name,
                tr.name AS referenced_table,
                cr.name AS referenced_column
            FROM sys.foreign_keys AS fk
            INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
            INNER JOIN sys.tables AS tp ON fkc.parent_object_id = tp.object_id
            INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
            INNER JOIN sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
            INNER JOIN sys.columns AS cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
            WHERE tp.name = ?;
        """
        self.cursor.execute(query, (table_name,))
        # Accessing each column by its index in the tuple
        return [{
            'column': row[0],
            'references_table': row[1],
            'references_column': row[2]
        } for row in self.cursor.fetchall()]

    def format_schema_for_llm(self, target_tables: Optional[List[str]] = None) -> str:
        """Format the filtered schema for LLM consumption."""
        tables = self.get_tables(include_tables=target_tables)
        schema_description = "# Database Schema (MSSQL)\n\n"
        
        for table in tables:
            schema = self.get_table_schema(table)
            fks = self.get_foreign_keys(table)
            
            schema_description += f"## Table: {table}\n"
            schema_description += "Columns:\n"
            
            for col in schema['columns']:
                pk_marker = " (PRIMARY KEY)" if col['name'] in schema['primary_keys'] else ""
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                schema_description += f"- {col['name']}: {col['type']} {nullable}{pk_marker}\n"
            
            if fks:
                schema_description += "\nForeign Keys:\n"
                for fk in fks:
                    schema_description += f"- {fk['column']} → {fk['references_table']}.{fk['references_column']}\n"
            
            schema_description += "\n"
        
        return schema_description
    
    def close(self):
        """Close database connection."""
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    # 1. Define your connection string
    # Change 'YourDatabaseName' and 'YourServerName' to your actual database
    db_config = {
        "SERVER": "YourServerName",
        "DATABASE": "YourDatabaseName",
        "Trusted_Connection": "yes",
        "Encrypt": "no"
    }
    # 2. Define the specific tables you want to extract, this is an 
    #    optional field, you can skip it to get details of all tables.
    MY_TABLES = ["customers", "orders"] 

    extractor = None
    try:
        # 3. Initialize and run
        extractor = SchemaExtractor(db_config)
        schema_text = extractor.format_schema_for_llm(target_tables=MY_TABLES)
        
        print(schema_text)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if extractor:
            extractor.close()