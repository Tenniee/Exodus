from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status

# ============================================================================
# CONFIGURATION
# ============================================================================

# Secret key for JWT encoding/decoding - CHANGE THIS IN PRODUCTION!
# Generate a secure random key with: openssl rand -hex 32
SECRET_KEY = "your-secret-key-here-change-this-in-production"
ALGORITHM = "HS256"  # Algorithm used to sign the JWT
ACCESS_TOKEN_EXPIRE_WEEKS = 2  # Token expiration time

# ============================================================================
# PASSWORD HASHING
# ============================================================================

# CryptContext handles password hashing securely
# bcrypt is a strong hashing algorithm designed for passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Takes a plain text password and returns a hashed version
    The hash is one-way (you can't reverse it to get the original password)
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain text password matches a hashed password
    
    Args:
        plain_password: The password to check
        hashed_password: The hashed password to check against
    
    Returns:
        True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

# ============================================================================
# JWT TOKEN FUNCTIONS
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT token with the provided data
    
    Args:
        data: Dictionary containing user information (like user_id, email)
        expires_delta: How long until the token expires
    
    Returns:
        Encoded JWT token as a string
    """
    # Make a copy of the data so we don't modify the original
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default to 2 weeks if not specified
        expire = datetime.utcnow() + timedelta(weeks=ACCESS_TOKEN_EXPIRE_WEEKS)
    
    # Add expiration time to the token data
    to_encode.update({"exp": expire})
    
    # Encode the token using our secret key
    # This creates a signed token that can't be tampered with
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """
    Decodes and validates a JWT token
    
    Args:
        token: The JWT token string
    
    Returns:
        Dictionary containing the token's payload (user data)
    
    Raises:
        HTTPException if token is invalid or expired
    """
    try:
        # Decode the token using our secret key
        # This will automatically check if the token is expired
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # Token is invalid or expired
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# ============================================================================
# ============================================================================
