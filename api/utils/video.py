from .parsing import Parsing
from urllib.parse import urlparse, urlencode, parse_qsl
from dotenv import load_dotenv
import os
from base64 import b64decode
import logging
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class Video(Parsing):
    def __init__(self, slug: str) -> None:
        super().__init__()
        self.slug: str = slug
        logger.info(f"Initialized Video scraper for slug: {slug}")

    def get_details(self) -> Union[Dict[str, Any], bool]:
        """Get video details for the specified slug."""
        try:
            logger.info(f"Starting to fetch video details for slug: {self.slug}")

            data = self.get_parsed_html(self.slug)
            if not data:
                logger.error("Failed to get video page data")
                return False

            video_data = self.__get_video(data)
            return video_data

        except Exception as e:
            logger.error(f"Error in get_details for slug {self.slug}: {e}")
            return False

    def __get_video(self, data: BeautifulSoup) -> Union[Dict[str, Any], bool]:
        """Extract video information from the page data."""
        try:
            video_select = data.find("select", {"class": "mirror"})
            if not video_select:
                logger.warning("Video select element not found")
                return False

            options = video_select.find_all("option")
            if not options:
                logger.warning("No video options found")
                return False

            # Find OK.ru option
            okru_option = None
            for option in options:
                if option.text.strip() == "OK.ru":
                    okru_option = option
                    break

            if not okru_option or not okru_option.get("value"):
                logger.warning("OK.ru option not found or has no value")
                return False

            # Decode base64 video data
            try:
                video_value = okru_option["value"]
                decoded_data = b64decode(video_value).decode("utf-8")
                parsed_content = self.parsing(decoded_data)

                if not parsed_content:
                    logger.error("Failed to parse decoded video data")
                    return False

                iframe = parsed_content.find("iframe")
                if not iframe or not iframe.get("src"):
                    logger.error("Iframe not found or has no src")
                    return False

                video_src = iframe["src"].replace("videoembed", "video")
                logger.debug(f"Found video source: {video_src}")

            except Exception as decode_error:
                logger.error(f"Error decoding video data: {decode_error}")
                return False

            # Make request to video API
            try:
                api_url = "https://fastsavenow.com/wp-json/aio-dl/video-data/"
                params = {
                    "url": video_src,
                    "token": "a9c0082f6f8e3d7d5a00924c93ffe2deb6a42080ae9a8d25af54dc0b0d46e458",
                }

                user_agent = os.getenv(
                    "USER_AGENT",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                )
                headers = {"User-Agent": user_agent}

                logger.debug(f"Making API request to: {api_url}")
                response = self.post(api_url, data=params, headers=headers)

                if response.status_code != 200:
                    logger.error(
                        f"API request failed with status code: {response.status_code}"
                    )
                    return False

                results = response.json()
                logger.debug(f"API response received: {type(results)}")

                # Update media URLs
                updated_results = self.__update_media_urls(results, "ct=4")
                logger.info("Successfully processed video data")
                return updated_results

            except Exception as api_error:
                logger.error(f"Error making API request: {api_error}")
                return False

        except Exception as e:
            logger.error(f"Error extracting video data: {e}")
            return False

    def __update_media_urls(
        self, results: Dict[str, Any], query_string: str
    ) -> Dict[str, Any]:
        """Update media URLs with additional query parameters."""
        try:
            if not isinstance(results, dict) or "medias" not in results:
                logger.warning("Invalid results format for media URL update")
                return results

            medias = results.get("medias", [])
            if not isinstance(medias, list):
                logger.warning("Medias is not a list")
                return results

            for media in medias:
                try:
                    if not isinstance(media, dict) or "url" not in media:
                        logger.warning("Invalid media format, skipping")
                        continue

                    url_parts = urlparse(media["url"])
                    query = dict(parse_qsl(url_parts.query))

                    # Parse and add new query parameters
                    new_params = dict(
                        param.split("=")
                        for param in query_string.split("&")
                        if "=" in param
                    )
                    query.update(new_params)

                    # Reconstruct URL
                    updated_url_parts = url_parts._replace(query=urlencode(query))
                    media["url"] = updated_url_parts.geturl()

                    logger.debug(f"Updated media URL: {media['url']}")

                except Exception as media_error:
                    logger.error(f"Error updating media URL: {media_error}")
                    continue

            logger.debug(f"Updated {len(medias)} media URLs")
            return results

        except Exception as e:
            logger.error(f"Error in __update_media_urls: {e}")
            return results


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    video = Video("perfect-world-episode-03-subtitle-indonesia")
    print(video.get_details())
