# models/artist_request.py
"""
Artist Request database model
Stores requests from artists wanting to join the platform
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.models.database import Base

# ============================================================================
# ARTIST REQUEST MODEL
# ============================================================================

class ArtistRequest(Base):
    """
    ArtistRequest model - represents the 'artist_requests' table in the database
    Stores artist onboarding requests with their contact info and selected services
    """
    __tablename__ = "artist_requests"
    
    # Primary key - unique identifier for each request
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Artist name - required
    artist_name = Column(String(255), nullable=False, index=True)
    
    # Email - required and must be unique (can't submit multiple requests with same email)
    email = Column(String(255), nullable=False, unique=True, index=True)
    
    # Social media and streaming links - all optional
    ig_link = Column(String(500), nullable=True)
    yt_link = Column(String(500), nullable=True)
    spotify_link = Column(String(500), nullable=True)
    apple_music_link = Column(String(500), nullable=True)
    
    # Service selection - boolean fields for each service
    # Default False means not selected
    music_distribution = Column(Boolean, default=False, nullable=False)
    music_publishing = Column(Boolean, default=False, nullable=False)
    prod_and_engineering = Column(Boolean, default=False, nullable=False)
    marketing_and_promotions = Column(Boolean, default=False, nullable=False)
    
    # Status of the request - "pending", "approved", or "rejected"
    status = Column(String(50), default="pending", nullable=False, index=True)
    
    # Timestamp when the request was created
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)