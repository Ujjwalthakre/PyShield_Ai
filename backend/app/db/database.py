from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Create a SQLite database file named 'pyshield.db' in the backend folder
SQLALCHEMY_DATABASE_URL = "sqlite:///./pyshield.db"

# 2. The Engine is the actual connection to the database
# (check_same_thread is needed only for SQLite in FastAPI)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. A SessionFactory to spawn database sessions when we need to query data
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. The Base class that all our DB models will inherit from
Base = declarative_base()