# routes/video.py
"""
Video management routes
Handles adding and editing videos with automatic YouTube thumbnail extraction
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.database import get_db
from app.models.user import User
from app.models.video import Video
from app.schemas.video import VideoResponse, VideoCreate
from app.core.dependencies import get_current_user
from app.core.cloudinary_config import get_youtube_thumbnail_url
from sqlalchemy import func

from app.models.database import get_db
from app.models.video import Video
from app.models.artist_video_order import ArtistVideoOrder  # Make sure ArtistVideoOrder is imported
from app.schemas.video import VideoCreate, VideoResponse
from app.models.user import User


import json

# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(
    prefix="/videos",
    tags=["Videos"]
)

# ============================================================================
# ADD MULTIPLE VIDEOS ENDPOINT
# ============================================================================

@router.post("/admin-add-video", response_model=List[VideoResponse], status_code=status.HTTP_201_CREATED)
async def add_videos(
    videos: str = Form(..., description="JSON array of video objects"),  # Changed from VideoCreate
    
    # Dependencies
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add multiple videos in a single request
    
    This endpoint requires authentication (JWT token)
    All videos are added in a single transaction - if any fails, none are added
    
    For YouTube videos, thumbnails are automatically extracted from the video URL
    For non-YouTube videos, thumbnail_url will be null
    
    If artist_id is provided, it will be verified against the artists table
    
    **videos parameter format (JSON string):**
```json
    [
        {
            "video_name": "Video Title 1",
            "video_link": "https://youtube.com/watch?v=...",
            "artist_name": "Artist Name 1",
            "artist_id": 1
        },
        {
            "video_name": "Video Title 2",
            "video_link": "https://youtube.com/watch?v=...",
            "artist_name": "Artist Name 2",
            "artist_id": 2
        }
    ]
```
    
    Process:
    1. Parse videos JSON array
    2. Verify artist_id exists if provided
    3. Extract YouTube thumbnails for each video (if applicable)
    4. Create all video records in database
    5. Return all created videos
    
    Args:
        videos: JSON string array of video objects, each with:
               - video_name: Name of the video
               - video_link: URL to the video (YouTube or other platform)
               - artist_name: Name of the artist (always required for display)
               - artist_id: ID of artist in database
        db: Database session
        current_user: Authenticated user (from JWT token)
    
    Returns:
        List of all created videos with details including thumbnail URLs
    
    Raises:
        HTTPException 400 if videos format is invalid or artist_id invalid
        HTTPException 500 if database operation fails (all changes rolled back)
    """
    
    # Import Artist model for validation
    from app.models.artist import Artist
    
    # ========================================================================
    # STEP 1: Parse and validate videos JSON
    # ========================================================================
    
    try:
        videos_list = json.loads(videos)  # Changed from 'video' to 'videos'
        
        if not isinstance(videos_list, list) or len(videos_list) == 0:
            raise ValueError("Videos must be a non-empty array")
        
        for idx, video_data in enumerate(videos_list):  # Changed variable name
            if not isinstance(video_data, dict):
                raise ValueError(f"Video at index {idx} must be an object")
            
            # Check required fields including artist_id
            required_fields = ["video_name", "video_link", "artist_name", "artist_id"]
            for field in required_fields:
                if field not in video_data or not video_data[field]:
                    raise ValueError(f"Video at index {idx} missing required field: {field}")
            
            # Validate artist_id is a positive integer
            if not isinstance(video_data["artist_id"], int) or video_data["artist_id"] <= 0:
                raise ValueError(f"Video at index {idx}: artist_id must be a positive integer")
        
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid videos format: {str(e)}"
        )
    
    # ========================================================================
    # STEP 2: Verify all artist_id values exist
    # ========================================================================
    
    for idx, video_data in enumerate(videos_list):
        artist_id = video_data["artist_id"]
        
        # Verify the artist exists in the database
        artist = db.query(Artist).filter(Artist.id == artist_id).first()
        if not artist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Video at index {idx}: Artist with ID {artist_id} not found"
            )
    
    # ========================================================================
    # STEP 3: Extract YouTube thumbnails for each video
    # ========================================================================
    
    videos_with_thumbnails = []
    for video_data in videos_list:
        video_link = video_data["video_link"].strip()
        thumbnail_url = get_youtube_thumbnail_url(video_link)
        
        videos_with_thumbnails.append({
            "video_name": video_data["video_name"].strip(),
            "video_link": video_link,
            "artist_name": video_data["artist_name"].strip(),
            "artist_id": video_data["artist_id"],
            "thumbnail_url": thumbnail_url
        })
    
    # ========================================================================
    # STEP 4: Create all video records in database (transaction)
    # ========================================================================
    
    created_videos = []
    
    try:
        for video_data in videos_with_thumbnails:
            new_video = Video(
                video_name=video_data["video_name"],
                video_link=video_data["video_link"],
                artist_name=video_data["artist_name"],
                artist_id=video_data["artist_id"],
                thumbnail_url=video_data["thumbnail_url"]
            )
            db.add(new_video)
            created_videos.append(new_video)
        
        # Commit to get video IDs
        db.commit()
        
        # Refresh all videos to get their IDs
        for video in created_videos:
            db.refresh(video)
        
        # ====================================================================
        # STEP 5: Auto-create order entries for each video
        # ====================================================================
        
        for video in created_videos:
            # Get the current max position for this artist
            max_position = db.query(func.max(ArtistVideoOrder.display_order)).filter(
                ArtistVideoOrder.artist_id == video.artist_id
            ).scalar()
            
            # If no videos exist yet, start at 1, otherwise increment
            next_position = 1 if max_position is None else max_position + 1
            
            # Create order entry
            order_entry = ArtistVideoOrder(
                artist_id=video.artist_id,
                video_id=video.id,
                display_order=next_position
            )
            db.add(order_entry)
        
        # Commit order entries
        db.commit()
        
        return created_videos
        
    except Exception as e:
        db.rollback()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create videos: {str(e)}. All changes have been rolled back."
        )
