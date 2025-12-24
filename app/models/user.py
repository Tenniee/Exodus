from sqlalchemy import Column, Integer, String
from app.models.database import Base

# ============================================================================
# USER MODEL
# ============================================================================

class User(Base):
    """
    User model - represents the 'users' table in the database
    SQLAlchemy will automatically create this table with these columns
    """
    __tablename__ = "users"  # Name of the table in the database
    
    # Primary key - unique identifier for each user
    # autoincrement=True means the database will automatically assign IDs (1, 2, 3, etc.)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # User's first name - String with max length 100, cannot be null
    first_name = Column(String(100), nullable=False)
    
    # User's last name
    last_name = Column(String(100), nullable=False)
    
    # Email must be unique (no two users can have the same email)
    # index=True makes searching by email faster
    email = Column(String(255), unique=True, index=True, nullable=False)
    
    # Hashed password (we NEVER store plain text passwords!)
    hashed_password = Column(String(255), nullable=False)


# ============================================================================
# ============================================================================
# ============================================================================
