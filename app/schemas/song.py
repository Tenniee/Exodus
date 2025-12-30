# schemas/song.py
"""
Pydantic schemas for song-related requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from fastapi import Form
from typing import Optional
from pydantic import BaseModel, Field

# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class SongCreate(BaseModel):
    song_name: str = Field(..., min_length=1, max_length=255)
    artist_name: str = Field(..., min_length=1, max_length=255)
    linktree: str = Field(..., min_length=1, max_length=500)
    artist_id: Optional[int] = None

    @classmethod
    def as_form(
        cls,
        song_name: str = Form(...),
        artist_name: str = Form(...),
        linktree: str = Form(...),
        artist_id: Optional[int] = Form(None),
    ):
        return cls(
            song_name=song_name,
            artist_name=artist_name,
            linktree=linktree,
            artist_id=artist_id,
        )

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
    artist_id: Optional[int]
    cover_art_url: str
    linktree: str
    created_at: datetime
    
    class Config:
        from_attributes = True



class SongWithOrderResponse(BaseModel):
    """
    Schema for song data with display order (used in artist profile)
    """
    id: int
    song_name: str
    artist_name: str
    artist_id: int
    cover_art_url: str
    linktree: str
    created_at: datetime
    display_order: Optional[int]  # Will be None if no custom order set
    
    class Config:
        from_attributes = True
