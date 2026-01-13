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

from app.schemas.artist import ArtistListResponse, ArtistDetailResponse, ArtistWithSongsResponse, PaginationMeta, ReorderRequest, ItemOrder, ItemOrder
from app.models.song import Song
from app.models.video import Video
from sqlalchemy import or_
import math

from typing import List
from app.schemas.song import SongResponse, SongWithOrderResponse
from app.schemas.video import VideoResponse, VideoWithOrderResponse


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
    from app.core.cloudinary_config import delete_cloudinary_image
    
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




@router.get("/", response_model=ArtistListResponse)
def get_all_artists(
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get all artists with pagination
    
    Returns paginated list of artists with their songs
    Songs are matched by artist_id (if linked) OR by artist_name (string match)
    
    Args:
        page: Page number (default: 1)
        per_page: Items per page (default: 50)
        db: Database session
    
    Returns:
        Paginated artist list with metadata
        
    Response structure:
        {
            "data": [
                {
                    "id": 1,
                    "artist_name": "Drake",
                    "banner_image_url": "...",
                    "image_url": "...",
                    "genres": ["Hip Hop", "R&B"],
                    "spotify_link": "...",
                    ...
                    "songs": [
                        {
                            "id": 1,
                            "song_name": "God's Plan",
                            "artist_name": "Drake",
                            "artist_id": 1,
                            "cover_art_url": "...",
                            ...
                        }
                    ]
                }
            ],
            "meta": {
                "total": 100,
                "page": 1,
                "per_page": 50,
                "total_pages": 2
            }
        }
    """
    
    # ========================================================================
    # STEP 1: Get total count for pagination
    # ========================================================================
    
    total_artists = db.query(Artist).count()
    total_pages = math.ceil(total_artists / per_page)
    
    # Validate page number
    if page < 1:
        page = 1
    
    # ========================================================================
    # STEP 2: Get paginated artists
    # ========================================================================
    
    offset = (page - 1) * per_page
    artists = db.query(Artist).offset(offset).limit(per_page).all()
    
    # ========================================================================
    # STEP 3: For each artist, fetch their songs
    # ========================================================================
    
    artists_with_songs = []
    
    for artist in artists:
        # Find songs that are linked to this artist by artist_id
        # OR match by artist_name (for old data or features)
        songs = db.query(Song).filter(
            or_(
                Song.artist_id == artist.id,
                Song.artist_name == artist.artist_name
            )
        ).all()
        
        # Build artist response with songs
        artist_data = ArtistWithSongsResponse(
            id=artist.id,
            artist_name=artist.artist_name,
            banner_image_url=artist.banner_image_url,
            image_url=artist.image_url,
            genres=artist.genres.split(","),
            spotify_link=artist.spotify_link,
            apple_music_link=artist.apple_music_link,
            youtube_link=artist.youtube_link,
            youtube_music_link=artist.youtube_music_link,
            instagram_link=artist.instagram_link,
            x_link=artist.x_link,
            tiktok_link=artist.tiktok_link,
            created_at=artist.created_at,
            songs=songs
        )
        
        artists_with_songs.append(artist_data)
    
    # ========================================================================
    # STEP 4: Build response with pagination metadata
    # ========================================================================
    
    return ArtistListResponse(
        data=artists_with_songs,
        meta=PaginationMeta(
            total=total_artists,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
    )


# ============================================================================
# FETCH SINGLE ARTIST WITH ALL DETAILS
# ============================================================================

@router.get("/{artist_id}", response_model=ArtistDetailResponse)
def get_artist_by_id(
    artist_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single artist with all their songs and videos (ORDERED)
    
    Returns complete artist profile including:
    - Artist information (banner, image, genres, social links)
    - All songs linked to this artist (ordered by display_order)
    - All videos linked to this artist (ordered by display_order)
    
    Songs and videos are returned in their custom order as set by admin
    
    Args:
        artist_id: ID of the artist
        db: Database session
    
    Returns:
        Complete artist profile with ordered songs and videos
    
    Raises:
        HTTPException 404 if artist not found
    """
    
    from app.models.artist_song_order import ArtistSongOrder
    from app.models.artist_video_order import ArtistVideoOrder
    
    # ========================================================================
    # STEP 1: Find the artist
    # ========================================================================
    
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist with ID {artist_id} not found"
        )
    
    # ========================================================================
    # STEP 2: Fetch all songs by this artist WITH ordering
    # ========================================================================
    
    # Join Song with ArtistSongOrder to get display_order
    # Only fetch songs linked to this artist by artist_id
    songs_query = db.query(
        Song,
        ArtistSongOrder.display_order
    ).outerjoin(
        ArtistSongOrder,
        (Song.id == ArtistSongOrder.song_id) & (ArtistSongOrder.artist_id == artist_id)
    ).filter(
        Song.artist_id == artist_id
    ).order_by(
        ArtistSongOrder.display_order.asc()
    ).all()
    
    # Build song response objects with display_order
    songs = []
    for song, display_order in songs_query:
        song_data = SongWithOrderResponse(
            id=song.id,
            song_name=song.song_name,
            artist_name=song.artist_name,
            artist_id=song.artist_id,
            cover_art_url=song.cover_art_url,
            linktree=song.linktree,
            created_at=song.created_at,
            display_order=display_order
        )
        songs.append(song_data)
    
    # ========================================================================
    # STEP 3: Fetch all videos by this artist WITH ordering
    # ========================================================================
    
    # Join Video with ArtistVideoOrder to get display_order
    # Only fetch videos linked to this artist by artist_id
    videos_query = db.query(
        Video,
        ArtistVideoOrder.display_order
    ).outerjoin(
        ArtistVideoOrder,
        (Video.id == ArtistVideoOrder.video_id) & (ArtistVideoOrder.artist_id == artist_id)
    ).filter(
        Video.artist_id == artist_id
    ).order_by(
        ArtistVideoOrder.display_order.asc()
    ).all()
    
    # Build video response objects with display_order
    videos = []
    for video, display_order in videos_query:
        video_data = VideoWithOrderResponse(
            id=video.id,
            video_name=video.video_name,
            video_link=video.video_link,
            artist_name=video.artist_name,
            artist_id=video.artist_id,
            thumbnail_url=video.thumbnail_url,
            created_at=video.created_at,
            display_order=display_order
        )
        videos.append(video_data)
    
    # ========================================================================
    # STEP 4: Build complete artist response
    # ========================================================================
    
    return ArtistDetailResponse(
        id=artist.id,
        artist_name=artist.artist_name,
        banner_image_url=artist.banner_image_url,
        image_url=artist.image_url,
        genres=artist.genres.split(","),
        spotify_link=artist.spotify_link,
        apple_music_link=artist.apple_music_link,
        youtube_link=artist.youtube_link,
        youtube_music_link=artist.youtube_music_link,
        instagram_link=artist.instagram_link,
        x_link=artist.x_link,
        tiktok_link=artist.tiktok_link,
        created_at=artist.created_at,
        songs=songs,
        videos=videos
    )



