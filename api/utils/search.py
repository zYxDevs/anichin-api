from .parsing import Parsing
from urllib.parse import urlparse
import logging
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup, Tag

# Configure logging
logger = logging.getLogger(__name__)


class Search(Parsing):
    def __init__(self, query: str) -> None:
        super().__init__()
        self.__query: str = query
        logger.info(f"Initialized Search for query: {query}")

    def __get_card(self, item: Tag) -> Dict[str, str]:
        """Extract card information from a search result item."""
        try:
            # Extract title
            title_div = item.find("div", {"class": "tt"})
            if not title_div:
                logger.warning("Title div not found in search item")
                return self.__get_default_card()

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
                logger.warning("URL link not found in search item")
                slug = "unknown"
            else:
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
            return self.__get_default_card()

    def __get_default_card(self) -> Dict[str, str]:
        """Return default card data when extraction fails."""
        return {
            "title": "Unknown Title",
            "type": "Unknown",
            "headline": "Unknown",
            "status": "Unknown",
            "thumbnail": "",
            "slug": "unknown",
        }

    def __get_home(
        self, data: BeautifulSoup
    ) -> Dict[str, Union[List[Dict[str, str]], str, int]]:
        """Extract search results from the home page data."""
        try:
            content = data.find("div", {"class": "bixbox"})
            if not content:
                logger.warning("Content bixbox not found")
                return {
                    "results": [],
                    "query": self.__query,
                    "total": 0,
                    "source": self.history_url,
                    "error": "Content section not found",
                }

            wrapper = content.find("div", {"class": "listupd"})
            if not wrapper:
                logger.warning("List wrapper not found")
                return {
                    "results": [],
                    "query": self.__query,
                    "total": 0,
                    "source": self.history_url,
                    "error": "List wrapper not found",
                }

            articles = wrapper.find_all("article")
            logger.info(f"Found {len(articles)} search results")

            cards = []
            for i, article in enumerate(articles):
                try:
                    card = self.__get_card(article)
                    cards.append(card)
                except Exception as card_error:
                    logger.error(f"Error processing article {i+1}: {card_error}")
                    continue

            result = {
                "results": cards,
                "query": self.__query,
                "total": len(cards),
                "source": self.history_url,
            }

            logger.info(
                f"Successfully processed {len(cards)} search results for query: {self.__query}"
            )
            return result

        except Exception as e:
            logger.error(f"Error extracting search results: {e}")
            return {
                "results": [],
                "query": self.__query,
                "total": 0,
                "source": self.history_url,
                "error": str(e),
            }

    def get_details(self) -> Dict[str, Union[List[Dict[str, str]], str, int]]:
        """Get search details for the query."""
        try:
            logger.info(f"Starting search for query: {self.__query}")

            url = f"/?s={self.__query}"
            data = self.get_parsed_html(url)

            if not data:
                logger.error("Failed to get search page data")
                return {
                    "results": [],
                    "query": self.__query,
                    "total": 0,
                    "source": self.history_url,
                    "error": "Failed to fetch search page",
                }

            return self.__get_home(data)

        except Exception as e:
            logger.error(f"Error in get_details for query {self.__query}: {e}")
            return {
                "results": [],
                "query": self.__query,
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

    search = Search("one piece")
    print(search.get_details())
