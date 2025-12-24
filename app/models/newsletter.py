# models/newsletter.py
"""
Newsletter subscription model
Stores emails of users who subscribed to the newsletter
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.models.database import Base

# ============================================================================
# NEWSLETTER MODEL
# ============================================================================

class NewsletterSubscription(Base):
    """
    NewsletterSubscription model - represents the 'newsletter_subscriptions' table
    Stores email addresses of newsletter subscribers
    """
    __tablename__ = "newsletter_subscriptions"
    
    # Primary key - unique identifier for each subscription
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Email address - must be unique (can't subscribe twice with same email)
    # index=True makes searching by email faster
    email = Column(String(255), unique=True, index=True, nullable=False)
    
    # Timestamp when the subscription was created
    # func.now() automatically sets this to the current time when a record is created
    subscribed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ============================================================================
# ============================================================================
# ============================================================================
