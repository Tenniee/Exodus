from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Database URL - Change this based on your database choice
# For SQLite (easiest for local testing):
# DATABASE_URL = "sqlite:///./test.db"

# For PostgreSQL:
DATABASE_URL = "postgresql://neondb_owner:npg_pCUvIczyK2L9@ep-cool-frost-af45s6ic-pooler.c-2.us-west-2.aws.neon.tech/exodus_db?sslmode=require&channel_binding=require"

# For MySQL:
# DATABASE_URL = "mysql+pymysql://username:password@localhost/dbname"

# ============================================================================
# DATABASE ENGINE & SESSION SETUP
# ============================================================================

# Create the database engine
# The engine is the starting point for any SQLAlchemy application
# It manages connections to the database
# check_same_thread=False is needed for SQLite only (allows multiple threads)
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# SessionLocal is a factory for creating database sessions
# A session is like a "workspace" for database operations
# Each request will get its own session to ensure isolation
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all our database models (tables)
# All models will inherit from this
Base = declarative_base()

# ============================================================================
# DATABASE DEPENDENCY FUNCTION
# ============================================================================

def get_db():
    """
    Dependency function that provides a database session
    FastAPI will automatically call this for endpoints that need database access
    The session is automatically closed after the request is complete
    
    Usage in endpoints:
        def my_endpoint(db: Session = Depends(get_db)):
            # Use db here to query the database
    """
    db = SessionLocal()  # Create a new database session
    try:
        yield db  # Provide the session to the endpoint
    finally:
        db.close()  # Always close the session when done

# ============================================================================
# INITIALIZE DATABASE
# ============================================================================

def init_db():
    """
    Create all tables in the database
    This checks if tables exist and creates them if they don't
    Call this when starting the application
    """
    # Import all models here so SQLAlchemy knows about them
    from app.models.user import User  # noqa
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
