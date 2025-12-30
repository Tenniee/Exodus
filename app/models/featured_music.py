# models/featured_music.py
"""
Featured Music model
Stores songs featured on the "New Music" page with ordering
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.models.database import Base

# ============================================================================
# FEATURED MUSIC MODEL
# ============================================================================

class FeaturedMusic(Base):
    """
    FeaturedMusic model - stores songs featured on the New Music page
    Allows admins to curate and order featured songs
    """
    __tablename__ = "featured_music"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to songs table
    # unique=True ensures a song can only be featured once
    song_id = Column(Integer, ForeignKey('songs.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    
    # Display position in the featured list
    # Lower number = appears first (1, 2, 3...)
    position = Column(Integer, nullable=False)
    
    # Timestamp when song was added to featured list
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ============================================================================
# ============================================================================
# ============================================================================
