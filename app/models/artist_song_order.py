# models/artist_song_order.py
"""
Artist Song Order model
Junction table for managing song display order per artist
"""

from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.models.database import Base

# ============================================================================
# ARTIST SONG ORDER MODEL (JUNCTION TABLE)
# ============================================================================

class ArtistSongOrder(Base):
    """
    ArtistSongOrder model - junction table linking artists to songs with ordering
    Allows each artist to have custom ordering of their songs
    """
    __tablename__ = "artist_song_orders"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to artists table
    artist_id = Column(Integer, ForeignKey('artists.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Foreign key to songs table
    song_id = Column(Integer, ForeignKey('songs.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Display order (position) for this song in this artist's profile
    # Lower number = appears first (1, 2, 3...)
    display_order = Column(Integer, nullable=False)
    
    # Ensure each artist can only have one order entry per song
    __table_args__ = (
        UniqueConstraint('artist_id', 'song_id', name='unique_artist_song'),
    )


# ============================================================================
# ============================================================================
# ============================================================================
