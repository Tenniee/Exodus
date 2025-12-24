"""
Pydantic schemas for song-related requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class SongCreate(BaseModel):
    """
    Schema for creating a new song
    Note: Cover art is uploaded as a file separately, not in this schema
    """
    song_name: str = Field(..., min_length=1, max_length=255)
    artist_name: str = Field(..., min_length=1, max_length=255)
    linktree: str = Field(..., min_length=1, max_length=500)

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class SongResponse(BaseModel):
    """
    Schema for song data in responses
    """
    id: int
    song_name: str
    artist_name: str
    cover_art_url: str
    linktree: str
    created_at: datetime
    
    class Config:
        from_attributes = True
