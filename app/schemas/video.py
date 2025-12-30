# schemas/video.py
"""
Pydantic schemas for video-related requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from fastapi import Form

# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class VideoCreate(BaseModel):
    """
    Schema for creating a new video
    """
    video_name: str = Field(..., min_length=1, max_length=255)
    video_link: str = Field(..., min_length=1, max_length=500)
    artist_id: Optional[int] = None  # Optional link to artist in database
    @classmethod
    def as_form(
        cls,
        video_name: str = Form(...),
        video_link: str = Form(...),
        artist_id: Optional[int] = Form(None),
    ):
        return cls(
            video_name=video_name,
            video_link=video_link,
            artist_id=artist_id,
        )

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class VideoResponse(BaseModel):
    """
    Schema for video data in responses
    """
    id: int
    video_name: str
    video_link: str
    artist_name: str
    artist_id: Optional[int]
    thumbnail_url: Optional[str]  # Will be None if not a YouTube video
    created_at: datetime
    
    class Config:
        from_attributes = True

class VideoWithOrderResponse(BaseModel):
    """
    Schema for video data with display order (used in artist profile)
    """
    id: int
    video_name: str
    video_link: str
    artist_name: str
    artist_id: int
    thumbnail_url: Optional[str]
    created_at: datetime
    display_order: Optional[int]  # Will be None if no custom order set
    
    class Config:
        from_attributes = True
