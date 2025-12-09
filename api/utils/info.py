from .parsing import Parsing
from urllib.parse import urlparse
import re
import logging
from time import strptime, struct_time
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup, Tag

# Configure logging
logger = logging.getLogger(__name__)


class Info(Parsing):
    def __init__(self, slug: str) -> None:
        super().__init__()
        self.__thumbnail: Optional[str] = None
        self.slug: str = slug
        logger.info(f"Initialized Info scraper for slug: {slug}")

    def __get_info(self) -> Optional[BeautifulSoup]:
        """Get parsed HTML content for the anime info page."""
        try:
            if "anixverse" in self.url:
                return self.get_parsed_html(f"anime/{self.slug}")
            return self.get_parsed_html(self.slug)
        except Exception as e:
            logger.error(f"Failed to get info for slug {self.slug}: {e}")
            return None

    def __get_name(self, content: BeautifulSoup) -> str:
        """Extract anime name from the content."""
        try:
            name_element = content.find(
                "h1", {"class": "entry-title", "itemprop": "name"}
            )
            if name_element:
                name = name_element.text.strip()
                logger.debug(f"Found anime name: {name}")
                return name
            else:
                logger.warning("Anime name element not found")
                return "Unknown Title"
        except Exception as e:
            logger.error(f"Error extracting anime name: {e}")
            return "Unknown Title"

    def __get_thumbnail(self, content: BeautifulSoup) -> str:
        """Extract thumbnail URL from the content."""
        try:
            thumb_div = content.find("div", {"class": "thumb"})
            if thumb_div:
                img_element = thumb_div.find("img")
                if img_element:
                    thumbnail = img_element.get("data-lazy-src") or img_element.get(
                        "src"
                    )
                    if thumbnail:
                        self.__thumbnail = thumbnail
                        logger.debug(f"Found thumbnail: {thumbnail}")
                        return thumbnail

            logger.warning("Thumbnail not found")
            return ""
        except Exception as e:
            logger.error(f"Error extracting thumbnail: {e}")
            return ""

    def __get_genres(self, content: BeautifulSoup) -> List[str]:
        """Extract genres from the content."""
        try:
            genres_div = content.find("div", {"class": "genxed"})
            if genres_div:
                genre_links = genres_div.find_all("a")
                genres = [
                    link.text.strip() for link in genre_links if link.text.strip()
                ]
                logger.debug(f"Found genres: {genres}")
                return genres
            else:
                logger.warning("Genres section not found")
                return []
        except Exception as e:
            logger.error(f"Error extracting genres: {e}")
            return []

    def __get_info_details(self, content: BeautifulSoup) -> Dict[str, str]:
        """Extract detailed information from the content."""
        try:
            info_content = content.find("div", {"class": "info-content"})
            if not info_content:
                logger.warning("Info content section not found")
                return {}

            spe_div = info_content.find("div", {"class": "spe"})
            if not spe_div:
                logger.warning("Spe div not found in info content")
                return {}

            spans = spe_div.find_all("span")
            info_dict = {}

            for span in spans:
                try:
                    text = span.text.strip()
                    if ":" in text:
                        key, value = text.split(":", 1)
                        key = key.strip().lower().replace(" ", "_")
                        value = value.strip()
                        if key and value:
                            info_dict[key] = value
                except Exception as span_error:
                    logger.warning(f"Error processing span element: {span_error}")
                    continue

            logger.debug(f"Extracted info details: {info_dict}")
            return info_dict
        except Exception as e:
            logger.error(f"Error extracting info details: {e}")
            return {}

    def __get_rating(self, content: BeautifulSoup) -> Optional[str]:
        """Extract rating from the content."""
        try:
            rating_div = content.find("div", {"class": "rating"})
            if rating_div:
                # Try to find rating in strong tag first
                strong_element = rating_div.find("strong")
                if strong_element:
                    rating_text = strong_element.text.strip()
                    parts = rating_text.split(" ")
                    if len(parts) > 1:
                        rating = parts[1]
                        logger.debug(f"Found rating (strong): {rating}")
                        return rating

                # Try numscore as fallback
                numscore_div = rating_div.find("div", {"class": "numscore"})
                if numscore_div:
                    rating = numscore_div.text.strip()
                    logger.debug(f"Found rating (numscore): {rating}")
                    return rating

            logger.warning("Rating not found")
            return None
        except Exception as e:
            logger.error(f"Error extracting rating: {e}")
            return None

    def __get_sinopsis(self, data: BeautifulSoup) -> str:
        """Extract synopsis from the content."""
        try:

            synopsis = data.find(
                "div", {"class": "entry-content", "itemprop": "description"}
            )
            if not synopsis:
                logger.warning("Synopsis div not found")
                return {}
            title_element = synopsis.find("h1")
            if not title_element:
                title = ""
            else:
                title = title_element.text.strip() + " - "
            paragraphs = synopsis.find_all("p")
            if not paragraphs:
                logger.warning("No paragraphs found in synopsis")
                paragraphs = [synopsis]
            return {
                "paragraphs": [
                    p.text.strip() for p in paragraphs if isinstance(p, Tag)
                ],
                "title": title.strip(),
            }
        except Exception as e:
            logger.error(f"Error extracting synopsis: {e}")
            return ""

    def __parse_date(self, date_str: str) -> str:
        """Parse and format date string safely."""
        try:
            # Expected format: "January 01, 2023"
            # Convert to "01 January 2023" format for parsing
            formatted_date = re.sub(
                r"(\w+)\s+(\d{1,2}),\s+(\d{4})", r"\2 \1 \3", date_str.strip()
            )

            # Parse the date
            parsed_date = strptime(formatted_date, "%d %B %Y")

            # Format as MM/DD/YYYY
            result = f"{parsed_date.tm_mon}/{parsed_date.tm_mday}/{parsed_date.tm_year}"
            logger.debug(f"Parsed date '{date_str}' to '{result}'")
            return result
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {e}")
            return date_str  # Return original string if parsing fails

    def __get_episodes(self, data: BeautifulSoup) -> List[Dict[str, Union[str, None]]]:
        """Extract episodes list from the content."""
        result = []
        try:
            episodelist_div = data.find("div", {"class": "eplister"})
            if not episodelist_div:
                logger.warning("Episode list section not found")
                return result

            ul_element = episodelist_div.find("ul")
            if not ul_element:
                logger.warning("Episode list UL element not found")
                return result

            episodes = ul_element.find_all("li")
            logger.info(f"Found {len(episodes)} episodes")

            for i, item in enumerate(episodes):
                try:
                    # Extract slug
                    link = item.find("a")
                    if not link or not link.get("href"):
                        logger.warning(f"Episode {i+1}: Link not found, skipping")
                        continue

                    slug = urlparse(link["href"]).path.strip("/")
                    subtitle = item.find("div", {"class": "epl-title"})
                    if subtitle:
                        subtitle = subtitle.text.strip()
                    else:
                        subtitle = f"Episode {i+1}"
                    date = item.find("div", {"class": "epl-date"})
                    if date:
                        date_text = date.text.strip()
                        date = self.__parse_date(date_text)
                    else:
                        date = "Unknown Date"
                    eps = item.find("div", {"class": "epl-num"})
                    if eps:
                        eps_text = eps.text.strip()
                        eps = eps_text
                    else:
                        eps = None

                    episode_data = {
                        "slug": slug,
                        "subtitle": subtitle,
                        "date": date,
                        "episode": eps,
                        "thumbnail": self.__thumbnail,
                    }

                    result.append(episode_data)
                    logger.debug(f"Successfully processed episode {i+1}: {slug}")

                except Exception as episode_error:
                    logger.error(f"Error processing episode {i+1}: {episode_error}")
                    continue

            logger.info(f"Successfully processed {len(result)} episodes")
            return result

        except Exception as e:
            logger.error(f"Error extracting episodes: {e}")
            return result

    def to_json(self) -> Dict[str, Any]:
        """Convert scraped data to JSON format."""
        try:
            logger.info(f"Starting to scrape data for slug: {self.slug}")

            data = self.__get_info()
            if not data:
                logger.error("Failed to get initial data")
                return {
                    "result": None,
                    "source": self.history_url,
                    "error": "Failed to fetch data",
                }

            content = data.find("div", {"class": "infox"})
            if not content:
                logger.error("Main content section not found")
                return {
                    "result": None,
                    "source": self.history_url,
                    "error": "Main content not found",
                }

            # Extract all information
            name = self.__get_name(content)
            thumbnail = self.__get_thumbnail(data)
            genres = self.__get_genres(content)
            info_details = self.__get_info_details(content)
            rating = self.__get_rating(data)
            sinopsis = self.__get_sinopsis(data)
            episodes = self.__get_episodes(data)

            # Combine all information
            result_info = {
                **info_details,
                "name": name,
                "thumbnail": thumbnail,
                "genre": genres,
                "rating": rating,
                "sinopsis": sinopsis,
                "episode": episodes,
            }

            result = {"result": result_info, "source": self.history_url}

            logger.info(f"Successfully scraped data for {name}")
            return result

        except Exception as e:
            logger.error(f"Error in to_json method: {e}")
            return {"result": None, "source": self.history_url, "error": str(e)}


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    info = Info("against-the-sky-supreme-episode-218-subtitle-indonesia")
    print(info.to_json())
