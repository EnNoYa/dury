import os
import sqlite3
from enum import Enum
from typing import Optional, Union

from selenium.webdriver import Chrome
from loguru import logger

from .base import SeleniumCrawler


class InstagramMode(Enum):
    USER = 0
    HASHTAG = 1


class InstagramCrawler(SeleniumCrawler):
    INSTAGRAM_URL = "https://www.instagram.com/"
    VALID_MODE_LIST = ["user", "hashtag"]

    def __init__(
        self, *,
        username: Optional[str] = None,
        password: Optional[str] = None,
        retry: Optional[int] = 5,
        limit: Optional[int] = 100,
        **kwargs
    ) -> None:
        super(InstagramCrawler, self).__init__(**kwargs)

        self.__username = username
        self.__password = password
        self.retry = retry

    def run_on_user(self, user: str):
        driver = self._launch()

        try:
            self._setup("user", user)
        finally:
            driver.quit()

    def run_on_hashtag(self, hashtag: str):
        driver = self._launch()

        try:
            self._setup("hashtag", hashtag)
        finally:
            driver.quit()

    def _setup(self, mode, target):
        return super()._setup("instagram", mode, target)

    def _launch(self) -> Chrome:
        driver = super()._launch()
        status = self._load_cookies(driver, self.PIXIV_URL)
        if status < 0 and (self.__username and self.__password):
            self._login(self.__username, self.__password)
        return driver

    def _login(self):
        ...
