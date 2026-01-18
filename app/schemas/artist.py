"""
Pydantic schemas for artist-related requests and responses
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.song import SongResponse, SongWithOrderResponse
from app.schemas.video import VideoResponse, VideoWithOrderResponse

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
    genres: List[str]
    
    # Optional links
    spotify_link: Optional[str]
    apple_music_link: Optional[str]
    youtube_link: Optional[str]
    youtube_music_link: Optional[str]
    instagram_link: Optional[str]
    x_link: Optional[str]
    tiktok_link: Optional[str]
    
    display_order: int  # NEW FIELD
    created_at: datetime
    
    class Config:
        from_attributes = True



class ArtistWithSongsResponse(BaseModel):
    """
    Schema for artist data with their songs in paginated list
    """
    id: int
    artist_name: str
    banner_image_url: str
    image_url: str
    genres: List[str]
    
    # Optional links
    spotify_link: Optional[str]
    apple_music_link: Optional[str]
    youtube_link: Optional[str]
    youtube_music_link: Optional[str]
    instagram_link: Optional[str]
    x_link: Optional[str]
    tiktok_link: Optional[str]
    
    display_order: int  # NEW FIELD
    created_at: datetime
    
    # Songs by this artist
    songs: List[SongResponse]
    
    class Config:
        from_attributes = True

class PaginationMeta(BaseModel):
    """
    Pagination metadata
    """
    total: int
    page: int
    per_page: int
    total_pages: int

class ArtistListResponse(BaseModel):
    """
    Response schema for paginated artist list
    """
    data: List[ArtistWithSongsResponse]
    meta: PaginationMeta

# ============================================================================
# SINGLE ARTIST DETAIL RESPONSE
# ============================================================================

class ArtistDetailResponse(BaseModel):
    """
    Schema for single artist with all related content (songs and videos)
    """
    id: int
    artist_name: str
    banner_image_url: str
    image_url: str
    genres: List[str]
    
    # Optional links
    spotify_link: Optional[str]
    apple_music_link: Optional[str]
    youtube_link: Optional[str]
    youtube_music_link: Optional[str]
    instagram_link: Optional[str]
    x_link: Optional[str]
    tiktok_link: Optional[str]
    
    display_order: int  # NEW FIELD
    created_at: datetime
    
    # All songs by this artist (with ordering)
    songs: List[SongWithOrderResponse]
    
    # All videos by this artist (with ordering)
    videos: List[VideoWithOrderResponse]
    
    class Config:
        from_attributes = True





class ItemOrder(BaseModel):
    """Schema for individual item order"""
    id: int  # song_id or video_id
    position: int

class ReorderRequest(BaseModel):
    """Schema for reordering items"""
    items: List[ItemOrder]

class ArtistReorderRequest(BaseModel):
    """Schema for reordering all artists"""
    items: List[ItemOrder]  # ItemOrder is from previous reorder schemas




# ============================================================================
# ============================================================================
# ============================================================================
