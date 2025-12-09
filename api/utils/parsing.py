from bs4 import BeautifulSoup
from dotenv import load_dotenv
from os import getenv
from requests import Session, Response
import logging
from typing import Optional, Dict, Any

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class Parsing(Session):
    def __init__(self) -> None:
        super().__init__()
        self.url: str = "https://anichin.club"
        self.history_url: Optional[str] = None
        logger.info(f"Initialized Parsing session with URL: {self.url}")

    def __get_html(self, slug: str, **kwargs: Any) -> Optional[str]:
        """Get HTML content from the specified slug."""
        try:
            if slug.startswith("/"):
                url = f"{self.url}{slug}"
            else:
                url = f"{self.url}/{slug}"

            cookies = "cf_clearance=XIBMo7QdecdvAcdM8uzEOnK_2UnaTHJJ8RieN.AoMY4-1748586290-1.2.1.1-UH.LSXh9BmHpSLaJS_QMPgFflT778PdhoLS1KmyRjdmD6fyvBCwlbktmnaZXXzHZkrmtk.LqI2A6LBAMEeSIjUiSkZOoleahDZ5cEEE1IM9hpSYAVSNFikWmc1UscY6NdDU_BNsHdRklnGzIKXkZ.Sbynw3BuFQmjHEgcq53BG9OQRl4BOHmZIQ4KZnfqu1IBc8o0WDYBkW_fKQgcVrLD81HY_1sObt1jDOV1cfSHMvTUoKOaVyJjASKrps90RTeM0QJtZmbFE8MBynNbZeZipOueDnYCEqaNjbI5BakFWEIEQ.t8ymqTVH37ZI0BGmacY.UwliDAFTYbPahtY6_Ac0xJbuH8BbrK_5dW3cjuswE_25hq1m0s.uuTc68owr1"

            headers: Dict[str, str] = {
                "User-Agent": getenv(
                    "USER_AGENT",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
                ),
                "Cookie": cookies,
            }

            if kwargs.get("headers"):
                headers.update(kwargs["headers"])
            kwargs["headers"] = headers

            logger.debug(f"Making request to: {url}")
            response: Response = self.get(url, **kwargs)
            response.raise_for_status()  # Raise an exception for bad status codes

            self.history_url = url
            logger.debug(f"Successfully fetched content from: {url}")
            return response.text

        except Exception as e:
            logger.error(f"Failed to fetch HTML from {slug}: {e}")
            return None

    def get_parsed_html(self, url: str, **kwargs: Any) -> Optional[BeautifulSoup]:
        """Get parsed HTML content using BeautifulSoup."""
        try:
            html_content = self.__get_html(url, **kwargs)
            if html_content:
                parsed = BeautifulSoup(html_content, "html.parser")
                logger.debug(f"Successfully parsed HTML content for: {url}")
                return parsed
            else:
                logger.warning(f"No HTML content to parse for: {url}")
                return None
        except Exception as e:
            logger.error(f"Failed to parse HTML for {url}: {e}")
            return None

    def parsing(self, data: str) -> Optional[BeautifulSoup]:
        """Parse HTML data using BeautifulSoup."""
        try:
            if not data:
                logger.warning("Empty data provided for parsing")
                return None

            parsed = BeautifulSoup(data, "html.parser")
            logger.debug("Successfully parsed provided HTML data")
            return parsed
        except Exception as e:
            logger.error(f"Failed to parse provided data: {e}")
            return None
