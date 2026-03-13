import os
from dataclasses import dataclass

from dotenv import load_dotenv


# Load environment variables from a local .env file in development.
# In production you would typically set these directly in the environment.
load_dotenv()


@dataclass
class Config:
    """Base configuration for the Flask app and database."""

    # Flask settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    # Database connection settings
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "student_management")

    # Power BI embed URL placeholder
    POWER_BI_EMBED_URL: str = os.getenv("POWER_BI_EMBED_URL", "")

    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Build the SQLAlchemy-compatible MySQL URI from the parts."""
        # Using PyMySQL as the MySQL driver.
        user = self.DB_USER
        password = self.DB_PASSWORD
        host = self.DB_HOST
        port = self.DB_PORT
        name = self.DB_NAME
        if password:
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
        return f"mysql+pymysql://{user}@{host}:{port}/{name}"


config = Config()

