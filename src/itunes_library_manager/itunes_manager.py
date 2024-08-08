import xml.etree.ElementTree as ET
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
from difflib import SequenceMatcher
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='itunes_library_manager.log',
                    filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

class iTunesLibraryManager:
    def __init__(self, xml_path, limit=None):
        self.xml_path = xml_path
        self.library_data = []
        self.conflicts = []
        self.spotify = self.setup_spotify()
        self.limit = limit

    def setup_spotify(self):
        load_dotenv()
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            logging.warning("Spotify API credentials not found in .env file. Year inference will be limited.")
            return None

        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        return spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def parse_xml(self):
        logging.info(f"Parsing XML file: {self.xml_path}")
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        tracks = root.find('./dict/dict')
        
        if tracks is None:
            logging.error("No tracks found in the XML file.")
            return

        for track in tracks:
            if track.tag == 'dict':
                track_data = {}
                for i in range(0, len(track), 2):
                    key = track[i].text
                    value = track[i+1].text if track[i+1].tag in ['string', 'integer'] else track[i+1].tag
                    track_data[key] = value
                self.library_data.append(track_data)
                if self.limit and len(self.library_data) >= self.limit:
                    break
        
        logging.info(f"Parsed {len(self.library_data)} tracks from the XML file.")

    def enrich_metadata(self):
        logging.info("Starting metadata enrichment process.")
        enriched_count = 0
        for song in self.library_data:
            if 'Year' not in song or not song['Year']:
                inferred_year, confidence = self.infer_year(song)
                if inferred_year:
                    song['Year'] = inferred_year
                    song['Spotify Year Confidence'] = f"{confidence:.2f}"
                    enriched_count += 1
                    logging.info(f"Inferred year {inferred_year} for '{song['Name']}' by {song['Artist']} with confidence {confidence:.2f}")
                else:
                    song['Year'] = 'Unknown'
                    song['Spotify Year Confidence'] = '0.00'
                    logging.warning(f"Failed to infer year for '{song['Name']}' by {song['Artist']}")
            if 'Genre' not in song:
                song['Genre'] = 'Unknown'
        logging.info(f"Metadata enrichment complete. Enriched {enriched_count} tracks.")

    def infer_year(self, song):
        if not self.spotify:
            logging.warning("Spotify client not available. Skipping year inference.")
            return None, 0.0

        query = f"track:{song['Name']} artist:{song['Artist']}"
        logging.debug(f"Searching Spotify with query: {query}")
        results = self.spotify.search(q=query, type='track', limit=10)

        if results['tracks']['items']:
            for track in results['tracks']['items']:
                name_similarity = self.get_similarity(song['Name'], track['name'])
                artist_similarity = self.get_similarity(song['Artist'], track['artists'][0]['name'])
                if name_similarity > 0.8 and artist_similarity > 0.8:
                    album = self.spotify.album(track['album']['id'])
                    release_date = album['release_date']
                    confidence = (name_similarity + artist_similarity) / 2
                    logging.debug(f"Found match: '{track['name']}' by {track['artists'][0]['name']}, released {release_date}, confidence: {confidence:.2f}")
                    return release_date[:4], confidence  # Extract year from release date

        logging.debug(f"No close match found for '{song['Name']}' by {song['Artist']}")
        return None, 0.0

    def get_similarity(self, a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def get_json_data(self):
        return json.dumps(self.library_data)

    def generate_updated_xml(self, output_path):
        logging.info(f"Generating updated XML file: {output_path}")
        root = ET.Element("plist")
        root.set('version', '1.0')
        
        tracks_dict = ET.SubElement(root, 'dict')
        tracks_key = ET.SubElement(tracks_dict, 'key')
        tracks_key.text = 'Tracks'
        
        tracks = ET.SubElement(tracks_dict, 'dict')
        
        for i, track in enumerate(self.library_data, start=1):
            track_dict = ET.SubElement(tracks, 'dict')
            for key, value in track.items():
                key_elem = ET.SubElement(track_dict, 'key')
                key_elem.text = key
                value_elem = ET.SubElement(track_dict, 'string')
                value_elem.text = str(value)
        
        tree = ET.ElementTree(root)
        with open(output_path, 'w', encoding='UTF-8') as f:
            tree.write(f, encoding='unicode', xml_declaration=True)
        logging.info(f"Updated XML file generated: {output_path}")

def main():
    logging.info("Starting iTunes Library Manager")
    input_path = "/Users/renier.botha/dev/personal/projects/in-progress/itunes_organiser/Library.xml"
    output_path = "/Users/renier.botha/dev/personal/projects/in-progress/itunes_organiser/Library_updated.xml"
    manager = iTunesLibraryManager(input_path, limit=50)  # Limit to 50 records
    manager.parse_xml()
    manager.enrich_metadata()
    manager.generate_updated_xml(output_path)
    logging.info("iTunes Library Manager process completed")

if __name__ == "__main__":
    main()