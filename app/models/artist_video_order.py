# models/artist_video_order.py
"""
Artist Video Order model
Junction table for managing video display order per artist
"""

from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.models.database import Base

# ============================================================================
# ARTIST VIDEO ORDER MODEL (JUNCTION TABLE)
# ============================================================================

class ArtistVideoOrder(Base):
    """
    ArtistVideoOrder model - junction table linking artists to videos with ordering
    Allows each artist to have custom ordering of their videos
    """
    __tablename__ = "artist_video_orders"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to artists table
    artist_id = Column(Integer, ForeignKey('artists.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Foreign key to videos table
    video_id = Column(Integer, ForeignKey('videos.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Display order (position) for this video in this artist's profile
    # Lower number = appears first (1, 2, 3...)
    display_order = Column(Integer, nullable=False)
    
    # Ensure each artist can only have one order entry per video
    __table_args__ = (
        UniqueConstraint('artist_id', 'video_id', name='unique_artist_video'),
    )


# ============================================================================
# ============================================================================
# ============================================================================
