import os
from peewee import PostgresqlDatabase
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# Retrieve the database configuration from environment variables
db_name = os.environ["DB_NAME"]
db_user = os.environ["DB_USER"]
db_password = os.environ["DB_PASSWORD"]
db_host = os.environ["DB_HOST"]
db_port = os.environ["DB_PORT"]

# Create a PostgreSQL database instance
db = PostgresqlDatabase(
    db_name,
    user=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
)