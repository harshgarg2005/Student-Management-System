# Student Management System - Backend Setup

This project is a Flask-based Student Management System backed by a MySQL database.

## 1. Create and configure your environment

1. Create a virtual environment (recommended) and activate it.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the example environment file and fill in the values:

```bash
copy .env.example .env  # On Windows PowerShell / CMD
```

Edit `.env` to match your local MySQL configuration (user, password, host, port, and database name).

## 2. Initialize the MySQL database

With your `.env` file configured and MySQL server running, run:

```bash
python init_db.py
```

This will connect to the MySQL server and ensure that the configured database exists. Table creation will be handled later via SQLAlchemy models in the Flask app.

## 3. Next steps

- Implement the Flask app (`app.py`) using the `Config` class from `config.py` for `SQLALCHEMY_DATABASE_URI` and other settings.
- Define `Student`, `Teacher`, and `Feedback` models and use SQLAlchemy to create tables against the initialized database.

