"""
Artist management routes
Handles adding artists with image uploads
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.database import get_db
from app.models.user import User
from app.models.artist import Artist
from app.schemas.artist import ArtistResponse
from app.core.dependencies import get_current_user
from app.core.cloudinary_config import upload_artist_banner, upload_artist_image
import json

# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(
    prefix="/artists",
    tags=["Artists"]
)

# ============================================================================
# ADD ARTIST ENDPOINT
# ============================================================================

@router.post("/admin-add-artist", response_model=ArtistResponse, status_code=status.HTTP_201_CREATED)
async def add_artist(
    # Form fields - these come from multipart/form-data
    artist_name: str = Form(...),
    genres: str = Form(...),  # JSON string of array, e.g., '["Hip Hop", "R&B"]'
    spotify_link: Optional[str] = Form(None),
    apple_music_link: Optional[str] = Form(None),
    youtube_link: Optional[str] = Form(None),
    youtube_music_link: Optional[str] = Form(None),
    instagram_link: Optional[str] = Form(None),
    x_link: Optional[str] = Form(None),
    tiktok_link: Optional[str] = Form(None),
    
    # File uploads - these are the actual image files
    banner_image: UploadFile = File(...),
    profile_image: UploadFile = File(...),
    
    # Dependencies
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """
    Add a new artist with banner and profile images
    
    This endpoint requires authentication (JWT token)
    
    Process:
    1. Validate and parse genres from JSON string
    2. Upload banner image to Cloudinary (1200x400, rectangular)
    3. Upload profile image to Cloudinary (800x800, square)
    4. Create artist record in database with image URLs
    5. Return artist details
    
    Args:
        artist_name: Name of the artist
        genres: JSON string array of genres (e.g., '["Hip Hop", "R&B"]')
        spotify_link: Spotify profile URL (optional)
        apple_music_link: Apple Music profile URL (optional)
        youtube_link: YouTube channel URL (optional)
        youtube_music_link: YouTube Music profile URL (optional)
        instagram_link: Instagram profile URL (optional)
        x_link: X (Twitter) profile URL (optional)
        tiktok_link: TikTok profile URL (optional)
        banner_image: Banner image file (jpg/png/webp)
        profile_image: Profile image file (jpg/png/webp)
        db: Database session
        current_user: Authenticated user (from JWT token)
    
    Returns:
        Created artist with all details including image URLs
    
    Raises:
        HTTPException 400 if genres format is invalid
        HTTPException 500 if image upload or database operation fails
    """
    
    # ========================================================================
    # STEP 1: Parse and validate genres
    # ========================================================================
    try:
        # Parse genres from JSON string to Python list
        # Frontend should send: '["Hip Hop", "R&B", "Pop"]'
        genres_list = json.loads(genres)
        
        # Validate that it's actually a list
        if not isinstance(genres_list, list) or len(genres_list) == 0:
            raise ValueError("Genres must be a non-empty array")
        
        # Convert list to comma-separated string for database storage
        # ["Hip Hop", "R&B"] -> "Hip Hop,R&B"
        genres_str = ",".join(genres_list)
        
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid genres format. Must be a JSON array of strings: {str(e)}"
        )
    
    # ========================================================================
    # STEP 2: Upload images to Cloudinary
    # ========================================================================
    
    # Upload banner image (rectangular: 1200x400)
    # This function validates file format and handles the upload
    banner_url = upload_artist_banner(banner_image, artist_name)
    
    # Upload profile image (square: 800x800)
    profile_url = upload_artist_image(profile_image, artist_name)
    
    # ========================================================================
    # STEP 3: Create artist record in database
    # ========================================================================
    
    try:
        # Create new Artist instance with all the data
        new_artist = Artist(
            artist_name=artist_name.strip(),
            banner_image_url=banner_url,  # Cloudinary URL
            image_url=profile_url,  # Cloudinary URL
            genres=genres_str,  # Comma-separated string
            spotify_link=spotify_link.strip() if spotify_link else None,
            apple_music_link=apple_music_link.strip() if apple_music_link else None,
            youtube_link=youtube_link.strip() if youtube_link else None,
            youtube_music_link=youtube_music_link.strip() if youtube_music_link else None,
            instagram_link=instagram_link.strip() if instagram_link else None,
            x_link=x_link.strip() if x_link else None,
            tiktok_link=tiktok_link.strip() if tiktok_link else None
        )
        
        # Add to database session
        db.add(new_artist)
        
        # Commit transaction (save to database)
        db.commit()
        
        # Refresh to get auto-generated ID and timestamp
        db.refresh(new_artist)
        
        # ====================================================================
        # STEP 4: Prepare response
        # ====================================================================
        
        # Convert the Artist model to response format
        # Need to convert genres back from string to list for the response
        artist_response = ArtistResponse(
            id=new_artist.id,
            artist_name=new_artist.artist_name,
            banner_image_url=new_artist.banner_image_url,
            image_url=new_artist.image_url,
            genres=new_artist.genres.split(","),  # Convert back to list
            spotify_link=new_artist.spotify_link,
            apple_music_link=new_artist.apple_music_link,
            youtube_link=new_artist.youtube_link,
            youtube_music_link=new_artist.youtube_music_link,
            instagram_link=new_artist.instagram_link,
            x_link=new_artist.x_link,
            tiktok_link=new_artist.tiktok_link,
            created_at=new_artist.created_at
        )
        
        return artist_response
        
    except Exception as e:
        # If database operation fails, rollback
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create artist: {str(e)}"
        )




# ============================================================================
# EDIT ARTIST ENDPOINT
# ============================================================================

@router.patch("/admin-edit-artist/{artist_id}", response_model=ArtistResponse)
async def edit_artist(
    artist_id: int,
    
    # Form fields - all optional for editing
    artist_name: Optional[str] = Form(None),
    genres: Optional[str] = Form(None),  # JSON string of array
    spotify_link: Optional[str] = Form(None),
    apple_music_link: Optional[str] = Form(None),
    youtube_link: Optional[str] = Form(None),
    youtube_music_link: Optional[str] = Form(None),
    instagram_link: Optional[str] = Form(None),
    x_link: Optional[str] = Form(None),
    tiktok_link: Optional[str] = Form(None),
    
    # File uploads - optional (only upload if user wants to change them)
    banner_image: Optional[UploadFile] = File(None),
    profile_image: Optional[UploadFile] = File(None),
    
    # Dependencies
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """
    Edit an existing artist
    
    This endpoint requires authentication (JWT token)
    All fields are optional - only provided fields will be updated
    
    Process:
    1. Find the artist in the database
    2. Update text fields if provided
    3. If new images provided, delete old ones from Cloudinary and upload new ones
    4. Save changes to database
    5. Return updated artist details
    
    Args:
        artist_id: ID of the artist to edit
        artist_name: New name for the artist (optional)
        genres: New genres as JSON array string (optional)
        spotify_link: New Spotify URL (optional)
        apple_music_link: New Apple Music URL (optional)
        youtube_link: New YouTube URL (optional)
        youtube_music_link: New YouTube Music URL (optional)
        instagram_link: New Instagram URL (optional)
        x_link: New X (Twitter) URL (optional)
        tiktok_link: New TikTok URL (optional)
        banner_image: New banner image file (optional)
        profile_image: New profile image file (optional)
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Updated artist with all details
    
    Raises:
        HTTPException 404 if artist not found
        HTTPException 400 if genres format is invalid
        HTTPException 500 if update fails
    """
    
    # ========================================================================
    # STEP 1: Find the artist in database
    # ========================================================================
    
    # Query the database for the artist with this ID
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist with ID {artist_id} not found"
        )
    
    # ========================================================================
    # STEP 2: Update text fields if provided
    # ========================================================================
    
    # Update artist name if provided
    if artist_name is not None:
        artist.artist_name = artist_name.strip()
    
    # Update genres if provided
    if genres is not None:
        try:
            # Parse genres from JSON string to Python list
            genres_list = json.loads(genres)
            
            # Validate that it's a list
            if not isinstance(genres_list, list) or len(genres_list) == 0:
                raise ValueError("Genres must be a non-empty array")
            
            # Convert to comma-separated string
            artist.genres = ",".join(genres_list)
            
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid genres format. Must be a JSON array of strings: {str(e)}"
            )
    
    # Update social media links if provided
    # Using 'is not None' because empty string ("") should clear the link
    if spotify_link is not None:
        artist.spotify_link = spotify_link.strip() if spotify_link else None
    
    if apple_music_link is not None:
        artist.apple_music_link = apple_music_link.strip() if apple_music_link else None
    
    if youtube_link is not None:
        artist.youtube_link = youtube_link.strip() if youtube_link else None
    
    if youtube_music_link is not None:
        artist.youtube_music_link = youtube_music_link.strip() if youtube_music_link else None
    
    if instagram_link is not None:
        artist.instagram_link = instagram_link.strip() if instagram_link else None
    
    if x_link is not None:
        artist.x_link = x_link.strip() if x_link else None
    
    if tiktok_link is not None:
        artist.tiktok_link = tiktok_link.strip() if tiktok_link else None
    
    # ========================================================================
    # STEP 3: Handle image updates
    # ========================================================================
    
    # Import the delete function
    from core.cloudinary_config import delete_cloudinary_image
    
    # Update banner image if new one is provided
    if banner_image is not None:
        # Delete the old banner from Cloudinary
        old_banner_url = artist.banner_image_url
        delete_cloudinary_image(old_banner_url)
        
        # Upload new banner and get URL
        new_banner_url = upload_artist_banner(banner_image, artist.artist_name)
        artist.banner_image_url = new_banner_url
    
    # Update profile image if new one is provided
    if profile_image is not None:
        # Delete the old profile image from Cloudinary
        old_profile_url = artist.image_url
        delete_cloudinary_image(old_profile_url)
        
        # Upload new profile image and get URL
        new_profile_url = upload_artist_image(profile_image, artist.artist_name)
        artist.image_url = new_profile_url
    
    # ========================================================================
    # STEP 4: Save changes to database
    # ========================================================================
    
    try:
        # Commit the changes
        # SQLAlchemy tracks changes to the artist object automatically
        db.commit()
        
        # Refresh to get the latest data
        db.refresh(artist)
        
        # ====================================================================
        # STEP 5: Prepare and return response
        # ====================================================================
        
        artist_response = ArtistResponse(
            id=artist.id,
            artist_name=artist.artist_name,
            banner_image_url=artist.banner_image_url,
            image_url=artist.image_url,
            genres=artist.genres.split(","),  # Convert back to list
            spotify_link=artist.spotify_link,
            apple_music_link=artist.apple_music_link,
            youtube_link=artist.youtube_link,
            youtube_music_link=artist.youtube_music_link,
            instagram_link=artist.instagram_link,
            x_link=artist.x_link,
            tiktok_link=artist.tiktok_link,
            created_at=artist.created_at
        )
        
        return artist_response
        
    except Exception as e:
        # If something goes wrong, rollback
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update artist: {str(e)}"
        )
