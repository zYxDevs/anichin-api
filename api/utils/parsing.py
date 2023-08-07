from bs4 import BeautifulSoup
from dotenv import load_dotenv
from os import getenv
from requests import Session

load_dotenv()


class Parsing(Session):
    def __init__(self) -> None:
        super().__init__()
        self.url = getenv("HOST", "")
        self.history_url = None

    def __get_html(self, slug, **kwargs):
        url = f"{self.url}{slug}" if slug.startswith("/") else f"{self.url}/{slug}"
        print(kwargs)
        r = self.get(url, **kwargs)
        self.history_url = url
        return r.text

    def get_parsed_html(self, url, **kwargs):
        return BeautifulSoup(self.__get_html(url, **kwargs), "html.parser")

    def parsing(self, data):
        return BeautifulSoup(data, "html.parser")