@router.delete("/admin-delete-artist/{artist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artist(
    artist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an artist and all related content
    
    This endpoint requires authentication (JWT token)
    
    Deletes:
    - Artist record from database
    - Artist banner and profile images from Cloudinary
    - All songs linked to this artist (by artist_id)
    - All song cover arts from Cloudinary
    - All videos linked to this artist (by artist_id)
    
    Does NOT delete:
    - Songs/videos that only match by artist_name string (no artist_id link)
    
    Process:
    1. Find the artist
    2. Find all songs with this artist_id
    3. Delete all song cover arts from Cloudinary
    4. Delete all songs from database
    5. Find all videos with this artist_id
    6. Delete all videos from database
    7. Delete artist images from Cloudinary
    8. Delete artist from database
    
    Args:
        artist_id: ID of the artist to delete
        db: Database session
        current_user: Authenticated user (requires auth)
    
    Returns:
        204 No Content on success
    
    Raises:
        HTTPException 404 if artist not found
        HTTPException 500 if deletion fails
    """
    
    from app.models.song import Song
    from app.models.video import Video
    from app.core.cloudinary_config import delete_cloudinary_image
    
    # ========================================================================
    # STEP 1: Find the artist
    # ========================================================================
    
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist with ID {artist_id} not found"
        )
    
    # ========================================================================
    # STEP 2: Delete all songs linked to this artist
    # ========================================================================
    
    # Find all songs with this artist_id (not just matching name)
    songs = db.query(Song).filter(Song.artist_id == artist_id).all()
    
    # Delete all song cover arts from Cloudinary
    for song in songs:
        delete_cloudinary_image(song.cover_art_url)
    
    # Delete all songs from database
    db.query(Song).filter(Song.artist_id == artist_id).delete()
    
    # ========================================================================
    # STEP 3: Delete all videos linked to this artist
    # ========================================================================
    
    # Find all videos with this artist_id (not just matching name)
    # No need to delete thumbnails as they're YouTube URLs, not uploaded
    db.query(Video).filter(Video.artist_id == artist_id).delete()
    
    # ========================================================================
    # STEP 4: Delete artist images from Cloudinary
    # ========================================================================
    
    # Delete banner image
    delete_cloudinary_image(artist.banner_image_url)
    
    # Delete profile image
    delete_cloudinary_image(artist.image_url)
    
    # ========================================================================
    # STEP 5: Delete artist from database
    # ========================================================================
    
    try:
        db.delete(artist)
        db.commit()
        
        # Return 204 No Content (no response body)
        return None
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete artist: {str(e)}"
        )


@router.get("/{artist_id}/songs", response_model=List[SongResponse])
def get_artist_songs(
    artist_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all songs by a specific artist
    
    Returns all songs that are either:
    - Linked to this artist by artist_id
    - Match this artist's name by artist_name string
    
    Args:
        artist_id: ID of the artist
        db: Database session
    
    Returns:
        List of all songs by this artist
    
    Raises:
        HTTPException 404 if artist not found
    """
    
    from app.models.song import Song
    from sqlalchemy import or_
    
    # ========================================================================
    # STEP 1: Verify artist exists
    # ========================================================================
    
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist with ID {artist_id} not found"
        )
    
    # ========================================================================
    # STEP 2: Fetch all songs
    # ========================================================================
    
    # Find songs that are linked to this artist by artist_id
    # OR match by artist_name (for old data or features)
    songs = db.query(Song).filter(
        or_(
            Song.artist_id == artist.id,
            Song.artist_name == artist.artist_name
        )
    ).all()
    
    return songs


