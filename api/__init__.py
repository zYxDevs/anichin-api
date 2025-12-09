from dotenv import load_dotenv
from .utils.info import Info
from .utils.video import Video
from .utils.episode import Episode
from .utils.home import Home
from .utils.search import Search
from .utils.genre import Genres
from .utils.anime import Anime
import logging
from typing import Dict, List, Optional, Any, Union

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class Main:
    def __init__(self) -> None:
        logger.info("Initialized Main API handler")

    def get_info(self, slug: str) -> Dict[str, Any]:
        """Get anime information by slug."""
        try:
            logger.info(f"Getting info for slug: {slug}")
            return Info(slug).to_json()
        except Exception as e:
            logger.error(f"Error getting info for {slug}: {e}")
            return {"result": None, "error": str(e)}

    def get_video_source(self, slug: str) -> Union[Dict[str, Any], bool]:
        """Get video source by slug."""
        try:
            logger.info(f"Getting video source for slug: {slug}")
            return Video(slug).get_details()
        except Exception as e:
            logger.error(f"Error getting video source for {slug}: {e}")
            return False

    def get_episode(self, slug: str) -> Dict[str, Any]:
        """Get episode information by slug."""
        try:
            logger.info(f"Getting episode for slug: {slug}")
            return Episode(slug).to_json()
        except Exception as e:
            logger.error(f"Error getting episode for {slug}: {e}")
            return {"result": None, "error": str(e)}

    def get_home(self, page: int = 1) -> Dict[str, Any]:
        """Get home page content."""
        try:
            logger.info(f"Getting home page for page: {page}")
            return Home(page).get_details()
        except Exception as e:
            logger.error(f"Error getting home page {page}: {e}")
            return {"results": [], "page": page, "total": 0, "error": str(e)}

    def search(self, query: str) -> Dict[str, Any]:
        """Search anime by query."""
        try:
            logger.info(f"Searching for query: {query}")
            return Search(query).get_details()
        except Exception as e:
            logger.error(f"Error searching for {query}: {e}")
            return {"results": [], "query": query, "total": 0, "error": str(e)}

    def genres(self, genre: Optional[str] = None, page: int = 1) -> Dict[str, Any]:
        """Get genres list or anime by genre."""
        try:
            genres_handler = Genres()
            if not genre:
                logger.info("Getting genres list")
                return genres_handler.list_genre()
            else:
                logger.info(f"Getting genre '{genre}' page {page}")
                return genres_handler.get_genre(genre, page)
        except Exception as e:
            if genre:
                logger.error(f"Error getting genre {genre} page {page}: {e}")
                return {
                    "results": [],
                    "slug": genre,
                    "page": page,
                    "total": 0,
                    "error": str(e),
                }
            else:
                logger.error(f"Error getting genres list: {e}")
                return {"genres": [], "total": 0, "error": str(e)}

    def anime(self, **kwargs: Any) -> Dict[str, Any]:
        """Get anime list with optional parameters."""
        try:
            logger.info("Getting anime list")
            return Anime().get_details(**kwargs)
        except Exception as e:
            logger.error(f"Error getting anime list: {e}")
            return {"results": [], "total": 0, "error": str(e)}


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    main = Main()
    # Test video functionality
    video = main.get_video_source("perfect-world-episode-03-subtitle-indonesia")
    print(video)
