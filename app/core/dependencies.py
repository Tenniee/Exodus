"""
FastAPI dependencies for authentication and database access
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.user import User
from app.core.security import decode_access_token

# ============================================================================
# AUTHENTICATION SETUP
# ============================================================================

# HTTPBearer is a security scheme for bearer token authentication
# This tells FastAPI to look for "Authorization: Bearer <token>" in the request headers
security = HTTPBearer()

# ============================================================================
# AUTHENTICATION DEPENDENCY
# ============================================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that validates the JWT token and returns the current user
    Use this in endpoints that require authentication
    
    How it works:
    1. Extracts the token from the Authorization header
    2. Decodes and validates the token
    3. Looks up the user in the database
    4. Returns the User object
    
    Usage in endpoints:
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            # current_user is now available and authenticated
            return {"user_id": current_user.id}
    
    Args:
        credentials: The bearer token from the Authorization header (automatic)
        db: Database session (automatic)
    
    Returns:
        User object of the authenticated user
    
    Raises:
        HTTPException if token is invalid or user doesn't exist
    """
    # Extract the token from the credentials
    token = credentials.credentials
    
    # Decode the token to get user data
    # This will raise HTTPException if token is invalid or expired
    payload = decode_access_token(token)
    
    # Get the user_id from the token payload
    user_id: int = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Look up the user in the database
    # db.query(User) starts a query on the User table
    # .filter() adds a WHERE clause (WHERE id = user_id)
    # .first() returns the first result or None
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


# ============================================================================
# ============================================================================
# ============================================================================
