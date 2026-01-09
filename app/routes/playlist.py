# routes/playlist.py
"""
Playlist routes
Handles playlist creation, editing, deletion, and retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.database import get_db
from app.models.user import User
from app.models.playlist import Playlist
from app.schemas.playlist import PlaylistResponse
from app.core.dependencies import get_current_user
from app.core.cloudinary_config import upload_playlist_cover_art, delete_cloudinary_image

# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(
    prefix="/playlists",
    tags=["Playlists"]
)

# ============================================================================
# CREATE PLAYLIST (REQUIRES AUTH)
# ============================================================================

@router.post("/admin-add", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
async def create_playlist(
    # Form fields
    playlist_name: str = Form(...),
    linktree: str = Form(...),
    
    # File upload
    cover_art: UploadFile = File(...),
    
    # Dependencies
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """
    Create a new playlist
    
    This endpoint requires authentication (JWT token)
    
    Process:
    1. Upload cover art to Cloudinary (any size accepted)
    2. Create playlist record in database
    3. Return playlist details
    
    Args:
        playlist_name: Name of the playlist (required)
        linktree: URL to the playlist's linktree page (required)
        cover_art: Cover art image file (jpg/png/webp, any size)
        db: Database session
        current_user: Authenticated user (from JWT token)
    
    Returns:
        Created playlist with all details including cover art URL
    
    Raises:
        HTTPException 500 if upload or database operation fails
    """
    
    # Upload cover art to Cloudinary (accepts any size)
    cover_art_url = upload_playlist_cover_art(cover_art, playlist_name)
    
    try:
        # Create new Playlist instance
        new_playlist = Playlist(
            playlist_name=playlist_name.strip(),
            cover_art_url=cover_art_url,
            linktree=linktree.strip()
        )
        
        # Add to database session
        db.add(new_playlist)
        
        # Commit transaction (save to database)
        db.commit()
        
        # Refresh to get auto-generated ID and timestamp
        db.refresh(new_playlist)
        
        return new_playlist
        
    except Exception as e:
        # If database operation fails, rollback and delete uploaded image
        db.rollback()
        delete_cloudinary_image(cover_art_url)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create playlist: {str(e)}"
        )


# ============================================================================
# EDIT PLAYLIST (REQUIRES AUTH)
# ============================================================================

@router.patch("/admin-edit/{playlist_id}", response_model=PlaylistResponse)
async def edit_playlist(
    playlist_id: int,
    
    # Form fields - all optional
    playlist_name: Optional[str] = Form(None),
    linktree: Optional[str] = Form(None),
    
    # File upload - optional
    cover_art: Optional[UploadFile] = File(None),
    
    # Dependencies
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """
    Edit an existing playlist
    
    This endpoint requires authentication (JWT token)
    All fields are optional - only provided fields will be updated
    
    Process:
    1. Find the playlist in the database
    2. Update fields if provided
    3. If new cover art provided, delete old one and upload new one
    4. Save changes to database
    5. Return updated playlist details
    
    Args:
        playlist_id: ID of the playlist to edit
        playlist_name: New playlist name (optional)
        linktree: New linktree URL (optional)
        cover_art: New cover art image file (optional)
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Updated playlist with all details
    
    Raises:
        HTTPException 404 if playlist not found
        HTTPException 500 if update fails
    """
    
    # Find the playlist
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist with ID {playlist_id} not found"
        )
    
    # Update playlist name if provided
    if playlist_name is not None:
        playlist.playlist_name = playlist_name.strip()
    
    # Update linktree if provided
    if linktree is not None:
        playlist.linktree = linktree.strip()
    
    # Update cover art if provided
    if cover_art is not None:
        # Delete old cover art from Cloudinary
        old_cover_url = playlist.cover_art_url
        delete_cloudinary_image(old_cover_url)
        
        # Upload new cover art
        new_cover_url = upload_playlist_cover_art(cover_art, playlist.playlist_name)
        playlist.cover_art_url = new_cover_url
    
    # Save changes to database
    try:
        db.commit()
        db.refresh(playlist)
        
        return playlist
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update playlist: {str(e)}"
        )


# ============================================================================
# DELETE PLAYLIST (REQUIRES AUTH)
# ============================================================================

@router.delete("/admin-delete/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """
    Delete a playlist
    
    This endpoint requires authentication (JWT token)
    
    Deletes:
    - Playlist record from database
    - Playlist cover art from Cloudinary
    
    Args:
        playlist_id: ID of the playlist to delete
        db: Database session
        current_user: Authenticated user (requires auth)
    
    Returns:
        204 No Content on success
    
    Raises:
        HTTPException 404 if playlist not found
        HTTPException 500 if deletion fails
    """
    
    # Find the playlist
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist with ID {playlist_id} not found"
        )
    
    # Delete cover art from Cloudinary
    delete_cloudinary_image(playlist.cover_art_url)
    
    # Delete playlist from database
    try:
        db.delete(playlist)
        db.commit()
        
        return None
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete playlist: {str(e)}"
        )


# ============================================================================
# GET ALL PLAYLISTS (PUBLIC)
# ============================================================================

@router.get("/", response_model=List[PlaylistResponse])
def get_all_playlists(db: Session = Depends(get_db)):
    """
    Get all playlists (PUBLIC - no authentication required)
    
    Returns all playlists ordered by newest first
    
    Args:
        db: Database session
    
    Returns:
        List of all playlists
    """
    
    playlists = db.query(Playlist).order_by(Playlist.created_at.desc()).all()
    return playlists


# ============================================================================
# GET SINGLE PLAYLIST (PUBLIC)
# ============================================================================

@router.get("/{playlist_id}", response_model=PlaylistResponse)
def get_playlist_by_id(
    playlist_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single playlist by ID (PUBLIC - no authentication required)
    
    Args:
        playlist_id: ID of the playlist
        db: Database session
    
    Returns:
        Playlist details
    
    Raises:
        HTTPException 404 if playlist not found
    """
    
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist with ID {playlist_id} not found"
        )
    
    return playlist


# ============================================================================
# ============================================================================
# ============================================================================
