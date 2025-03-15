import os
import spotipy
from flask import Flask, request, jsonify, render_template
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Spotify authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
    scope="playlist-modify-public"
))

USER_ID = os.getenv("SPOTIFY_USER_ID")

# Function to use Gemini AI to summarize a sentence into a single word or phrase
def summarize_with_gemini(sentence):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(f"Summarize the following sentence into one word or a short phrase: {sentence}")
        return response.text.strip()
    except Exception as e:
        print("Error with Gemini API:", e)
        return sentence  # Fallback: Use the original input

# Function to search songs
def search_songs(keyword, limit):
    results = sp.search(q=keyword, type="track", limit=limit)
    tracks = results["tracks"]["items"]
    return [{"name": track["name"], "artist": track["artists"][0]["name"], "uri": track["uri"]} for track in tracks]

# Function to create a playlist
def create_playlist(name):
    playlist = sp.user_playlist_create(USER_ID, name, public=True, description="Generated via Flask + Gemini API")
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
    sentence = request.form.get('word')
    limit = request.form.get('limit', 10, type=int)

    if not sentence:
        return jsonify({"error": "Please enter a sentence"}), 400

    # Use Gemini to generate a keyword from the sentence
    keyword = summarize_with_gemini(sentence)
    print(f"🔍 Gemini Summary: {keyword}")

    # Search for tracks
    track_list = search_songs(keyword, limit)
    track_uris = [track["uri"] for track in track_list]

    if not track_uris:
        return jsonify({"error": "No songs found!"}), 404

    # Create a new playlist
    playlist_id = create_playlist(f"Playlist - {keyword}")

    # Add songs to the playlist
    add_songs_to_playlist(playlist_id, track_uris)

    return jsonify({
        "message": f"Playlist 'Songs about {keyword}' created successfully!",
        "keyword": keyword,
        "tracks": track_list
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
