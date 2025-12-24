"""
Pydantic schemas for newsletter subscription requests and responses
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime

# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class NewsletterSubscribe(BaseModel):
    """
    Schema for newsletter subscription request
    Only needs an email address
    """
    email: EmailStr  # Automatically validates email format

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class NewsletterSubscriptionResponse(BaseModel):
    """
    Schema for newsletter subscription response
    Returns subscription details
    """
    id: int
    email: str
    subscribed_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# ============================================================================
# ============================================================================
