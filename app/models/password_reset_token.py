# models/password_reset_token.py
"""
Password Reset Token model
Stores OTPs for password reset functionality
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.models.database import Base

# ============================================================================
# PASSWORD RESET TOKEN MODEL
# ============================================================================

class PasswordResetToken(Base):
    """
    PasswordResetToken model - stores OTPs for password reset
    """
    __tablename__ = "password_reset_tokens"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Email of the user requesting password reset
    email = Column(String(255), nullable=False, index=True)
    
    # 6-digit OTP
    otp = Column(String(6), nullable=False, index=True)
    
    # Timestamp when the OTP was created
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Whether the OTP has been used
    used = Column(Boolean, default=False, nullable=False)


# ============================================================================
# ============================================================================
# ============================================================================
