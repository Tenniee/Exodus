# models/video.py
"""
Video database model
Defines the Video table structure in the database
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.database import Base
from fastapi import Form

# ============================================================================
# VIDEO MODEL
# ============================================================================

class Video(Base):
    """
    Video model - represents the 'videos' table in the database
    Stores video information including YouTube links and auto-generated thumbnails
    """
    __tablename__ = "videos"
    
    # Primary key - unique identifier for each video
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Video name - required field
    video_name = Column(String(255), nullable=False, index=True)
    
    # Video link - YouTube or other platform URL - required
    video_link = Column(String(500), nullable=False)
    
    # Artist name - stored as string for display purposes
    artist_name = Column(String(255), nullable=False, index=True)
    
    # Artist ID - NOW REQUIRED - links to artists table
    artist_id = Column(Integer, ForeignKey('artists.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Thumbnail URL - auto-generated for YouTube videos, null for other platforms
    thumbnail_url = Column(String(500), nullable=True)
    
    # Timestamp when the video was added
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

