import logging
import sys
from typing import Text, Dict, Any, Tuple, Union
from flask import Flask, jsonify, request
from flask_cors import CORS
from api import Main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("anichin_api.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
main = Main()

# Configure CORS
CORS(app)


@app.get("/")
def read_root() -> Tuple[Dict[str, Any], int]:
    """
    Get home page
    params: page (optional) - int
    return: JSON
    """
    try:
        page = request.args.get("page")
        logger.info(f"Home page request with page: {page}")

        if page and not page.isdigit():
            logger.warning(f"Invalid page parameter: {page}")
            return jsonify(message="Page parameter must be a number"), 400

        page_num = int(page) if page else 1
        result = main.get_home(page_num)
        logger.info(f"Successfully served home page {page_num}")
        return result, 200

    except Exception as err:
        logger.error(f"Error in read_root: {err}")
        return jsonify(message=str(err)), 500


@app.get("/search/<query>")
def search(query: str) -> Tuple[Dict[str, Any], int]:
    """
    Search donghua by query
    params: query - string (required)
    return: JSON
    """
    try:
        if not query or not query.strip():
            logger.warning("Empty search query received")
            return jsonify(message="Search query cannot be empty"), 400

        logger.info(f"Search request for query: {query}")
        result = main.search(query.strip())
        logger.info(f"Successfully served search results for: {query}")
        return result, 200

    except Exception as err:
        logger.error(f"Error in search for query '{query}': {err}")
        return jsonify(message=str(err)), 500


@app.get("/<slug>")
def get_info(slug: Text) -> Tuple[Dict[str, Any], int]:
    """
    Show detail of donghua
    params: slug name of donghua - string (required)
    return: JSON
    """
    try:
        if not slug or not slug.strip():
            logger.warning("Empty slug received")
            return jsonify(message="Slug cannot be empty"), 400

        logger.info(f"Info request for slug: {slug}")
        data = main.get_info(slug.strip())

        if data.get("result") is None and data.get("error"):
            logger.warning(f"Info not found for slug: {slug}")
            return jsonify(message="Anime not found"), 404

        logger.info(f"Successfully served info for: {slug}")
        return data, 200

    except Exception as err:
        logger.error(f"Error in get_info for slug '{slug}': {err}")
        return jsonify(message=str(err)), 500


@app.get("/genres")
def list_genres() -> Tuple[Dict[str, Any], int]:
    """
    Show list of genres
    return: JSON
    """
    try:
        logger.info("Genres list request")
        data = main.genres()
        logger.info("Successfully served genres list")
        return data, 200

    except Exception as err:
        logger.error(f"Error in list_genres: {err}")
        return jsonify(message=str(err)), 500


@app.get("/genre/<slug>")
def get_genres(slug: str) -> Tuple[Dict[str, Any], int]:
    """
    Show list of donghua by genre
    params: slug genre - string (required)
    query: page (optional) - int
    return: JSON
    """
    try:
        if not slug or not slug.strip():
            logger.warning("Empty genre slug received")
            return jsonify(message="Genre slug cannot be empty"), 400

        page = request.args.get("page")
        if page and not page.isdigit():
            logger.warning(f"Invalid page parameter for genre: {page}")
            return jsonify(message="Page parameter must be a number"), 400

        page_num = int(page) if page else 1
        logger.info(f"Genre request for slug: {slug}, page: {page_num}")

        data = main.genres(slug.strip(), page_num)
        logger.info(f"Successfully served genre {slug} page {page_num}")
        return jsonify(data), 200

    except Exception as err:
        logger.error(f"Error in get_genres for slug '{slug}': {err}")
        return jsonify(message=str(err)), 500


@app.get("/episode/<slug>")
def get_episode(slug: Text) -> Tuple[Dict[str, Any], int]:
    """
    Get detail of episode
    params: slug episode - string (required)
    return: JSON
    """
    try:
        if not slug or not slug.strip():
            logger.warning("Empty episode slug received")
            return jsonify(message="Episode slug cannot be empty"), 400

        logger.info(f"Episode request for slug: {slug}")
        data = main.get_episode(slug.strip())

        if data.get("result") is None and data.get("error"):
            logger.warning(f"Episode not found for slug: {slug}")
            return jsonify(message="Episode not found"), 404

        logger.info(f"Successfully served episode: {slug}")
        return jsonify(data), 200

    except Exception as err:
        logger.error(f"Error in get_episode for slug '{slug}': {err}")
        return jsonify(message=str(err)), 500


@app.get("/video-source/<slug>")
def get_video(slug: Text) -> Tuple[Dict[str, Any], int]:
    """
    Show list of video source
    params: slug - string (required)
    return: JSON
    """
    try:
        if not slug or not slug.strip():
            logger.warning("Empty video slug received")
            return jsonify(message="Video slug cannot be empty"), 400

        logger.info(f"Video source request for slug: {slug}")
        data = main.get_video_source(slug.strip())

        if not data:
            logger.warning(f"Video source not found for slug: {slug}")
            return jsonify(message="Video source not found"), 404

        logger.info(f"Successfully served video source: {slug}")
        return jsonify(data), 200

    except Exception as err:
        logger.error(f"Error in get_video for slug '{slug}': {err}")
        return jsonify(message=str(err)), 500


@app.get("/anime")
def anime() -> Tuple[Dict[str, Any], int]:
    """
    Show list of anime
    return: JSON
    """
    try:
        logger.info("Anime list request")
        req = request.args
        params_dict = dict(req)

        logger.debug(f"Anime list parameters: {params_dict}")
        data = main.anime(params=params_dict)
        logger.info("Successfully served anime list")
        return jsonify(data), 200

    except Exception as err:
        logger.error(f"Error in anime: {err}")
        return jsonify(message=str(err)), 500


@app.errorhandler(404)
def not_found(error) -> Tuple[Dict[str, str], int]:
    """Handle 404 errors."""
    logger.warning(f"404 error: {request.url}")
    return jsonify(message="Endpoint not found"), 404


@app.errorhandler(500)
def internal_error(error) -> Tuple[Dict[str, str], int]:
    """Handle 500 errors."""
    logger.error(f"500 error: {error}")
    return jsonify(message="Internal server error"), 500


if __name__ == "__main__":
    logger.info("Starting Anichin API server")
    app.run(debug=True, host="0.0.0.0", port=5000)
