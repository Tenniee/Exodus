# routes/featured_music.py
"""
Featured Music routes
Handles the "New Music" page where admins curate featured songs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.models.database import get_db
from app.models.user import User
from app.models.song import Song
from app.models.featured_music import FeaturedMusic
from app.schemas.song import SongResponse
from app.core.dependencies import get_current_user
from pydantic import BaseModel

# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(
    prefix="/new-music",
    tags=["Featured Music"]
)

# ============================================================================
# SCHEMAS
# ============================================================================

class FeaturedSongResponse(BaseModel):
    """Response schema for featured songs with position"""
    song: SongResponse
    position: int
    
    class Config:
        from_attributes = True

class ReorderFeaturedRequest(BaseModel):
    """Schema for reordering featured songs"""
    positions: List[dict]  # [{"song_id": 45, "position": 1}, ...]

# ============================================================================
# GET ALL FEATURED MUSIC (PUBLIC)
# ============================================================================

@router.get("/", response_model=List[FeaturedSongResponse])
def get_featured_music(db: Session = Depends(get_db)):
    """
    Get all featured songs (PUBLIC - no authentication required)
    
    Returns songs in order as set by admin (ordered by position)
    This is the endpoint for the "New Music" page on the frontend
    
    Args:
        db: Database session
    
    Returns:
        List of featured songs with their positions, ordered by position
    """
    
    # Query featured music joined with songs, ordered by position
    featured_query = db.query(
        FeaturedMusic,
        Song
    ).join(
        Song,
        FeaturedMusic.song_id == Song.id
    ).order_by(
        FeaturedMusic.position.asc()
    ).all()
    
    # Build response
    result = []
    for featured, song in featured_query:
        result.append(FeaturedSongResponse(
            song=SongResponse(
                id=song.id,
                song_name=song.song_name,
                artist_name=song.artist_name,
                artist_id=song.artist_id,
                cover_art_url=song.cover_art_url,
                linktree=song.linktree,
                created_at=song.created_at
            ),
            position=featured.position
        ))
    
    return result


# ============================================================================
# ADD SONG TO FEATURED MUSIC (REQUIRES AUTH)
# ============================================================================

@router.post("/admin-add", status_code=status.HTTP_201_CREATED)
def add_to_featured_music(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a song to the featured music list
    
    This endpoint requires authentication (JWT token)
    
    Song is automatically added to the last position in the featured list
    
    Args:
        song_id: ID of the song to feature
        db: Database session
        current_user: Authenticated user (requires auth)
    
    Returns:
        Success message with assigned position
    
    Raises:
        HTTPException 404 if song not found
        HTTPException 400 if song is already featured
    """
    
    # Verify song exists
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Song with ID {song_id} not found"
        )
    
    # Check if song is already featured
    existing = db.query(FeaturedMusic).filter(
        FeaturedMusic.song_id == song_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This song is already featured"
        )
    
    # Get the current max position
    max_position = db.query(func.max(FeaturedMusic.position)).scalar()
    next_position = 1 if max_position is None else max_position + 1
    
    # Create featured music entry
    try:
        featured_entry = FeaturedMusic(
            song_id=song_id,
            position=next_position
        )
        db.add(featured_entry)
        db.commit()
        
        return {
            "message": "Song added to featured music",
            "song_id": song_id,
            "position": next_position
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add song to featured music: {str(e)}"
        )


# ============================================================================
# REMOVE SONG FROM FEATURED MUSIC (REQUIRES AUTH)
# ============================================================================

@router.delete("/admin-remove/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_featured_music(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a song from the featured music list
    
    This endpoint requires authentication (JWT token)
    
    Args:
        song_id: ID of the song to remove from featured
        db: Database session
        current_user: Authenticated user (requires auth)
    
    Returns:
        204 No Content on success
    
    Raises:
        HTTPException 404 if song is not in featured list
    """
    
    # Find the featured entry
    featured_entry = db.query(FeaturedMusic).filter(
        FeaturedMusic.song_id == song_id
    ).first()
    
    if not featured_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song is not in featured music list"
        )
    
    try:
        db.delete(featured_entry)
        db.commit()
        return None
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove song from featured music: {str(e)}"
        )


# ============================================================================
# REORDER FEATURED MUSIC (REQUIRES AUTH)
# ============================================================================

@router.patch("/admin-reorder", status_code=status.HTTP_200_OK)
def reorder_featured_music(
    reorder_data: ReorderFeaturedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reorder featured music
    
    This endpoint requires authentication (JWT token)
    
    Updates the position for multiple featured songs at once
    
    Args:
        reorder_data: List of song_id and position pairs
        db: Database session
        current_user: Authenticated user (requires auth)
    
    Request body example:
    {
        "positions": [
            {"song_id": 45, "position": 1},
            {"song_id": 23, "position": 2},
            {"song_id": 67, "position": 3}
        ]
    }
    
    Returns:
        Success message
    
    Raises:
        HTTPException 404 if song not in featured list
        HTTPException 500 if update fails
    """
    
    try:
        # Update all positions
        for item in reorder_data.positions:
            song_id = item["song_id"]
            position = item["position"]
            
            # Find existing featured entry
            featured_entry = db.query(FeaturedMusic).filter(
                FeaturedMusic.song_id == song_id
            ).first()
            
            if not featured_entry:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Song with ID {song_id} is not in featured music list"
                )
            
            # Update position
            featured_entry.position = position
        
        db.commit()
        
        return {"message": f"Successfully reordered {len(reorder_data.positions)} featured songs"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder featured music: {str(e)}"
        )