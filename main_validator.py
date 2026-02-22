import os
from dotenv import load_dotenv
from schema_extractor import SchemaExtractor
from simple_query_generator import SimpleSQLQueryGenerator
from sql_validator import SQLValidator

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
    #user_question = "Show me the top 5 customers by total order amount."
    user_question = "Delete all the orders placed today"
    sql_query = generator.generate_query(user_question, schema_md)
    validator = SQLValidator(allowed_tables=my_tables)
    is_valid, error = validator.validate(sql_query)
    print(f"--- Database Schema ---\n{schema_md}")
    print(f"User Question: {user_question}\n")
    print(f"--- Generated SQL ---\n{sql_query}\n")
    print(f"Validation Result: {'Valid' if is_valid else f'Invalid: {error}'}")

if __name__ == "__main__":
    main()