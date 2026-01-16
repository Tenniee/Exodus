"""
Cloudinary configuration and image upload utilities
Handles image uploads to Cloudinary with auto-cropping
"""

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException, status
import os
from typing import Literal, Optional

# ============================================================================
# CLOUDINARY CONFIGURATION
# ============================================================================

# Configure Cloudinary with credentials from environment variables
# IMPORTANT: Store these in a .env file, never commit to git!
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dxno2dbla"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "591687732417823"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "czkLjU4PdqpZ1yEOg1GJsCg6XTA")
)

# ============================================================================
# IMAGE VALIDATION
# ============================================================================

# Allowed image formats
ALLOWED_FORMATS = ["jpg", "jpeg", "png", "webp"]

def validate_image_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is an allowed image format
    
    Args:
        file: The uploaded file from FastAPI
    
    Raises:
        HTTPException if file format is not allowed
    """
    # Get file extension from filename
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    # Extract extension (e.g., "image.jpg" -> "jpg")
    file_extension = file.filename.split(".")[-1].lower()
    
    if file_extension not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_FORMATS)}"
        )

# ============================================================================
# IMAGE UPLOAD FUNCTIONS
# ============================================================================

def upload_artist_banner(file: UploadFile, artist_name: str) -> str:
    """
    Uploads an artist banner image to Cloudinary with auto-cropping to rectangular format
    
    Banner dimensions: 1200x400 (3:1 aspect ratio - rectangular)
    
    Args:
        file: The uploaded banner image file
        artist_name: Name of the artist (used in filename)
    
    Returns:
        Cloudinary URL of the uploaded image
    
    Raises:
        HTTPException if upload fails or file format is invalid
    """
    # Validate the file format
    validate_image_file(file)
    
    try:
        # Upload to Cloudinary with transformations
        # folder: Organizes images in Cloudinary dashboard
        # public_id: Filename in Cloudinary (sanitized artist name)
        # transformation: Auto-crops and resizes to exact dimensions
        # crop: "fill" maintains aspect ratio and fills the dimensions
        # gravity: "auto" uses AI to focus on important parts of the image
        result = cloudinary.uploader.upload(
            file.file,
            folder="artists/banners",
            public_id=f"{artist_name.replace(' ', '_').lower()}_banner",
            transformation=[
                {
                    #"width": 1200,
                    #"height": 400,
                    #"crop": "fill",
                    "gravity": "auto"
                }
            ],
            overwrite=True  # Replace if image with same name exists
        )
        
        # Return the secure URL (https://) of the uploaded image
        return result["secure_url"]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload banner image: {str(e)}"
        )

def upload_artist_image(file: UploadFile, artist_name: str) -> str:
    """
    Uploads an artist profile image to Cloudinary with auto-cropping to square format
    
    Profile dimensions: 800x800 (1:1 aspect ratio - square)
    
    Args:
        file: The uploaded profile image file
        artist_name: Name of the artist (used in filename)
    
    Returns:
        Cloudinary URL of the uploaded image
    
    Raises:
        HTTPException if upload fails or file format is invalid
    """
    # Validate the file format
    validate_image_file(file)
    
    try:
        # Upload to Cloudinary with square crop transformation
        result = cloudinary.uploader.upload(
            file.file,
            folder="artists/profiles",
            public_id=f"{artist_name.replace(' ', '_').lower()}_profile",
            transformation=[
                {
                    "width": 800,
                    "height": 800,
                    "crop": "fill",
                    "gravity": "auto"  # AI-powered smart cropping
                }
            ],
            overwrite=True
        )
        
        return result["secure_url"]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile image: {str(e)}"
        )

def delete_cloudinary_image(image_url: str) -> bool:
    """
    Deletes an image from Cloudinary using its URL
    
    Args:
        image_url: The full Cloudinary URL of the image to delete
    
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        # Extract the public_id from the Cloudinary URL
        # Example URL: https://res.cloudinary.com/dxno2dbla/image/upload/v1234/artists/banners/drake_banner.jpg
        # We need: artists/banners/drake_banner
        
        # Split by '/upload/' to get the part after it
        parts = image_url.split('/upload/')
        if len(parts) < 2:
            return False
        
        # Get everything after '/upload/v1234/' (version number)
        # Remove the file extension
        path_with_version = parts[1]
        
        # Remove version number (e.g., 'v1234/')
        path_parts = path_with_version.split('/')
        if len(path_parts) < 2:
            return False
        
        # Reconstruct public_id without version and extension
        public_id_with_ext = '/'.join(path_parts[1:])
        public_id = public_id_with_ext.rsplit('.', 1)[0]  # Remove extension
        
        # Delete from Cloudinary
        result = cloudinary.uploader.destroy(public_id)
        
        # Cloudinary returns {'result': 'ok'} on success
        return result.get('result') == 'ok'
    
    except Exception as e:
        print(f"Failed to delete image from Cloudinary: {str(e)}")
        return False

