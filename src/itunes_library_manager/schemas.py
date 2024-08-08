from pydantic import BaseModel
from typing import Optional

class TrackBase(BaseModel):
    title: Optional[str]
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    spotify_year_confidence: Optional[float] = None
    spotify_matched_title: Optional[str] = None
    spotify_matched_artist: Optional[str] = None
    spotify_matched_album: Optional[str] = None

class TrackCreate(TrackBase):
    pass

class TrackUpdate(TrackBase):
    pass

class TrackResponse(TrackBase):
    id: int

    class Config:
        orm_mode = True