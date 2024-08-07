import xml.etree.ElementTree as ET
from prettytable import PrettyTable

class iTunesLibraryManager:
    def __init__(self, xml_path):
        self.xml_path = xml_path
        self.library_data = []
        self.conflicts = []

    def parse_xml(self):
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        tracks = root.find('./dict/dict')
        
        if tracks is None:
            return

        for track in tracks:
            if track.tag == 'dict':
                track_data = {}
                for i in range(0, len(track), 2):
                    key = track[i].text
                    value = track[i+1].text if track[i+1].tag in ['string', 'integer'] else track[i+1].tag
                    track_data[key] = value
                self.library_data.append(track_data)

    def enrich_metadata(self):
        for song in self.library_data:
            if 'Year' not in song:
                song['Year'] = '2024'  # Default year
            if 'Genre' not in song:
                song['Genre'] = 'Unknown'  # Default genre

    def preview_data(self):
        if not self.library_data:
            print("No data to preview. Make sure to parse the XML first.")
            return

        preview_size = min(5, len(self.library_data))  # Preview up to 5 tracks
        table = PrettyTable()
        table.field_names = ["Name", "Artist", "Album", "Year", "Genre"]
        
        for track in self.library_data[:preview_size]:
            table.add_row([
                track.get('Name', 'N/A'),
                track.get('Artist', 'N/A'),
                track.get('Album', 'N/A'),
                track.get('Year', 'N/A'),
                track.get('Genre', 'N/A')
            ])

        print(f"Previewing {preview_size} out of {len(self.library_data)} tracks:")
        print(table)

    def preview_conflicts(self):
        print("Conflict preview not yet implemented")

    def generate_updated_xml(self, output_path):
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

def main():
    input_path = "/Users/renier.botha/dev/personal/projects/in-progress/itunes_organiser/Library.xml"
    output_path = "/Users/renier.botha/dev/personal/projects/in-progress/itunes_organiser/Library_updated.xml"
    manager = iTunesLibraryManager(input_path)
    manager.parse_xml()
    manager.enrich_metadata()
    manager.preview_data()
    manager.preview_conflicts()
    manager.generate_updated_xml(output_path)

if __name__ == "__main__":
    main()