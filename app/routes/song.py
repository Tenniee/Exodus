"""
Song management routes
Handles adding and editing songs with cover art uploads
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from app.models.database import get_db
from app.models.user import User
from app.models.song import Song
from app.schemas.song import SongResponse
from app.core.dependencies import get_current_user
from app.core.cloudinary_config import upload_song_cover_art, delete_cloudinary_image

# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(
    prefix="/songs",
    tags=["Songs"]
)

# ============================================================================
# ADD SONG ENDPOINT
# ============================================================================

@router.post("/admin-add-song", response_model=SongResponse, status_code=status.HTTP_201_CREATED)
async def add_song(
    # Form fields
    song_name: str = Form(...),
    artist_name: str = Form(...),
    linktree: str = Form(...),
    
    # File upload
    cover_art: UploadFile = File(...),
    
    # Dependencies
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """
    Add a new song with cover art
    
    This endpoint requires authentication (JWT token)
    
    Process:
    1. Upload cover art to Cloudinary (1000x1000, square)
    2. Create song record in database with cover art URL
    3. Return song details
    
    Args:
        song_name: Name of the song
        artist_name: Name of the artist (can be features, doesn't need to exist in artists table)
        linktree: URL to the song's linktree page
        cover_art: Cover art image file (jpg/png/webp)
        db: Database session
        current_user: Authenticated user (from JWT token)
    
    Returns:
        Created song with all details including cover art URL
    
    Raises:
        HTTPException 500 if upload or database operation fails
    """
    
    # ========================================================================
    # STEP 1: Upload cover art to Cloudinary
    # ========================================================================
    
    # Upload cover art (square: 1000x1000)
    cover_art_url = upload_song_cover_art(cover_art, song_name, artist_name)
    
    # ========================================================================
    # STEP 2: Create song record in database
    # ========================================================================
    
    try:
        # Create new Song instance
        new_song = Song(
            song_name=song_name.strip(),
            artist_name=artist_name.strip(),
            cover_art_url=cover_art_url,  # Cloudinary URL
            linktree=linktree.strip()
        )
        
        # Add to database session
        db.add(new_song)
        
        # Commit transaction (save to database)
        db.commit()
        
        # Refresh to get auto-generated ID and timestamp
        db.refresh(new_song)
        
        # Return the song
        return new_song
        
    except Exception as e:
        # If database operation fails, rollback
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create song: {str(e)}"
        )


# ============================================================================
# EDIT SONG ENDPOINT
# ============================================================================

@router.patch("/admin-edit-song/{song_id}", response_model=SongResponse)
async def edit_song(
    song_id: int,
    
    # Form fields - all optional for editing
    song_name: Optional[str] = Form(None),
    artist_name: Optional[str] = Form(None),
    linktree: Optional[str] = Form(None),
    
    # File upload - optional
    cover_art: Optional[UploadFile] = File(None),
    
    # Dependencies
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """
    Edit an existing song
    
    This endpoint requires authentication (JWT token)
    All fields are optional - only provided fields will be updated
    
    Process:
    1. Find the song in the database
    2. Update text fields if provided
    3. If new cover art provided, delete old one from Cloudinary and upload new one
    4. Save changes to database
    5. Return updated song details
    
    Args:
        song_id: ID of the song to edit
        song_name: New song name (optional)
        artist_name: New artist name (optional)
        linktree: New linktree URL (optional)
        cover_art: New cover art image file (optional)
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Updated song with all details
    
    Raises:
        HTTPException 404 if song not found
        HTTPException 500 if update fails
    """
    
    # ========================================================================
    # STEP 1: Find the song in database
    # ========================================================================
    
    song = db.query(Song).filter(Song.id == song_id).first()
    
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Song with ID {song_id} not found"
        )
    
    # ========================================================================
    # STEP 2: Update text fields if provided
    # ========================================================================
    
    if song_name is not None:
        song.song_name = song_name.strip()
    
    if artist_name is not None:
        song.artist_name = artist_name.strip()
    
    if linktree is not None:
        song.linktree = linktree.strip()
    
    # ========================================================================
    # STEP 3: Handle cover art update
    # ========================================================================
    
    if cover_art is not None:
        # Delete the old cover art from Cloudinary
        old_cover_url = song.cover_art_url
        delete_cloudinary_image(old_cover_url)
        
        # Upload new cover art and get URL
        new_cover_url = upload_song_cover_art(cover_art, song.song_name, song.artist_name)
        song.cover_art_url = new_cover_url
    
    # ========================================================================
    # STEP 4: Save changes to database
    # ========================================================================
    
    try:
        # Commit the changes
        db.commit()
        
        # Refresh to get the latest data
        db.refresh(song)
        
        # Return updated song
        return song
        
    except Exception as e:
        # If something goes wrong, rollback
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update song: {str(e)}"
        )
