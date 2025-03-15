import os
import google.generativeai as genai
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Authenticate Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
    scope="playlist-modify-public"
))

USER_ID = os.getenv("SPOTIFY_USER_ID")

# Flask app
app = Flask(__name__)

# Function to summarize sentence into one word/phrase
def summarize_sentence(sentence):
    model = genai.GenerativeModel("gemini-1.5-pro")
    prompt = f"Summarize this sentence into one word or a short phrase: '{sentence}'"
    
    response = model.generate_content(prompt)
    return response.text.strip() if response else "music"

# Function to search songs on Spotify
def search_songs(query, limit=10):
    results = sp.search(q=query, type="track", limit=limit)
    return [{"name": track["name"], "artist": track["artists"][0]["name"], "uri": track["uri"]} for track in results["tracks"]["items"]]

# Function to create a playlist
def create_playlist(name):
    playlist = sp.user_playlist_create(USER_ID, name, public=True, description="Generated with OpenAI + Spotify API")
    return playlist["id"]

# Function to add songs to a playlist
def add_songs_to_playlist(playlist_id, track_uris):
    sp.playlist_add_items(playlist_id, track_uris)

# Route for homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to generate playlist
@app.route('/generate_playlist', methods=['POST'])
def generate_playlist():
    sentence = request.form.get('sentence')
    
    if not sentence:
        return jsonify({"error": "Please enter a sentence"}), 400

    # Step 1: Use Gemini to summarize the sentence into one word/phrase
    summarized_word = summarize_sentence(sentence)
    print(f"🎤 Gemini summarized: '{sentence}' → '{summarized_word}'")

    # Step 2: Search for songs on Spotify
    track_list = search_songs(summarized_word)
    track_uris = [track["uri"] for track in track_list]

    if not track_uris:
        return jsonify({"error": f"No songs found for '{summarized_word}'"}), 404

    # Step 3: Create a Spotify playlist
    playlist_id = create_playlist(f"Songs about {summarized_word}")

    # Step 4: Add songs to the playlist
    add_songs_to_playlist(playlist_id, track_uris)

    return jsonify({
        "message": f"Playlist 'Songs about {summarized_word}' created successfully!",
        "summarized_word": summarized_word,
        "tracks": track_list
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
