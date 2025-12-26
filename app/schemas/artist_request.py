# schemas/artist_request.py
"""
Pydantic schemas for artist request-related requests and responses
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class ArtistRequestSubmit(BaseModel):
    """
    Schema for submitting an artist request
    Only artist_name and email are required
    """
    artist_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    
    # Optional social media and streaming links
    ig_link: Optional[str] = Field(None, max_length=500)
    yt_link: Optional[str] = Field(None, max_length=500)
    spotify_link: Optional[str] = Field(None, max_length=500)
    apple_music_link: Optional[str] = Field(None, max_length=500)
    
    # Service selections - all default to False if not provided
    music_distribution: bool = False
    music_publishing: bool = False
    prod_and_engineering: bool = False
    marketing_and_promotions: bool = False

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ArtistRequestResponse(BaseModel):
    """
    Schema for artist request data in responses
    """
    id: int
    artist_name: str
    email: str
    
    # Optional links
    ig_link: Optional[str]
    yt_link: Optional[str]
    spotify_link: Optional[str]
    apple_music_link: Optional[str]
    
    # Service selections
    music_distribution: bool
    music_publishing: bool
    prod_and_engineering: bool
    marketing_and_promotions: bool
    
    # Status and timestamp
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True