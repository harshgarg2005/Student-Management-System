"""
Basic MySQL database initialization script.

This script:
1. Loads environment variables (from .env if present).
2. Connects to the MySQL server.
3. Ensures that the target database exists.

Table creation will be handled later by SQLAlchemy models within the Flask app.
"""

import os
import sys

import pymysql
from dotenv import load_dotenv

from config import config


def ensure_database_exists() -> None:
    """Create the configured database if it does not already exist."""
    load_dotenv()

    db_user = config.DB_USER
    db_password = config.DB_PASSWORD
    db_host = config.DB_HOST
    db_port = int(config.DB_PORT)
    db_name = config.DB_NAME

    try:
        # Connect without specifying a database, so we can create it if needed.
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            autocommit=True,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to connect to MySQL server: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4;")
        print(f"Database '{db_name}' is ready.")
    except Exception as exc:  # noqa: BLE001
        print(f"Error while ensuring database exists: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        connection.close()


if __name__ == "__main__":
    ensure_database_exists()

