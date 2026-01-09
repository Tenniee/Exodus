# schemas/playlist.py
"""
Pydantic schemas for playlist-related requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class PlaylistCreate(BaseModel):
    """
    Schema for creating a new playlist
    Note: Cover art is uploaded as file separately
    """
    playlist_name: str = Field(..., min_length=1, max_length=255)
    linktree: str = Field(..., min_length=1, max_length=500)

class PlaylistUpdate(BaseModel):
    """
    Schema for updating a playlist
    All fields optional
    """
    playlist_name: Optional[str] = Field(None, min_length=1, max_length=255)
    linktree: Optional[str] = Field(None, min_length=1, max_length=500)

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class PlaylistResponse(BaseModel):
    """
    Schema for playlist data in responses
    """
    id: int
    playlist_name: str
    cover_art_url: str
    linktree: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# ============================================================================
# ============================================================================