def upload_song_cover_art(file: UploadFile, song_name: str, artist_name: str) -> str:
    """
    Uploads a song cover art to Cloudinary with auto-cropping to square format
    
    Cover art dimensions: 1000x1000 (1:1 aspect ratio - square, standard album art size)
    
    Args:
        file: The uploaded cover art image file
        song_name: Name of the song (used in filename)
        artist_name: Name of the artist (used in filename)
    
    Returns:
        Cloudinary URL of the uploaded cover art
    
    Raises:
        HTTPException if upload fails or file format is invalid
    """
    # Validate the file format
    validate_image_file(file)
    
    try:
        # Create a clean filename from song and artist name
        # Example: "Drake - God's Plan" -> "drake_gods_plan"
        clean_song_name = song_name.replace(' ', '_').replace("'", "").lower()
        clean_artist_name = artist_name.replace(' ', '_').replace("'", "").lower()
        filename = f"{clean_artist_name}_{clean_song_name}_cover"
        
        # Upload to Cloudinary with square crop transformation
        result = cloudinary.uploader.upload(
            file.file,
            folder="songs/covers",
            public_id=filename,
            transformation=[
                {
                    "width": 1000,
                    "height": 1000,
                    "crop": "fill",
                    "gravity": "auto"  # AI-powered smart cropping
                }
            ],
            overwrite=True  # Replace if image with same name exists
        )
        
        return result["secure_url"]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload cover art: {str(e)}"
        )
    
    # Look up the user in the database
    # db.query(User) starts a query on the User table
    # .filter() adds a WHERE clause (WHERE id = user_id)
    # .first() returns the first result or None
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


# ============================================================================
# ============================================================================
# ============================================================================

# ============================================================================
# YOUTUBE THUMBNAIL UTILITY
# ============================================================================

def extract_youtube_video_id(url: str) -> Optional[str]:
    """
    Extracts the video ID from a YouTube URL
    
    Supports formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    
    Args:
        url: YouTube video URL
    
    Returns:
        Video ID if URL is valid YouTube, None otherwise
    """
    import re
    from typing import Optional
    
    # Pattern to match various YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def get_youtube_thumbnail_url(video_url: str) -> Optional[str]:
    """
    Generates YouTube thumbnail URL from video URL
    
    Args:
        video_url: YouTube video URL
    
    Returns:
        Thumbnail URL if it's a valid YouTube video, None otherwise
    """
    video_id = extract_youtube_video_id(video_url)
    
    if video_id:
        # YouTube thumbnail URL pattern
        # maxresdefault.jpg gives the highest quality (1920x1080)
        # Falls back to hqdefault.jpg (480x360) if maxres not available
        return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    
    return None
    
    # Look up the user in the database
    # db.query(User) starts a query on the User table
    # .filter() adds a WHERE clause (WHERE id = user_id)
    # .first() returns the first result or None
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


def upload_user_profile_picture(file: UploadFile, user_id: int) -> str:
    """
    Uploads a user profile picture to Cloudinary with auto-cropping to square format
    
    Profile picture dimensions: 400x400 (1:1 aspect ratio - square)
    
    Args:
        file: The uploaded profile picture image file
        user_id: ID of the user (used in filename)
    
    Returns:
        Cloudinary URL of the uploaded profile picture
    
    Raises:
        HTTPException if upload fails or file format is invalid
    """
    # Validate the file format
    validate_image_file(file)
    
    try:
        # Upload to Cloudinary with square crop transformation
        result = cloudinary.uploader.upload(
            file.file,
            folder="users/profiles",
            public_id=f"user_{user_id}_profile",
            transformation=[
                {
                    "width": 400,
                    "height": 400,
                    "crop": "fill",
                    "gravity": "auto"  # AI-powered smart cropping
                }
            ],
            overwrite=True  # Replace if image with same name exists
        )
        
        return result["secure_url"]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )





def upload_playlist_cover_art(file: UploadFile, playlist_name: str) -> str:
    """
    Uploads a playlist cover art to Cloudinary without cropping
    Accepts any image size
    
    Args:
        file: The uploaded cover art image file
        playlist_name: Name of the playlist (used in filename)
    
    Returns:
        Cloudinary URL of the uploaded cover art
    
    Raises:
        HTTPException if upload fails or file format is invalid
    """
    # Validate the file format
    validate_image_file(file)
    
    try:
        # Create a clean filename from playlist name
        # Remove all special characters that Cloudinary doesn't allow
        import re
        
        # Replace spaces with underscores
        clean_name = playlist_name.replace(' ', '_')
        
        # Remove all characters except alphanumeric, underscore, and hyphen
        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '', clean_name)
        
        # Convert to lowercase
        clean_name = clean_name.lower()
        
        # If name is empty after sanitization, use a default
        if not clean_name:
            clean_name = "playlist"
        
        # Upload to Cloudinary without any transformations (keeps original size)
        result = cloudinary.uploader.upload(
            file.file,
            folder="playlists/covers",
            public_id=f"{clean_name}_cover",
            overwrite=True  # Replace if image with same name exists
        )
        
        return result["secure_url"]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload playlist cover art: {str(e)}"
        )


# ============================================================================
# ============================================================================
# ============================================================================

