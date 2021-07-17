from copy import copy
import os
from dataclasses import dataclass, field
from typing import Optional, List

from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from loguru import logger

from .base import SeleniumCrawler


@dataclass
class Article:
    username: str
    url: str
    title: Optional[str] = ""
    likes: Optional[int] = -1
    datetime: Optional[str] = ""
    image_urls: Optional[List[str]] = field(default_factory=list)
    tags: Optional[List[str]] = field(default_factory=list)


class InstagramCrawler(SeleniumCrawler):
    INSTAGRAM_URL = "https://www.instagram.com"
    LOGIN_URL = "https://www.instagram.com/accounts/login"

    def __init__(
        self,
        username: str,
        password: str,
        cookie_file: Optional[str] = "instagram_cookie.json",
        *args, **kwargs
    ) -> None:
        super(InstagramCrawler, self).__init__(*args, **kwargs)

        self.__username = username
        self.__password = password
        self.cookie_file = cookie_file

    def run_on_user(self, user: str, *, limit: Optional[int] = 100):
        driver = self._launch()

        try:
            url = f"{self.INSTAGRAM_URL}/{user}/"
            self.collect_articles(driver, url, limit=limit)
        finally:
            driver.quit()

    def run_on_hashtag(self, hashtag: str):
        driver = self._launch()

        try:
            url = f"{self.INSTAGRAM_URL}/explore/tags/{hashtag}/"
        finally:
            driver.quit()

    def collect_articles(
        self,
        driver: Chrome,
        page_url: str,
        limit: Optional[int] = 100
    ):
        driver.get(page_url)

        article = driver.find_element(By.TAG_NAME, "article")
        latest_article = article.find_element(By.TAG_NAME, "a").get_attribute("href")

        articles = self.traverse_articles(driver, latest_article, limit=limit)

        return articles

    def traverse_articles(
        self,
        driver: Chrome,
        article_url: str, *,
        limit: Optional[int] = 100,
        articles: Optional[List[Article]] = []
    ):
        article, pagination = self.get_article(driver, article_url)

        if limit > 0:
            return self.get_articles(driver, article_url, limit=limit - 1, articles=articles)

        tmp = copy.deepcopy(articles)
        articles.clear()
        return tmp

    def get_article(self, driver: Chrome, article_url):
        driver.get(article_url)

        article_element = driver.find_element(By.TAG_NAME, "article")
        
        header_element = article_element.find_element(By.TAG_NAME, "header")
        username = header_element.text.split("\n")[0]
        
        image_container = article_element.find_element_by_xpath("//div[@role='presentation']")
        image_elements = image_container.find_elements(By.TAG_NAME, "img")
        image_urls = [ image_element.get_attribute("src") for image_element in image_elements ]
        
        like_element = article_element.find_element_by_xpath(".//a[contains(@href, 'liked_by')]")
        like_count = int(like_element.text.split(" ")[0].replace(",", ""))
        
        time_element = article_element.find_elements(By.TAG_NAME, "time")[-1]
        d_time = time_element.get_attribute("datetime")

        # TODO: handle comment

        return None, None

    def _launch(self) -> Chrome:
        driver = super()._launch()
        status = self._load_cookies(driver, self.cookie_file, self.INSTAGRAM_URL)
        if status < 0:
            self._login(driver)
        return driver

    def _login(self, driver: Chrome):
        driver.get(self.LOGIN_URL)
        self._delay()

        login_element = driver.find_element(By.ID, "loginForm")
        login_button = login_element.find_element(By.TAG_NAME, "button")
        username_input_element = login_element.find_element_by_xpath(".//input[@type='text']")
        username_input_element.send_keys(self.__username)
        password_input_element = login_element.find_element_by_xpath(".//input[@type='password']")
        password_input_element.send_keys(self.__password)
        login_button.click()
        self._delay(8)

        main = driver.find_element(By.TAG_NAME, "main")
        save_info_button = main.find_element(By.TAG_NAME, "button")
        save_info_button.click()
        self._delay(5)
        
        try:
            element = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "react-root")))
            self._save_cookies(driver, self.cookie_file)
        except Exception as e:
            if not os.path.exists("tmp"):
                os.makedirs("tmp", exist_ok=True)
            driver.save_screenshot("./temp/login_err.png")
            driver.quit()
            raise IOError("login sim wait failed, 'root' did not appear")
