from .parsing import Parsing
from urllib.parse import urlparse
import re
import logging
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup, Tag

# Configure logging
logger = logging.getLogger(__name__)


class Home(Parsing):
    def __init__(self, page: int = 1) -> None:
        super().__init__()
        self.__page: int = page
        logger.info(f"Initialized Home scraper for page: {page}")

    def __get_card(self, item: Tag) -> Optional[Dict[str, Union[str, int, None]]]:
        """Extract card information from a home page item."""
        try:
            # Extract title
            title_div = item.find("div", {"class": "tt"})
            if not title_div:
                logger.warning("Title div not found in home item")
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

            # Extract episode count
            eps_span = item.find("span", {"class": "epx"})
            eps = None
            if eps_span:
                eps_text = eps_span.text.strip()
                eps_numbers = re.sub("[^0-9]", "", eps_text)
                eps = int(eps_numbers) if eps_numbers else None

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
                logger.warning("URL link not found in home item")
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
                "eps": eps,
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
    ) -> Dict[str, Union[List[Dict[str, Any]], int, str]]:
        """Extract home page content from the data."""
        cards = []
        try:
            content_sections = data.find_all("div", {"class": "bixbox bbnofrm"})
            logger.info(f"Found {len(content_sections)} sections in home page")

            for section in content_sections:
                try:
                    # Extract section name
                    releases_div = section.find("div", "releases")
                    if releases_div:
                        section_element = releases_div.find()
                        section_name = (
                            section_element.text.lower().replace(" ", "_")
                            if section_element
                            else "unknown"
                        )
                    else:
                        section_name = "unknown"

                    # Extract articles
                    articles = section.find_all("article")
                    section_items = []

                    for article in articles:
                        try:
                            card = self.__get_card(article)
                            if card:
                                section_items.append(card)
                        except Exception as card_error:
                            logger.error(
                                f"Error processing article in section {section_name}: {card_error}"
                            )
                            continue

                    if section_items:
                        cards.append({"section": section_name, "cards": section_items})
                        logger.debug(
                            f"Added section '{section_name}' with {len(section_items)} items"
                        )

                except Exception as section_error:
                    logger.error(f"Error processing section: {section_error}")
                    continue

            result = {
                "results": cards,
                "page": self.__page,
                "total": len(cards),
                "source": self.history_url,
            }

            logger.info(
                f"Successfully processed {len(cards)} sections for page {self.__page}"
            )
            return result

        except Exception as e:
            logger.error(f"Error extracting home page content: {e}")
            return {
                "results": [],
                "page": self.__page,
                "total": 0,
                "source": self.history_url,
                "error": str(e),
            }

    def get_details(self) -> Dict[str, Union[List[Dict[str, Any]], int, str]]:
        """Get home page details."""
        try:
            logger.info(f"Starting to fetch home page for page: {self.__page}")

            url = ""
            if self.__page > 1:
                url = f"/page/{self.__page}/"

            data = self.get_parsed_html(url)
            if not data:
                logger.error("Failed to get home page data")
                return {
                    "results": [],
                    "page": self.__page,
                    "total": 0,
                    "source": self.history_url,
                    "error": "Failed to fetch home page",
                }

            return self.__get_home(data)

        except Exception as e:
            logger.error(f"Error in get_details for page {self.__page}: {e}")
            return {
                "results": [],
                "page": self.__page,
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

    home = Home(1)
    print(home.get_details())
