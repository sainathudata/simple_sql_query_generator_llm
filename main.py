import os
from dotenv import load_dotenv
from schema_extractor import SchemaExtractor
from simple_query_generator import SimpleSQLQueryGenerator

# Load environment variables
load_dotenv(override=True)

def main():
    # 1. Config & Connection
    # If running locally
    db_params = {
        "SERVER": "(localdb)\\MSSQLLocalDB",
        "DATABASE": "master",
        "Trusted_Connection": "yes",
        "Encrypt": "no"
    }
    """
    # If using environment variables (e.g., for production)
    db_params = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    """
    # 2. Extract Schema
    my_tables = ["customers", "orders"]
    extractor = SchemaExtractor(db_params)
    schema_md = extractor.format_schema_for_llm(my_tables)
    
    # 3. Generate Query
    generator = SimpleSQLQueryGenerator()
    user_question = "Show me the top 5 customers by total order amount."
    sql_query = generator.generate_query(user_question, schema_md)
    
    print(f"--- Database Schema ---\n{schema_md}")
    print(f"User Question: {user_question}\n")
    print(f"--- Generated SQL ---\n{sql_query}")

if __name__ == "__main__":
    main()