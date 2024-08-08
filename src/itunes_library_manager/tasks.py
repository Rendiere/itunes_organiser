from celery import Celery
from .database import SessionLocal
from .models import Track
import xml.etree.ElementTree as ET
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = os.getenv('REDIS_PORT', '6379')

celery = Celery('tasks', broker=f'redis://{redis_host}:{redis_port}/0',
                backend=f'redis://{redis_host}:{redis_port}/0')

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
))
@celery.task(bind=True)
def parse_xml(self, file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    total_tracks = len(root.findall('.//dict/dict/dict'))
    processed_tracks = 0

    db = SessionLocal()
    try:
        for track in root.findall('.//dict/dict/dict'):
            track_dict = {}
            for i in range(0, len(track), 2):
                key = track[i].text
                value = track[i+1].text
                track_dict[key] = value

            new_track = Track(
                title=track_dict.get('Name'),
                artist=track_dict.get('Artist'),
                album=track_dict.get('Album'),
                year=track_dict.get('Year'),
                genre=track_dict.get('Genre')
            )
            db.add(new_track)
            
            processed_tracks += 1
            self.update_state(state='PROGRESS', meta={'progress': processed_tracks / total_tracks * 100})

        db.commit()
    finally:
        db.close()

    return {"status": "completed"}

@celery.task
def infer_year(track_id):
    db = SessionLocal()
    try:
        track = db.query(Track).filter(Track.id == track_id).first()
        if not track:
            return {"status": "error", "message": "Track not found"}

        query = f"track:{track.title} artist:{track.artist}"
        results = spotify.search(q=query, type='track', limit=1)

        if results['tracks']['items']:
            spotify_track = results['tracks']['items'][0]
            album = spotify.album(spotify_track['album']['id'])
            
            confidence = 0.8  # You might want to adjust this based on your criteria
            
            track.spotify_matched_title = spotify_track['name']
            track.spotify_matched_artist = spotify_track['artists'][0]['name']
            track.spotify_matched_album = album['name']
            
            if album['release_date_precision'] == 'year':
                track.year = int(album['release_date'][:4])
                track.spotify_year_confidence = confidence
            
        db.commit()
        return {"status": "completed", "inferred_year": track.year, "confidence": track.spotify_year_confidence}
    finally:
        db.close()