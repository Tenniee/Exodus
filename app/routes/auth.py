"""
Authentication routes
Handles user signup, login, and current user retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from typing import Optional
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.user import User
from app.schemas.user import UserSignup, UserLogin, Token, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from pydantic import EmailStr

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
async def signup(
    # Form fields
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    
    # Optional file upload
    profile_picture: Optional[UploadFile] = File(None),
    
    # Dependencies
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    Now accepts multipart/form-data to support optional profile picture upload
    
    Process:
    1. Check if email already exists
    2. Hash the password
    3. Upload profile picture to Cloudinary if provided
    4. Create new user in database
    5. Generate JWT token
    6. Return token to client
    
    Args:
        first_name: User's first name
        last_name: User's last name
        email: User's email address
        password: User's password (will be hashed)
        profile_picture: Optional profile picture file (jpg/png/webp)
        db: Database session (automatically injected by FastAPI)
    
    Returns:
        JWT token for the newly created user
    
    Raises:
        HTTPException 400 if email already registered
        HTTPException 500 if profile picture upload fails
    """
    
    # Check if user with this email already exists
    existing_user = db.query(User).filter(User.email == email.lower()).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password before storing it
    hashed_pwd = hash_password(password)
    
    # Create a new User instance (without profile picture first)
    new_user = User(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        email=email.lower().strip(),
        hashed_password=hashed_pwd,
        profile_picture_url=None  # Will be updated if picture provided
    )
    
    # Add the new user to the database session and commit to get ID
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Upload profile picture if provided
    if profile_picture is not None:
        try:
            from core.cloudinary_config import upload_user_profile_picture
            
            # Upload to Cloudinary using the user's ID
            profile_picture_url = upload_user_profile_picture(profile_picture, new_user.id)
            
            # Update user with profile picture URL
            new_user.profile_picture_url = profile_picture_url
            db.commit()
            db.refresh(new_user)
            
        except Exception as e:
            # If profile picture upload fails, still allow signup but without picture
            # You could also choose to rollback the entire signup here
            print(f"Profile picture upload failed: {str(e)}")
    
    # Create a JWT token for the new user
    access_token = create_access_token(
        data={"user_id": new_user.id, "email": new_user.email}
    )
    
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



@router.patch("/edit-profile", response_model=UserResponse)
async def edit_profile(
    # Form fields - all optional
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    email: Optional[EmailStr] = Form(None),
    
    # Optional file upload
    profile_picture: Optional[UploadFile] = File(None),
    
    # Dependencies
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Edit current user's profile
    
    This endpoint requires authentication (JWT token)
    All fields are optional - only provided fields will be updated
    Password cannot be changed here (use separate change password endpoint)
    
    Process:
    1. Get current user from token
    2. Update fields if provided
    3. If email changed, verify it's not taken
    4. If new profile picture provided, delete old one and upload new one
    5. Save changes to database
    6. Return updated user details
    
    Args:
        first_name: New first name (optional)
        last_name: New last name (optional)
        email: New email address (optional)
        profile_picture: New profile picture file (optional)
        db: Database session
        current_user: Authenticated user (from JWT token)
    
    Returns:
        Updated user information
    
    Raises:
        HTTPException 400 if new email is already taken
        HTTPException 500 if update fails
    """
    
    # Update first name if provided
    if first_name is not None:
        current_user.first_name = first_name.strip()
    
    # Update last name if provided
    if last_name is not None:
        current_user.last_name = last_name.strip()
    
    # Update email if provided (check if not taken)
    if email is not None:
        email_lower = email.lower().strip()
        
        # Check if new email is different from current
        if email_lower != current_user.email:
            # Check if email is already taken by another user
            existing_user = db.query(User).filter(
                User.email == email_lower,
                User.id != current_user.id
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken by another user"
                )
            
            current_user.email = email_lower
    
    # Update profile picture if provided
    if profile_picture is not None:
        from core.cloudinary_config import upload_user_profile_picture, delete_cloudinary_image
        
        # Delete old profile picture from Cloudinary if exists
        if current_user.profile_picture_url:
            delete_cloudinary_image(current_user.profile_picture_url)
        
        # Upload new profile picture
        new_picture_url = upload_user_profile_picture(profile_picture, current_user.id)
        current_user.profile_picture_url = new_picture_url
    
    # Save changes to database
    try:
        db.commit()
        db.refresh(current_user)
        
        return current_user
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )