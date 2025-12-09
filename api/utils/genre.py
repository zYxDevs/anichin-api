from .parsing import Parsing
from urllib.parse import urlparse
import logging
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup, Tag

# Configure logging
logger = logging.getLogger(__name__)


class Genres(Parsing):
    def __init__(self) -> None:
        super().__init__()
        logger.info("Initialized Genres scraper")

    def __get_card(self, item: Tag) -> Optional[Dict[str, str]]:
        """Extract card information from a genre page item."""
        try:
            # Extract title
            title_div = item.find("div", {"class": "tt"})
            if not title_div:
                logger.warning("Title div not found in genre item")
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
                logger.warning("URL link not found in genre item")
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

    def list_genre(self) -> Dict[str, Union[List[Dict[str, str]], int, str]]:
        """Get list of all available genres."""
        try:
            logger.info("Fetching list of genres")

            data = self.get_parsed_html("/anime")
            if not data:
                logger.error("Failed to get anime page data")
                return {
                    "genres": [],
                    "total": 0,
                    "source": self.history_url,
                    "error": "Failed to fetch genres page",
                }

            genre_inputs = data.find_all("input", {"name": "genre[]", "value": True})
            genres = []

            for genre_input in genre_inputs:
                try:
                    value = genre_input.get("value")
                    if value:
                        name = " ".join(value.split("-")).title()
                        genres.append(
                            {
                                "name": name,
                                "slug": value,
                            }
                        )
                except Exception as genre_error:
                    logger.error(f"Error processing genre input: {genre_error}")
                    continue

            result = {
                "genres": genres,
                "total": len(genres),
                "source": self.history_url,
            }

            logger.info(f"Successfully found {len(genres)} genres")
            return result

        except Exception as e:
            logger.error(f"Error fetching genres list: {e}")
            return {
                "genres": [],
                "total": 0,
                "source": self.history_url,
                "error": str(e),
            }

    def get_genre(
        self, slug: str, page: int = 1
    ) -> Dict[str, Union[List[Dict[str, str]], str, int]]:
        """Get anime list for a specific genre."""
        try:
            logger.info(f"Fetching genre '{slug}' page {page}")

            url = f"/anime?genre[]={slug}"
            if page > 1:
                url = f"{url}&page={page}"

            data = self.get_parsed_html(url)
            if not data:
                logger.error("Failed to get genre page data")
                return {
                    "results": [],
                    "slug": slug,
                    "page": page,
                    "total": 0,
                    "source": self.history_url,
                    "error": "Failed to fetch genre page",
                }

            content = data.find("div", {"class": "bixbox"})
            if not content:
                logger.warning("Content bixbox not found")
                return {
                    "results": [],
                    "slug": slug,
                    "page": page,
                    "total": 0,
                    "source": self.history_url,
                    "error": "Content section not found",
                }

            wrapper = content.find("div", {"class": "listupd"})
            if not wrapper:
                logger.warning("List wrapper not found")
                return {
                    "results": [],
                    "slug": slug,
                    "page": page,
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
                    logger.error(
                        f"Error processing article in genre {slug}: {card_error}"
                    )
                    continue

            result = {
                "results": cards,
                "slug": slug,
                "page": page,
                "total": len(cards),
                "source": self.history_url,
            }

            logger.info(
                f"Successfully processed {len(cards)} items for genre '{slug}' page {page}"
            )
            return result

        except Exception as e:
            logger.error(f"Error fetching genre {slug} page {page}: {e}")
            return {
                "results": [],
                "slug": slug,
                "page": page,
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

    genres = Genres()
    print(genres.list_genre())
    print(genres.get_genre("action", 1))
