import copy
import os
from dataclasses import dataclass, field
from typing import Optional, List

from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from loguru import logger
from tqdm import tqdm

from .base import SeleniumCrawler


@dataclass
class Comment:
    username: str
    text: Optional[str] = ""
    like_count: Optional[int] = -1
    datetime: Optional[str] = ""


@dataclass
class Article:
    username: str
    article_id: str
    text: Optional[str] = ""
    like_count: Optional[int] = -1
    datetime: Optional[str] = ""
    image_urls: Optional[List[str]] = field(default_factory=list)
    tags: Optional[List[str]] = field(default_factory=list)
    comments: Optional[List[Comment]] = field(default_factory=list)


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
            main_page_url = f"{self.INSTAGRAM_URL}/{user}/"
            article_urls = self.get_article_urls(driver, main_page_url, limit=limit)
            articles = self.collect_articles(driver, article_urls, limit=limit)
            return articles
        finally:
            driver.quit()

    def run_on_hashtag(
        self,
        hashtag: str, *,
        limit: Optional[int] = 100
    ):
        driver = self._launch()

        try:
            main_page_url = f"{self.INSTAGRAM_URL}/explore/tags/{hashtag}/"
            article_urls = self.get_article_urls(driver, main_page_url, limit=limit)
            articles = self.collect_articles(driver, article_urls, limit=limit)
            return articles
        finally:
            driver.quit()

    def get_article_urls(
        self,
        driver: Chrome,
        main_page_url: str, *,
        limit: Optional[int] = 100,
        max_retry: Optional[int] = 5
    ) -> List[str]:
        driver.get(main_page_url)

        cache = {}
        prev_num_urls = 0
        retry_cnt = max_retry

        while (retry_cnt > 0 and len(cache.keys()) < limit):
            article_element = driver.find_element(By.TAG_NAME, "article")
            article_links = article_element.find_elements(By.TAG_NAME, "a")

            for article_link in article_links:
                href = article_link.get_attribute("href")
                if href not in cache:
                    cache[href] = None

            if prev_num_urls == len(cache.keys()):
                retry_cnt -= 1
            else:
                retry_cnt = max_retry
            
            prev_num_urls = len(cache.keys())
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._delay(1)

        return list(cache.keys())

    def collect_articles(
        self,
        driver: Chrome,
        article_urls: List[str], *,
        limit: Optional[int] = 100,
        retry: Optional[int] = 5,
        safe_delay: Optional[float] = 10
    ) -> List[Article]:
        articles = []
        for article_url in tqdm(article_urls[:limit]):
            article = self.get_article(driver, article_url, retry=retry)
            articles.append(article)
            self._delay(safe_delay)
        return articles

    def get_article(
        self,
        driver: Chrome,
        article_url: str, *,
        retry: Optional[int] = 5
    ) -> Article:
        driver.get(article_url)

        article_element = driver.find_element(By.TAG_NAME, "article")
        header_element = article_element.find_element(By.TAG_NAME, "header")
        username = header_element.text.split("\n")[0]
        article_id = driver.current_url.split("/")[-2]

        try:
            image_elements = article_element.find_elements(By.CLASS_NAME, "FFVAD")
            image_urls = [ image_element.get_attribute("src") for image_element in image_elements ]
            
            like_element = article_element.find_element_by_xpath(".//a[contains(@href, 'liked_by')]")
            like_count = int(like_element.text.split(" ")[0].replace(",", ""))
            
            time_element = article_element.find_elements(By.TAG_NAME, "time")[-1]
            d_time = time_element.get_attribute("datetime")

            main_element = article_element.find_element_by_xpath(".//li[@role='menuitem']")
            
            comments = self.get_comments(driver)

            try:
                tags = article_element.find_element_by_xpath(".//a[contains(@href, '/explore/tags')]")
            except Exception as e:
                logger.info(e)
                tags = []

            article = Article(
                username, article_id, main_element.text,
                like_count, d_time, image_urls, tags, comments
            )
            return article
        except Exception as e:
            logger.error(e)

            if retry > 1:
                return self.get_article(driver, article_url, retry=retry - 1)
            else:
                return Article(username, article_id)

    def get_comments(
        self,
        driver: Chrome,
        max_retry: Optional[int] = 5
    ) -> List[Comment]:
        article_element = driver.find_element(By.TAG_NAME, "article")

        prev_num_comments = 0
        retry_cnt = max_retry
        while(retry_cnt > 0):
            try:
                more_button = article_element.find_element_by_xpath(".//span[contains(@aria-label, 'Load more comments')]")
                more_button.click()
                self._delay(2)
                comment_elements = article_element.find_elements(By.CLASS_NAME, "Mr508")
                
                if prev_num_comments == len(comment_elements):
                    retry_cnt -= 1
                else:
                    retry_cnt = max_retry

                prev_num_comments = len(comment_elements)
            except Exception as e:
                logger.info(e)
                break

        try:
            comment_elements = article_element.find_elements(By.CLASS_NAME, "Mr508")
        except Exception as e:
            logger.info(e)
            comment_elements = []

        comments = []
        for comment_element in comment_elements:
            meta_elements = comment_element.find_elements(By.CLASS_NAME, "FH9sR")
            try:
                d_time = meta_elements[0].get_attribute("datetime")
            except Exception as e:
                logger.info(e)
                continue

            if len(meta_elements) == 3:
                like_count = int(meta_elements[1].text.split(" ")[0].replace(",", ""))
            else:
                like_count = 0

            username = comment_element.text.split("\n")[0]
            comment = Comment(
                username,
                comment_element.text,
                like_count,
                d_time
            )
            comments.append(comment)

        return comments

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
