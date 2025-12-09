from .parsing import Parsing
from urllib.parse import urlparse
import logging
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup, Tag

# Configure logging
logger = logging.getLogger(__name__)


class Anime(Parsing):
    def __init__(self) -> None:
        super().__init__()
        logger.info("Initialized Anime scraper")

    def __get_card(self, item: Tag) -> Optional[Dict[str, str]]:
        """Extract card information from an anime page item."""
        try:
            # Extract title
            title_div = item.find("div", {"class": "tt"})
            if not title_div:
                logger.warning("Title div not found in anime item")
                return None

            # Extract headline
            headline_element = title_div.find("h2")
            headline = headline_element.text.strip() if headline_element else "Unknown"

            # Clean title by removing child elements
            for child in title_div.find_all():
                child.extract()
            title = title_div.text.strip() if title_div.text else "Unknown Title"

            # Extract type
            type_div = item.find("div", {"class": "typez"})
            anime_type = type_div.text.strip() if type_div else "Unknown"

            # Extract status
            status_span = item.find("span", {"class": "epx"})
            status = status_span.text.strip() if status_span else "Unknown"

            # Extract thumbnail
            thumbnail_img = item.find("img", {"src": True})
            thumbnail = ""
            if thumbnail_img:
                thumbnail = (
                    thumbnail_img.get("data-lazy-src") or thumbnail_img.get("src") or ""
                )

            # Extract URL and slug
            url_link = item.find("a", {"title": True})
            if not url_link or not url_link.get("href"):
                logger.warning("URL link not found in anime item")
                return None

            url = url_link.get("href")
            slug_path = urlparse(url).path
            slug = (
                slug_path.split("/")[-2]
                if slug_path.endswith("/")
                else slug_path.split("/")[-1]
            )

            card_data = {
                "title": title,
                "type": anime_type,
                "headline": headline,
                "status": status,
                "thumbnail": thumbnail,
                "slug": slug,
            }

            logger.debug(f"Successfully extracted card data for: {title}")
            return card_data

        except Exception as e:
            logger.error(f"Error extracting card data: {e}")
            return None

    def __get_home(
        self, data: BeautifulSoup
    ) -> Dict[str, Union[List[Dict[str, str]], int, str]]:
        """Extract anime list from the data."""
        try:
            content = data.find("div", {"class": "bixbox"})
            if not content:
                logger.warning("Content bixbox not found")
                return {
                    "results": [],
                    "total": 0,
                    "source": self.history_url,
                    "error": "Content section not found",
                }

            wrapper = content.find("div", {"class": "listupd"})
            if not wrapper:
                logger.warning("List wrapper not found")
                return {
                    "results": [],
                    "total": 0,
                    "source": self.history_url,
                    "error": "List wrapper not found",
                }

            articles = wrapper.find_all("article")
            cards = []

            for article in articles:
                try:
                    card = self.__get_card(article)
                    if card:
                        cards.append(card)
                except Exception as card_error:
                    logger.error(f"Error processing article: {card_error}")
                    continue

            result = {"results": cards, "total": len(cards), "source": self.history_url}

            logger.info(f"Successfully processed {len(cards)} anime items")
            return result

        except Exception as e:
            logger.error(f"Error extracting anime list: {e}")
            return {
                "results": [],
                "total": 0,
                "source": self.history_url,
                "error": str(e),
            }

    def get_details(
        self, **kwargs: Any
    ) -> Dict[str, Union[List[Dict[str, str]], int, str]]:
        """Get anime list with optional parameters."""
        try:
            logger.info("Fetching anime list")

            url = "/anime"
            data = self.get_parsed_html(url, **kwargs)

            if not data:
                logger.error("Failed to get anime page data")
                return {
                    "results": [],
                    "total": 0,
                    "source": self.history_url,
                    "error": "Failed to fetch anime page",
                }

            return self.__get_home(data)

        except Exception as e:
            logger.error(f"Error in get_details: {e}")
            return {
                "results": [],
                "total": 0,
                "source": self.history_url,
                "error": str(e),
            }


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    anime = Anime()
    print(anime.get_details())
