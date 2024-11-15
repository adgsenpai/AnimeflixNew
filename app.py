from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
from flask_caching import Cache
from datetime import timedelta

app = Flask(__name__,template_folder='pages')
# Configure Flask-Caching
cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',  # SimpleCache for development; consider RedisCache for production
    'CACHE_DEFAULT_TIMEOUT': 300  # Cache timeout in seconds (e.g., 5 minutes)
})

# Jikan API Base URL
JIKAN_API_BASE = "https://api.jikan.moe/"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/jikan', methods=['POST'])
def api_jikan():
    data = request.get_json()
    endpoint = data.get('url')

    if not endpoint:
        return jsonify({"error": "No endpoint provided."}), 400

    # Define the cache key based on the endpoint
    cache_key = f"jikan_{endpoint}"

    # Check if response is cached
    cached_response = cache.get(cache_key)
    if cached_response:
        return jsonify(cached_response)

    # Construct the full URL
    url = f"{JIKAN_API_BASE}{endpoint}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Cache the response
        cache.set(cache_key, data, timeout=300)  # Cache for 5 minutes

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 429:
            return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
        else:
            return jsonify({"error": f"HTTP error occurred: {http_err}"}), response.status_code
    except requests.exceptions.RequestException as err:
        return jsonify({"error": f"Error fetching data: {err}"}), 500

@app.route('/api/anime/<int:mal_id>', methods=['GET'])
def get_anime_details(mal_id):
    endpoint = f"v4/anime/{mal_id}"
    cache_key = f"jikan_anime_{mal_id}"

    # Check if response is cached
    cached_response = cache.get(cache_key)
    if cached_response:
        return jsonify(cached_response)

    url = f"{JIKAN_API_BASE}{endpoint}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Cache the response
        cache.set(cache_key, data, timeout=300)  # Cache for 5 minutes

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 429:
            return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
        else:
            return jsonify({"error": f"HTTP error occurred: {http_err}"}), response.status_code
    except requests.exceptions.RequestException as err:
        return jsonify({"error": f"Error fetching data: {err}"}), 500


# Route to proxy Jikan API requests
@app.route('/api/jikan/top/anime', methods=['GET'])
def get_top_anime():
    try:
        filter_param = request.args.get('filter', 'airing')
        jikan_url = 'https://api.jikan.moe/v4/top/anime'
        params = {'filter': filter_param}
        response = requests.get(jikan_url, params=params)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        print(f'Error fetching data from Jikan API: {e}')
        return jsonify({'error': 'Failed to fetch data from Jikan API'}), 500

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/library')
def library():
    return render_template('library.html')

if __name__ == '__main__':
    app.run(debug=True)
