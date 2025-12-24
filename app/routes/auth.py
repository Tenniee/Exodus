"""
Authentication routes
Handles user signup, login, and current user retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.user import User
from app.schemas.user import UserSignup, UserLogin, Token, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user

# ============================================================================
# ROUTER SETUP
# ============================================================================

# Create an APIRouter for authentication endpoints
# prefix="/auth" means all routes will start with /auth
# tags help organize endpoints in the API documentation
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# ============================================================================
# SIGNUP ENDPOINT
# ============================================================================

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """
    Register a new user
    
    Process:
    1. Check if email already exists
    2. Hash the password
    3. Create new user in database
    4. Generate JWT token
    5. Return token to client
    
    Args:
        user_data: User signup information (first_name, last_name, email, password)
        db: Database session (automatically injected by FastAPI)
    
    Returns:
        JWT token for the newly created user
    
    Raises:
        HTTPException 400 if email already registered
    """
    # Check if user with this email already exists
    # db.query(User) - starts a query on the User table
    # .filter(User.email == user_data.email) - adds WHERE email = 'user@example.com'
    # .first() - returns the first matching user or None
    existing_user = db.query(User).filter(User.email == user_data.email.lower()).first()
    
    if existing_user:
        # Email is already taken, return error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password before storing it
    # NEVER store plain text passwords in the database!
    hashed_pwd = hash_password(user_data.password)
    
    # Create a new User instance with the provided data
    new_user = User(
        first_name=user_data.first_name.strip(),  # .strip() removes leading/trailing whitespace
        last_name=user_data.last_name.strip(),
        email=user_data.email.lower().strip(),  # Store emails in lowercase for consistency
        hashed_password=hashed_pwd
    )
    
    # Add the new user to the database session
    # This stages the user to be inserted
    db.add(new_user)
    
    # Commit the transaction
    # This actually executes the INSERT statement and saves to the database
    db.commit()
    
    # Refresh the user object to get the auto-generated ID from the database
    # After commit, the database assigns an ID, and refresh loads it into our object
    db.refresh(new_user)
    
    # Create a JWT token for the new user
    # The token contains the user's ID and email
    access_token = create_access_token(
        data={"user_id": new_user.id, "email": new_user.email}
    )
    
    # Return the token to the client
    return {"access_token": access_token, "token_type": "bearer"}

# ============================================================================
# LOGIN ENDPOINT
# ============================================================================

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login an existing user
    
    Process:
    1. Find user by email
    2. Verify password matches
    3. Generate JWT token
    4. Return token to client
    
    Args:
        user_data: Login credentials (email and password)
        db: Database session (automatically injected)
    
    Returns:
        JWT token for the authenticated user
    
    Raises:
        HTTPException 401 if credentials are invalid
    """
    # Find user by email in the database
    # Convert email to lowercase to match how we stored it
    user = db.query(User).filter(User.email == user_data.email.lower()).first()
    
    # Check if user exists AND password is correct
    # verify_password() securely compares the plain password with the hashed one
    if not user or not verify_password(user_data.password, user.hashed_password):
        # Don't specify whether email or password was wrong
        # This is a security best practice to prevent user enumeration attacks
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # User authenticated successfully, create a JWT token
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email}
    )
    
    # Return the token to the client
    return {"access_token": access_token, "token_type": "bearer"}

# ============================================================================
# GET CURRENT USER ENDPOINT
# ============================================================================

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get information about the currently authenticated user
    
    This endpoint demonstrates how to protect routes with authentication.
    The get_current_user dependency automatically:
    1. Extracts the token from the Authorization header
    2. Validates the token
    3. Retrieves the user from the database
    4. Injects the user object into this function
    
    Args:
        current_user: Authenticated user (automatically injected by dependency)
    
    Returns:
        User information (without password)
    """
    # Simply return the current user
    # FastAPI automatically converts it to the UserResponse schema
    # which excludes the password field
    return current_user


# ============================================================================
# ============================================================================
# ============================================================================
