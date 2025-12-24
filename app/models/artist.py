"""
Artist database model
Defines the Artist table structure in the database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.models.database import Base

# ============================================================================
# ARTIST MODEL
# ============================================================================

class Artist(Base):
    """
    Artist model - represents the 'artists' table in the database
    Stores artist information including images and social media links
    """
    __tablename__ = "artists"
    
    # Primary key - unique identifier for each artist
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Artist name - required field
    artist_name = Column(String(255), nullable=False, index=True)
    
    # Banner image URL from Cloudinary - required
    banner_image_url = Column(String(500), nullable=False)
    
    # Profile/Artist image URL from Cloudinary - required
    image_url = Column(String(500), nullable=False)
    
    # Genres - stored as comma-separated string (e.g., "Hip Hop,R&B,Pop")
    # Text type allows for longer strings than String
    genres = Column(Text, nullable=False)
    
    # Social media and streaming platform links - all optional
    spotify_link = Column(String(500), nullable=True)
    apple_music_link = Column(String(500), nullable=True)
    youtube_link = Column(String(500), nullable=True)
    youtube_music_link = Column(String(500), nullable=True)
    instagram_link = Column(String(500), nullable=True)
    x_link = Column(String(500), nullable=True)
    tiktok_link = Column(String(500), nullable=True)
    
    # Timestamp when the artist was added
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ============================================================================
# ============================================================================
# ============================================================================
