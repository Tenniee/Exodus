"""
Song database model
Defines the Song table structure in the database
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.models.database import Base

# ============================================================================
# SONG MODEL
# ============================================================================

class Song(Base):
    """
    Song model - represents the 'songs' table in the database
    Stores song information including cover art and artist name
    """
    __tablename__ = "songs"
    
    # Primary key - unique identifier for each song
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Song name - required field
    song_name = Column(String(255), nullable=False, index=True)
    
    # Artist name - stored as string (can be features, not necessarily in artists table)
    artist_name = Column(String(255), nullable=False, index=True)
    
    # Cover art URL from Cloudinary - required
    cover_art_url = Column(String(500), nullable=False)
    
    # Linktree link - single URL to the song's linktree page - required
    linktree = Column(String(500), nullable=False)
    
    # Timestamp when the song was added
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

