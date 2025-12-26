# routes/artist_request.py
"""
Artist Request routes
Handles artist onboarding requests
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.models.database import get_db
from app.models.user import User
from app.models.artist_request import ArtistRequest
from app.schemas.artist_request import ArtistRequestSubmit, ArtistRequestResponse
from app.core.dependencies import get_current_user
from typing import Optional

# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(
    prefix="/artist-requests",
    tags=["Artist Requests"]
)

# ============================================================================
# SUBMIT ARTIST REQUEST (NO AUTH REQUIRED)
# ============================================================================

@router.post("/submit", response_model=ArtistRequestResponse, status_code=status.HTTP_201_CREATED)
def submit_artist_request(
    request_data: ArtistRequestSubmit,
    db: Session = Depends(get_db)
):
    """
    Submit an artist request (NO authentication required)
    
    This is a public endpoint for artists to request to join the platform
    
    Process:
    1. Check if email has already submitted a request
    2. Create new artist request in database
    3. Return request details with ID and timestamp
    
    Args:
        request_data: Artist request information including:
                     - artist_name (required)
                     - email (required)
                     - ig_link, yt_link, spotify_link, apple_music_link (optional)
                     - Service selections (booleans, default False)
        db: Database session
    
    Returns:
        Created artist request with ID, status, and timestamp
    
    Raises:
        HTTPException 400 if email has already submitted a request
    """
    
    # ========================================================================
    # STEP 1: Check if email already exists in artist_requests
    # ========================================================================
    
    existing_request = db.query(ArtistRequest).filter(
        ArtistRequest.email == request_data.email.lower()
    ).first()
    
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An artist request with this email already exists"
        )
    
    # ========================================================================
    # STEP 2: Create new artist request
    # ========================================================================
    
    new_request = ArtistRequest(
        artist_name=request_data.artist_name.strip(),
        email=request_data.email.lower().strip(),
        ig_link=request_data.ig_link.strip() if request_data.ig_link else None,
        yt_link=request_data.yt_link.strip() if request_data.yt_link else None,
        spotify_link=request_data.spotify_link.strip() if request_data.spotify_link else None,
        apple_music_link=request_data.apple_music_link.strip() if request_data.apple_music_link else None,
        music_distribution=request_data.music_distribution,
        music_publishing=request_data.music_publishing,
        prod_and_engineering=request_data.prod_and_engineering,
        marketing_and_promotions=request_data.marketing_and_promotions,
        status="pending"  # Default status
    )
    
    # Add to database
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    
    # Return the created request
    return new_request


# ============================================================================
# GET ALL ARTIST REQUESTS (REQUIRES AUTH)
# ============================================================================

@router.get("/admin-list", response_model=List[ArtistRequestResponse])
def get_all_artist_requests(
    status_filter: Optional[str] = None,  # Query param to filter by status
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """
    Get all artist requests (REQUIRES authentication)
    
    This endpoint is for admins to view all pending/approved/rejected requests
    
    Optionally filter by status using query parameter:
    - /admin-list?status_filter=pending
    - /admin-list?status_filter=approved
    - /admin-list?status_filter=rejected
    
    Args:
        status_filter: Optional status to filter by ("pending", "approved", "rejected")
        db: Database session
        current_user: Authenticated user (from JWT token)
    
    Returns:
        List of all artist requests (or filtered by status)
    """
    
    # Build query
    query = db.query(ArtistRequest)
    
    # Apply status filter if provided
    if status_filter:
        query = query.filter(ArtistRequest.status == status_filter.lower())
    
    # Order by newest first
    requests = query.order_by(ArtistRequest.created_at.desc()).all()
    
    return requests


# ============================================================================
# DELETE ARTIST REQUEST (REQUIRES AUTH)
# ============================================================================

@router.delete("/admin-remove-request/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_artist_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """
    Delete an artist request (REQUIRES authentication)
    
    This endpoint is for admins to remove artist requests from the system
    
    Args:
        request_id: ID of the artist request to delete
        db: Database session
        current_user: Authenticated user (from JWT token)
    
    Returns:
        204 No Content on success
    
    Raises:
        HTTPException 404 if request not found
    """
    
    # Find the artist request
    artist_request = db.query(ArtistRequest).filter(
        ArtistRequest.id == request_id
    ).first()
    
    if not artist_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist request with ID {request_id} not found"
        )
    
    # Delete the request
    db.delete(artist_request)
    db.commit()
    
    return None