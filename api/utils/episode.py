from .parsing import Parsing
from urllib.parse import urlparse, urlencode, parse_qsl
from dotenv import load_dotenv
from base64 import b64decode
from time import strptime, struct_time
import re
import logging
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup, Tag

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class Episode(Parsing):
    def __init__(self, slug: str) -> None:
        super().__init__()
        self.slug: str = slug
        logger.info(f"Initialized Episode scraper for slug: {slug}")

    def __get_info(self) -> Optional[BeautifulSoup]:
        """Get parsed HTML content for the episode page."""
        try:
            return self.get_parsed_html(self.slug)
        except Exception as e:
            logger.error(f"Failed to get episode info for slug {self.slug}: {e}")
            return None

    def __get_name(self, content: BeautifulSoup) -> str:
        """Extract episode name from the content."""
        try:
            name_element = content.find("h2", {"itemprop": "partOfSeries"})
            if name_element:
                name = name_element.text.strip()
                logger.debug(f"Found episode name: {name}")
                return name
            else:
                logger.warning("Episode name element not found")
                return "Unknown Episode"
        except Exception as e:
            logger.error(f"Error extracting episode name: {e}")
            return "Unknown Episode"

    def __get_root(self, content: BeautifulSoup) -> str:
        """Extract root anime slug from the content."""
        try:
            # Try breadcrumb first
            div = content.find("div", {"class": "ts-breadcrumb"})
            if div:
                li_elements = div.find_all("li")
                if len(li_elements) > 1:
                    a_element = li_elements[1].find("a")
                    if a_element and a_element.get("href"):
                        href = a_element.get("href")
                        slug_path = urlparse(href).path
                        slug = (
                            slug_path.split("/")[-2]
                            if slug_path.endswith("/")
                            else slug_path.split("/")[-1]
                        )
                        slug = slug.replace("/", "")
                        logger.debug(f"Found root slug from breadcrumb: {slug}")
                        return slug

            # Fallback to year span
            year_span = content.find("span", {"class": "year"})
            if year_span:
                a_elements = year_span.find_all("a")
                if a_elements:
                    last_a = a_elements[-1]
                    if last_a.get("href"):
                        href = last_a.get("href")
                        slug_path = urlparse(href).path
                        slug = (
                            slug_path.split("/")[-2]
                            if slug_path.endswith("/")
                            else slug_path.split("/")[-1]
                        )
                        slug = slug.replace("/", "")
                        logger.debug(f"Found root slug from year span: {slug}")
                        return slug

            logger.warning("Root slug not found")
            return "unknown"

        except Exception as e:
            logger.error(f"Error extracting root slug: {e}")
            return "unknown"

    def __get_thumbnail(self, content: BeautifulSoup) -> Optional[str]:
        """Extract thumbnail URL from the content."""
        try:
            # Try thumbnail div first
            thumbnail_div = content.find("div", {"class": "thumbnail"})
            if thumbnail_div:
                img = thumbnail_div.find("img")
                if img:
                    thumbnail = img.get("data-lazy-src") or img.get("src")
                    if thumbnail:
                        logger.debug(f"Found thumbnail from thumbnail div: {thumbnail}")
                        return thumbnail

            # Fallback to thumb div
            thumb_div = content.find("div", {"class": "thumb"})
            if thumb_div:
                img = thumb_div.find("img")
                if img:
                    thumbnail = img.get("data-lazy-src") or img.get("src")
                    if thumbnail:
                        logger.debug(f"Found thumbnail from thumb div: {thumbnail}")
                        return thumbnail

            logger.warning("Thumbnail not found")
            return None

        except Exception as e:
            logger.error(f"Error extracting thumbnail: {e}")
            return None

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
                strong_element = rating_div.find("strong")
                if strong_element:
                    rating_text = strong_element.text.strip()
                    parts = rating_text.split(" ")
                    if len(parts) > 1:
                        rating = parts[1]
                        logger.debug(f"Found rating: {rating}")
                        return rating

            logger.warning("Rating not found")
            return None
        except Exception as e:
            logger.error(f"Error extracting rating: {e}")
            return None

    def __get_sinopsis(self, data: BeautifulSoup) -> str:
        """Extract synopsis from the content."""
        try:
            sinopsis_div = data.find("div", {"class": "desc mindes"})
            if sinopsis_div:
                synopsis = sinopsis_div.get_text(strip=True)
                logger.debug(f"Found synopsis (length: {len(synopsis)})")
                return synopsis
            else:
                logger.warning("Synopsis section not found")
                return ""
        except Exception as e:
            logger.error(f"Error extracting synopsis: {e}")
            return ""

    def __parse_date(self, date_str: str) -> str:
        """Parse and format date string safely."""
        try:
            # Expected format: "July 31, 2023"
            clean_date = date_str.replace(",", "").strip()
            parsed_date = strptime(clean_date, "%B %d %Y")
            result = f"{parsed_date.tm_mon}/{parsed_date.tm_mday}/{parsed_date.tm_year}"
            logger.debug(f"Parsed date '{date_str}' to '{result}'")
            return result
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {e}")
            return date_str

    def __get_episodes(self, data: BeautifulSoup) -> List[Dict[str, Union[str, None]]]:
        """Extract episodes list from the content."""
        result = []
        try:
            episodelist_div = data.find("div", {"class": "episodelist"})
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
                    # Extract image info
                    img_element = item.find("img", {"class": "ts-post-image"})
                    if not img_element:
                        logger.warning(
                            f"Episode {i+1}: Image element not found, skipping"
                        )
                        continue

                    name = img_element.get("title", "Unknown")
                    thumbnail = (
                        img_element.get("data-lazy-src") or img_element.get("src") or ""
                    )

                    # Extract slug
                    link = item.find("a")
                    if not link or not link.get("href"):
                        logger.warning(f"Episode {i+1}: Link not found, skipping")
                        continue

                    slug = urlparse(link["href"]).path.strip("/")

                    # Extract playinfo
                    playinfo_div = item.find("div", {"class": "playinfo"})
                    if not playinfo_div:
                        logger.warning(f"Episode {i+1}: Playinfo not found, skipping")
                        continue

                    span_element = playinfo_div.find("span")
                    if span_element:
                        episode_headline = span_element.get_text(strip=True)

                        if episode_headline.startswith("Ep"):
                            parts = episode_headline.split(" - ")
                            eps = re.sub("[^0-9]", "", parts[0]) if parts else "Unknown"
                            subtitle = parts[1].strip() if len(parts) > 2 else None
                            date_raw = (
                                parts[2].strip()
                                if len(parts) > 2
                                else (parts[1].strip() if len(parts) > 1 else "")
                            )
                            date = self.__parse_date(date_raw) if date_raw else ""
                        else:
                            eps = "Unknown"
                            subtitle = None
                            date = ""
                    else:
                        eps = "Unknown"
                        subtitle = None
                        date = ""
                        logger.warning(f"Episode {i+1}: Span element not found")

                    episode_data = {
                        "name": name,
                        "thumbnail": thumbnail,
                        "slug": slug,
                        "subtitle": subtitle,
                        "date": date,
                        "episode": eps,
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

    def __execute_javascript_code(self, js_code: str) -> str:
        """Execute and decode JavaScript code safely."""
        try:
            # Extract variable values and dynamic value from JavaScript code
            matches = re.search(
                r"var (\w+) = (\[[^\]]+\]);.*?\)\s*-\s*(\d+)", js_code, re.DOTALL
            )

            if matches:
                variable_values = eval(
                    matches.group(2)
                )  # This is potentially unsafe but matches original
                dynamic_value = int(matches.group(3))

                # Decode and transform values
                result = "".join(
                    [
                        chr(
                            int(
                                "".join(
                                    filter(
                                        str.isdigit, b64decode(value).decode("utf-8")
                                    )
                                )
                            )
                            - dynamic_value
                        )
                        for value in variable_values
                    ]
                )
                logger.debug("Successfully executed JavaScript code")
                return result
            else:
                logger.warning("No matches found in JavaScript code")
                return ""
        except Exception as e:
            logger.error(f"Error executing JavaScript code: {e}")
            return ""

    def __get_video(
        self, data: BeautifulSoup
    ) -> Union[List[Dict[str, str]], Dict[str, str]]:
        """Extract video sources from the content."""
        try:
            scripts = data.find_all("script")
            script_elements = [
                script
                for script in scripts
                if "document.write(decodeURIComponent(escape(" in script.text
            ]

            if script_elements:
                script_text = script_elements[0].text
                decoded_data = self.__execute_javascript_code(script_text)
                if decoded_data:
                    parsed_data = self.parsing(decoded_data)
                    if parsed_data:
                        data = parsed_data

            video_select = data.find("select", {"name": "mirror"})
            if video_select:
                options = video_select.find_all("option")
                videos = []
                for option in options:
                    value = option.get("value")
                    text = option.text
                    if value:
                        video_info = self.__bs64(value, text)
                        if video_info:
                            videos.append(video_info)

                logger.info(f"Found {len(videos)} video sources")
                return videos
            else:
                logger.warning("Video select element not found")
                return {"error": "Video not found"}

        except Exception as e:
            logger.error(f"Error extracting video sources: {e}")
            return {"error": f"Video extraction failed: {str(e)}"}

    def __bs64(self, data: str, name: str = "") -> Optional[Dict[str, str]]:
        """Decode base64 video data safely."""
        try:
            if not data:
                return None

            decoded = b64decode(data).decode("utf-8")
            parsed_content = self.parsing(decoded)

            if parsed_content:
                iframe = parsed_content.find("iframe")
                if iframe and iframe.get("src"):
                    return {
                        "name": name.strip(),
                        "url": iframe["src"],
                    }

            logger.warning(f"Failed to decode video data for: {name}")
            return None

        except Exception as e:
            logger.error(f"Error decoding base64 video data for {name}: {e}")
            return None

    def to_json(self) -> Dict[str, Any]:
        """Convert scraped data to JSON format."""
        try:
            logger.info(f"Starting to scrape episode data for slug: {self.slug}")

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
            player_list = self.__get_video(data)
            name = self.__get_name(content)
            thumbnail = self.__get_thumbnail(data)
            genres = self.__get_genres(content)
            info_details = self.__get_info_details(content)
            rating = self.__get_rating(content)
            sinopsis = self.__get_sinopsis(data)
            episodes = self.__get_episodes(data)
            root = self.__get_root(data)

            # Combine all information
            result_info = {
                **info_details,
                "name": name,
                "genre": genres,
                "rating": rating,
                "sinopsis": sinopsis,
                "thumbnail": thumbnail,
                "episode": episodes,
                "players": player_list,
                "root": root,
            }

            result = {"result": result_info, "source": self.history_url}

            logger.info(f"Successfully scraped episode data for {name}")
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

    episode = Episode("against-the-sky-supreme-episode-218-subtitle-indonesia")
    print(episode.to_json())
