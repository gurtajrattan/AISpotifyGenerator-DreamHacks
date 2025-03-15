import os
import spotipy
from flask import Flask, request, jsonify, render_template
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Spotify authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
    scope="playlist-modify-public"
))

USER_ID = os.getenv("SPOTIFY_USER_ID")

# Function to search songs
def search_songs(word, limit=10):
    results = sp.search(q=word, type="track", limit=limit)
    tracks = results["tracks"]["items"]
    return [{"name": track["name"], "artist": track["artists"][0]["name"], "uri": track["uri"]} for track in tracks]

# Function to create a playlist
def create_playlist(name):
    playlist = sp.user_playlist_create(USER_ID, name, public=True, description="Generated via Flask + Spotify API")
    return playlist["id"]

# Function to add songs to a playlist
def add_songs_to_playlist(playlist_id, track_uris):
    sp.playlist_add_items(playlist_id, track_uris)

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_playlist', methods=['POST'])
def generate_playlist():
    word = request.form.get('word')
    
    if not word:
        return jsonify({"error": "Please enter a word"}), 400

    # Search for tracks
    track_list = search_songs(word)
    track_uris = [track["uri"] for track in track_list]

    if not track_uris:
        return jsonify({"error": "No songs found!"}), 404

    # Create a new playlist
    playlist_id = create_playlist(f"Songs about {word}")

    # Add songs to the playlist
    add_songs_to_playlist(playlist_id, track_uris)

    return jsonify({
        "message": f"Playlist 'Songs about {word}' created successfully!",
        "tracks": track_list
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