# ============================================================================
# EDIT VIDEO ENDPOINT
# ============================================================================
@router.patch("/admin-edit-video/{video_id}", response_model=VideoResponse)
async def edit_video(
    video_id: int,
    
    # Form fields - all optional for editing
    video_name: Optional[str] = Form(None),
    video_link: Optional[str] = Form(None),
    artist_name: Optional[str] = Form(None),  # NEW: Optional artist_name field
    artist_id: Optional[int] = Form(None),  # NEW: Optional artist_id field
    
    # Dependencies
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """
    Edit an existing video
    
    This endpoint requires authentication (JWT token)
    All fields are optional - only provided fields will be updated
    
    If video_link is updated and it's a YouTube URL, thumbnail will be auto-updated
    If video_link is updated and it's NOT YouTube, thumbnail will be set to None
    If artist_id is provided, it will be verified against the artists table
    
    Process:
    1. Find the video in the database
    2. Verify artist_id if provided
    3. Update fields if provided
    4. If video_link changed, extract new YouTube thumbnail (if applicable)
    5. Save changes to database
    6. Return updated video details
    
    Args:
        video_id: ID of the video to edit
        video_name: New video name (optional)
        video_link: New video link (optional)
        artist_name: New artist name (optional)
        artist_id: New artist ID to link (optional, set to -1 to remove link)
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Updated video with all details
    
    Raises:
        HTTPException 404 if video not found
        HTTPException 400 if artist_id is invalid
        HTTPException 500 if update fails
    """
    
    # Import Artist model for validation
    from app.models.artist import Artist
    
    # ========================================================================
    # STEP 1: Find the video in database
    # ========================================================================
    
    video = db.query(Video).filter(Video.id == video_id).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with ID {video_id} not found"
        )
    
    # ========================================================================
    # STEP 2: Verify artist_id if provided
    # ========================================================================
    
    if artist_id is not None:
        if artist_id == -1:
            # Special value to remove artist link
            video.artist_id = None
        else:
            # Verify the artist exists in the database
            artist = db.query(Artist).filter(Artist.id == artist_id).first()
            if not artist:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Artist with ID {artist_id} not found"
                )
            video.artist_id = artist_id
    
    # ========================================================================
    # STEP 3: Update fields if provided
    # ========================================================================
    
    if video_name is not None:
        video.video_name = video_name.strip()
    
    if artist_name is not None:
        video.artist_name = artist_name.strip()
    
    if video_link is not None:
        video.video_link = video_link.strip()
        
        # Extract new thumbnail if video link changed
        # This will be None if not a YouTube video
        video.thumbnail_url = get_youtube_thumbnail_url(video.video_link)
    
    # ========================================================================
    # STEP 4: Save changes to database
    # ========================================================================
    
    try:
        # Commit the changes
        db.commit()
        
        # Refresh to get the latest data
        db.refresh(video)
        
        # Return updated video
        return video
        
    except Exception as e:
        # If something goes wrong, rollback
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update video: {str(e)}"
        )



@router.delete("/admin-delete-video/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a video
    
    This endpoint requires authentication (JWT token)
    
    Deletes:
    - Video record from database
    - Note: Thumbnails are YouTube URLs, not uploaded files, so nothing to delete from Cloudinary
    
    Args:
        video_id: ID of the video to delete
        db: Database session
        current_user: Authenticated user (requires auth)
    
    Returns:
        204 No Content on success
    
    Raises:
        HTTPException 404 if video not found
        HTTPException 500 if deletion fails
    """
    
    # Find the video
    video = db.query(Video).filter(Video.id == video_id).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with ID {video_id} not found"
        )
    
    # Delete video from database
    # No need to delete thumbnail as it's a YouTube URL
    try:
        db.delete(video)
        db.commit()
        
        return None
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete video: {str(e)}"
        )