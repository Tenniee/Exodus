from pydantic import BaseModel, EmailStr, Field

# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class UserSignup(BaseModel):
    """
    Schema for signup request
    Pydantic validates that incoming data matches this structure
    """
    first_name: str = Field(..., min_length=1, max_length=100)  # ... means required
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr  # EmailStr automatically validates email format
    password: str = Field(..., min_length=1)  # No max length for password input
    
    class Config:
        # This allows Pydantic to work with SQLAlchemy models
        from_attributes = True

class UserLogin(BaseModel):
    """
    Schema for login request
    Only needs email and password
    """
    email: EmailStr
    password: str

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class Token(BaseModel):
    """
    Schema for token response
    This is what we send back after successful signup/login
    """
    access_token: str
    token_type: str = "bearer"  # Standard token type for JWT

class UserResponse(BaseModel):
    """
    Schema for user data in responses
    We don't send the password back!
    """
    id: int
    first_name: str
    last_name: str
    email: str
    
    class Config:
        from_attributes = True


# ============================================================================
# ============================================================================
# ============================================================================