@router.get("/{artist_id}/videos", response_model=List[VideoResponse])
def get_artist_videos(
    artist_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all videos by a specific artist
    
    Returns all videos that are either:
    - Linked to this artist by artist_id
    - Match this artist's name by artist_name string
    
    Args:
        artist_id: ID of the artist
        db: Database session
    
    Returns:
        List of all videos by this artist
    
    Raises:
        HTTPException 404 if artist not found
    """
    
    from app.models.video import Video
    from sqlalchemy import or_
    
    # ========================================================================
    # STEP 1: Verify artist exists
    # ========================================================================
    
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist with ID {artist_id} not found"
        )
    
    # ========================================================================
    # STEP 2: Fetch all videos
    # ========================================================================
    
    # Find videos that are linked to this artist by artist_id
    # OR match by artist_name (for old data or features)
    videos = db.query(Video).filter(
        or_(
            Video.artist_id == artist.id,
            Video.artist_name == artist.artist_name
        )
    ).all()
    
    return videos




@router.patch("/{artist_id}/admin-reorder-songs", status_code=status.HTTP_200_OK)
def reorder_artist_songs(
    artist_id: int,
    reorder_data: ReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reorder songs for a specific artist
    
    This endpoint requires authentication (JWT token)
    
    Updates the display_order for multiple songs at once
    
    Args:
        artist_id: ID of the artist
        reorder_data: List of song_id and position pairs
        db: Database session
        current_user: Authenticated user (requires auth)
    
    Request body example:
    {
        "items": [
            {"id": 45, "position": 1},
            {"id": 23, "position": 2},
            {"id": 67, "position": 3}
        ]
    }
    
    Returns:
        Success message
    
    Raises:
        HTTPException 404 if artist not found
        HTTPException 400 if song doesn't belong to this artist
        HTTPException 500 if update fails
    """
    
    from app.models.artist_song_order import ArtistSongOrder
    
    # Verify artist exists
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist with ID {artist_id} not found"
        )
    
    # Verify all songs belong to this artist
    for item in reorder_data.items:
        song = db.query(Song).filter(
            Song.id == item.id,
            Song.artist_id == artist_id
        ).first()
        
        if not song:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Song with ID {item.id} not found or doesn't belong to artist {artist_id}"
            )
    
    try:
        # Update all positions
        for item in reorder_data.items:
            # Find existing order entry
            order_entry = db.query(ArtistSongOrder).filter(
                ArtistSongOrder.artist_id == artist_id,
                ArtistSongOrder.song_id == item.id
            ).first()
            
            if order_entry:
                # Update existing entry
                order_entry.display_order = item.position
            else:
                # Create new entry (shouldn't happen but handle it)
                new_entry = ArtistSongOrder(
                    artist_id=artist_id,
                    song_id=item.id,
                    display_order=item.position
                )
                db.add(new_entry)
        
        db.commit()
        
        return {"message": f"Successfully reordered {len(reorder_data.items)} songs"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder songs: {str(e)}"
        )


