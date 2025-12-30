"""
Song management routes
Handles adding and editing songs with cover art uploads
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional,List
import json
from app.models.database import get_db
from app.models.user import User
from app.models.song import Song
from app.schemas.song import SongResponse, SongCreate
from app.core.dependencies import get_current_user
from app.core.cloudinary_config import upload_song_cover_art, delete_cloudinary_image
from sqlalchemy import func

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
@router.post(
    "/admin-add-song",
    response_model=list[SongResponse],
    status_code=status.HTTP_201_CREATED
)
async def add_song(
    songs: str = Form(...),
    cover_arts: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    """
    Add multiple songs with cover arts in a single request
    
    This endpoint requires authentication (JWT token)
    All songs are added in a single transaction - if any fails, none are added
    
    If artist_id is provided, it will be verified against the artists table
    If artist_id is not provided, artist_name will be stored as a string (for features)
    
    Process:
    1. Parse songs JSON array
    2. Validate that number of songs matches number of cover arts
    3. Verify artist_id exists if provided
    4. Upload all cover arts to Cloudinary
    5. Create all song records in database
    6. Return all created songs (or rollback if any step fails)
    
    Args:
        songs: JSON string array of song objects, each with:
               - song_name: Name of the song
               - artist_name: Name of the artist (always required for display)
               - linktree: URL to the song's linktree page
               - artist_id: Optional ID of artist in database (for linking)
        cover_arts: List of cover art image files (jpg/png/webp)
        db: Database session
        current_user: Authenticated user (from JWT token)
    
    Returns:
        List of all created songs with details including cover art URLs
    
    Raises:
        HTTPException 400 if songs format is invalid, counts don't match, or artist_id invalid
        HTTPException 500 if upload or database operation fails (all changes rolled back)
    """
    
    # Import Artist model for validation
    from app.models.artist import Artist
    
    # ========================================================================
    # STEP 1: Parse and validate songs JSON
    # ========================================================================
    
    try:
        raw_songs = json.loads(songs)

        if not isinstance(raw_songs, list) or not raw_songs:
            raise ValueError("Songs must be a non-empty array")

        songs_list: list[SongCreate] = []

        for idx, song_data in enumerate(raw_songs):
            try:
                song_obj = SongCreate(**song_data)
                songs_list.append(song_obj)
            except ValidationError as e:
                raise ValueError(f"Song at index {idx}: {e}")

    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid songs format: {str(e)}"
        )

    
    # ========================================================================
    # STEP 2: Validate cover arts count matches songs count
    # ========================================================================
    
    if len(cover_arts) != len(songs_list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Number of cover arts ({len(cover_arts)}) must match number of songs ({len(songs_list)})"
        )
    
    # ========================================================================
    # STEP 3: Verify all artist_id values exist
    # ========================================================================
    
    for idx, song_data in enumerate(songs_list):
        artist_id = song.artist_id
        
        # Verify the artist exists in the database
        artist = db.query(Artist).filter(Artist.id == artist_id).first()
        if not artist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Song at index {idx}: Artist with ID {artist_id} not found"
            )
    
    # ========================================================================
    # STEP 4: Upload all cover arts to Cloudinary
    # ========================================================================
    
    uploaded_cover_urls = []
    
    try:
        for idx, (song_data, cover_art) in enumerate(zip(songs_list, cover_arts)):
            cover_url = upload_song_cover_art(
                cover_art,
                song.song_name,
                song.artist_name
            )
            uploaded_cover_urls.append(cover_url)
        
    except Exception as e:
        for url in uploaded_cover_urls:
            delete_cloudinary_image(url)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload cover arts: {str(e)}. All uploads have been rolled back."
        )
    
    # ========================================================================
    # STEP 5: Create all song records in database (transaction)
    # ========================================================================
    
    created_songs = []
    
    try:
        for song_data, cover_url in zip(songs_list, uploaded_cover_urls):
            new_song = Song(
                song_name=song.song_name,
                artist_name=song.artist_name,
                artist_id=song.artist_id,  # Now required
                cover_art_url=cover_url,
                linktree=song.linktree.strip()
            )
            db.add(new_song)
            created_songs.append(new_song)
        
        # Commit to get song IDs
        db.commit()
        
        # Refresh all songs to get their IDs
        for song in created_songs:
            db.refresh(song)
        
        # ====================================================================
        # STEP 6: Auto-create order entries for each song
        # ====================================================================
        
        for song in created_songs:
            # Get the current max position for this artist
            max_position = db.query(func.max(ArtistSongOrder.display_order)).filter(
                ArtistSongOrder.artist_id == song.artist_id
            ).scalar()
            
            # If no songs exist yet, start at 1, otherwise increment
            next_position = 1 if max_position is None else max_position + 1
            
            # Create order entry
            order_entry = ArtistSongOrder(
                artist_id=song.artist_id,
                song_id=song.id,
                display_order=next_position
            )
            db.add(order_entry)
        
        # Commit order entries
        db.commit()
        
        return created_songs
        
    except Exception as e:
        db.rollback()
        
        # Delete all uploaded cover arts from Cloudinary
        for url in uploaded_cover_urls:
            delete_cloudinary_image(url)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create songs: {str(e)}. All changes have been rolled back."
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
    artist_id: Optional[int] = Form(None),  # NEW: Optional artist_id field
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
    
    If artist_id is provided, it will be verified against the artists table
    
    Process:
    1. Find the song in the database
    2. Verify artist_id if provided
    3. Update text fields if provided
    4. If new cover art provided, delete old one from Cloudinary and upload new one
    5. Save changes to database
    6. Return updated song details
    
    Args:
        song_id: ID of the song to edit
        song_name: New song name (optional)
        artist_name: New artist name (optional)
        artist_id: New artist ID to link (optional, set to -1 to remove link)
        linktree: New linktree URL (optional)
        cover_art: New cover art image file (optional)
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Updated song with all details
    
    Raises:
        HTTPException 404 if song not found
        HTTPException 400 if artist_id is invalid
        HTTPException 500 if update fails
    """
    
    # Import Artist model for validation
    from models.artist import Artist
    
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
    # STEP 2: Verify artist_id if provided
    # ========================================================================
    
    if artist_id is not None:
        if artist_id == -1:
            # Special value to remove artist link
            song.artist_id = None
        else:
            # Verify the artist exists in the database
            artist = db.query(Artist).filter(Artist.id == artist_id).first()
            if not artist:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Artist with ID {artist_id} not found"
                )
            song.artist_id = artist_id
    
    # ========================================================================
    # STEP 3: Update text fields if provided
    # ========================================================================
    
    if song_name is not None:
        song.song_name = song_name.strip()
    
    if artist_name is not None:
        song.artist_name = artist_name.strip()
    
    if linktree is not None:
        song.linktree = linktree.strip()
    
    # ========================================================================
    # STEP 4: Handle cover art update
    # ========================================================================
    
    if cover_art is not None:
        # Delete the old cover art from Cloudinary
        old_cover_url = song.cover_art_url
        delete_cloudinary_image(old_cover_url)
        
        # Upload new cover art and get URL
        new_cover_url = upload_song_cover_art(cover_art, song.song_name, song.artist_name)
        song.cover_art_url = new_cover_url
    
    # ========================================================================
    # STEP 5: Save changes to database
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


@router.delete("/admin-delete-song/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_song(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a song
    
    This endpoint requires authentication (JWT token)
    
    Deletes:
    - Song record from database
    - Song cover art from Cloudinary
    
    Args:
        song_id: ID of the song to delete
        db: Database session
        current_user: Authenticated user (requires auth)
    
    Returns:
        204 No Content on success
    
    Raises:
        HTTPException 404 if song not found
        HTTPException 500 if deletion fails
    """
    
    from core.cloudinary_config import delete_cloudinary_image
    
    # Find the song
    song = db.query(Song).filter(Song.id == song_id).first()
    
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Song with ID {song_id} not found"
        )
    
    # Delete cover art from Cloudinary
    delete_cloudinary_image(song.cover_art_url)
    
    # Delete song from database
    try:
        db.delete(song)
        db.commit()
        
        return None
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete song: {str(e)}"
        )