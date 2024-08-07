import pytest
from unittest.mock import mock_open, patch
from src.itunes_library_manager.main import iTunesLibraryManager

@pytest.fixture
def xml_content():
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Tracks</key>
    <dict>
        <key>1</key>
        <dict>
            <key>Track ID</key><integer>1</integer>
            <key>Name</key><string>Test Song</string>
            <key>Artist</key><string>Test Artist</string>
            <key>Album</key><string>Test Album</string>
            <key>Year</key><integer>2021</integer>
            <key>Genre</key><string>Rock</string>
        </dict>
    </dict>
</dict>
</plist>"""

@pytest.fixture
def manager():
    return iTunesLibraryManager("dummy_path.xml")

def test_parse_xml(manager, xml_content):
    with patch("builtins.open", mock_open(read_data=xml_content)):
        manager.parse_xml()
    assert len(manager.library_data) == 1
    assert manager.library_data[0]['Name'] == "Test Song"
    assert manager.library_data[0]['Artist'] == "Test Artist"

def test_enrich_metadata(manager):
    manager.library_data = [{"Name": "Test Song", "Artist": "Test Artist"}]
    manager.enrich_metadata()
    assert any('Year' in song for song in manager.library_data)
    assert any('Genre' in song for song in manager.library_data)

def test_preview_data(manager, capsys):
    manager.library_data = [{"Name": "Test Song", "Artist": "Test Artist"}]
    manager.preview_data()
    captured = capsys.readouterr()
    assert captured.out  # Check that something was printed

def test_preview_conflicts(manager, capsys):
    manager.conflicts = [{"Original": {"Name": "Test Song"}, "New": {"Name": "Different Name"}}]
    manager.preview_conflicts()
    captured = capsys.readouterr()
    assert captured.out  # Check that something was printed

def test_generate_updated_xml(manager):
    manager.library_data = [{"Name": "Test Song", "Artist": "Test Artist"}]
    with patch("builtins.open", mock_open()) as mock_file:
        manager.generate_updated_xml("output.xml")
    mock_file.assert_called_with("output.xml", "w", encoding="UTF-8")

if __name__ == '__main__':
    pytest.main()