@router.patch("/{artist_id}/admin-reorder-videos", status_code=status.HTTP_200_OK)
def reorder_artist_videos(
    artist_id: int,
    reorder_data: ReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reorder videos for a specific artist
    
    This endpoint requires authentication (JWT token)
    
    Updates the display_order for multiple videos at once
    
    Args:
        artist_id: ID of the artist
        reorder_data: List of video_id and position pairs
        db: Database session
        current_user: Authenticated user (requires auth)
    
    Request body example:
    {
        "items": [
            {"id": 12, "position": 1},
            {"id": 34, "position": 2},
            {"id": 56, "position": 3}
        ]
    }
    
    Returns:
        Success message
    
    Raises:
        HTTPException 404 if artist not found
        HTTPException 400 if video doesn't belong to this artist
        HTTPException 500 if update fails
    """
    
    from app.models.artist_video_order import ArtistVideoOrder
    
    # Verify artist exists
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist with ID {artist_id} not found"
        )
    
    # Verify all videos belong to this artist
    for item in reorder_data.items:
        video = db.query(Video).filter(
            Video.id == item.id,
            Video.artist_id == artist_id
        ).first()
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Video with ID {item.id} not found or doesn't belong to artist {artist_id}"
            )
    
    try:
        # Update all positions
        for item in reorder_data.items:
            # Find existing order entry
            order_entry = db.query(ArtistVideoOrder).filter(
                ArtistVideoOrder.artist_id == artist_id,
                ArtistVideoOrder.video_id == item.id
            ).first()
            
            if order_entry:
                # Update existing entry
                order_entry.display_order = item.position
            else:
                # Create new entry (shouldn't happen but handle it)
                new_entry = ArtistVideoOrder(
                    artist_id=artist_id,
                    video_id=item.id,
                    display_order=item.position
                )
                db.add(new_entry)
        
        db.commit()
        
        return {"message": f"Successfully reordered {len(reorder_data.items)} videos"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder videos: {str(e)}"
        )