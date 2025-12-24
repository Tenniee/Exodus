"""
Pydantic schemas for artist-related requests and responses
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime

# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class ArtistCreate(BaseModel):
    """
    Schema for creating a new artist
    Note: Images are uploaded as files separately, not in this schema
    """
    artist_name: str = Field(..., min_length=1, max_length=255)
    genres: List[str] = Field(..., min_items=1)  # At least one genre required
    
    # All social/streaming links are optional
    spotify_link: Optional[str] = None
    apple_music_link: Optional[str] = None
    youtube_link: Optional[str] = None
    youtube_music_link: Optional[str] = None
    instagram_link: Optional[str] = None
    x_link: Optional[str] = None
    tiktok_link: Optional[str] = None

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ArtistResponse(BaseModel):
    """
    Schema for artist data in responses
    """
    id: int
    artist_name: str
    banner_image_url: str
    image_url: str
    genres: List[str]  # Will be converted from comma-separated string
    
    # Optional links
    spotify_link: Optional[str]
    apple_music_link: Optional[str]
    youtube_link: Optional[str]
    youtube_music_link: Optional[str]
    instagram_link: Optional[str]
    x_link: Optional[str]
    tiktok_link: Optional[str]
    
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# ============================================================================
# ============================================================================
