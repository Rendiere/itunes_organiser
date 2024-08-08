from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    artist = Column(String, index=True, nullable=True)
    album = Column(String, index=True, nullable=True)
    year = Column(Integer, nullable=True)
    genre = Column(String, nullable=True)
    spotify_year_confidence = Column(Float, nullable=True)
    spotify_matched_title = Column(String, nullable=True)
    spotify_matched_artist = Column(String, nullable=True)
    spotify_matched_album = Column(String, nullable=True)