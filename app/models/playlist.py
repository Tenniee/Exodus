# models/playlist.py
"""
Playlist database model
Defines the Playlist table structure in the database
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.models.database import Base

# ============================================================================
# PLAYLIST MODEL
# ============================================================================

class Playlist(Base):
    """
    Playlist model - represents the 'playlists' table in the database
    Stores playlist metadata (no actual songs, just name, cover, and link)
    """
    __tablename__ = "playlists"
    
    # Primary key - unique identifier for each playlist
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Playlist name - required
    playlist_name = Column(String(255), nullable=False, index=True)
    
    # Cover art URL from Cloudinary - required
    cover_art_url = Column(String(500), nullable=False)
    
    # Linktree link - required
    linktree = Column(String(500), nullable=False)
    
    # Timestamp when the playlist was created
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ============================================================================
# ============================================================================
# ============================================================================
