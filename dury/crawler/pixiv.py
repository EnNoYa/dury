import os
from dataclasses import dataclass, field
import copy
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List

from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from loguru import logger
from tqdm import tqdm

from dury.utils import download
from dury.crawler.base import SeleniumCrawler


@dataclass
class Artwork:
    url: str
    title: Optional[str] = ""
    desc: Optional[str] = ""
    image_urls: Optional[List[str]] = field(default_factory=list)
    tags: Optional[List[str]] = field(default_factory=list)


class PixivCrawler(SeleniumCrawler):
    LOGIN_URL = "https://accounts.pixiv.net/login"
    PIXIV_URL = "https://www.pixiv.net"
    REQUEST_HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "Referer": "https://www.pixiv.net/"
    }

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        retry: Optional[int] = 5,
        *args, **kwargs
    ) -> None:
        super(PixivCrawler, self).__init__(*args, **kwargs)

        self.__username = username
        self.__password = password
        self.retry = retry

    def run_on_keyword(
        self,
        keyword: str, *,
        safe_mode: Optional[bool] = True,
        limit: Optional[int] = 100, 
        retry: Optional[int] = 5
    ) -> List[Artwork]:
        driver = self._launch()

        try:
            url = f"{self.PIXIV_URL}/tags/{keyword}/illustrations"
            if safe_mode:
                url += "?mode=safe"

            artwork_urls = self.get_artwork_urls(driver, url, limit=limit)
            artworks = self.collect_artworks(driver, artwork_urls, limit=limit, retry=retry)
            return artworks
        finally:
            driver.quit()

    def run_on_id(
        self,
        user_id: str, *,
        limit: Optional[int] = 100,
        retry: Optional[int] = 5
    ) -> List[Artwork]:
        driver = self._launch()

        try:
            url = f"{self.PIXIV_URL}/users/{user_id}/illustrations"
            artwork_urls = self.get_artwork_urls(driver, url, limit=limit)
            artworks = self.collect_artworks(driver, artwork_urls, limit=limit, retry=retry)
            return artworks
        finally:
            driver.quit()

    def run_on_user(
        self,
        username: str, *,
        limit: Optional[int] = 100,
        retry: Optional[int] = 5
    ) -> List[Artwork]:
        driver = self._launch()

        try:
            driver.get(f"{self.PIXIV_URL}/search_user.php?nick={username}&s_mode=s_usr")

            # Go to top user page
            target = driver.find_elements(By.CLASS_NAME, "user-recommendation-item")[0]
            target = target.find_element(By.CLASS_NAME, "title")
            target.click()
            self._delay()

            # New tab is created after link to user page is clicked
            last_tab = driver.window_handles[-1]

            # Switch to illustrations page
            logger.info("Switch to illustrations page")
            driver.switch_to.window(window_name=last_tab)

            url = f"{driver.current_url}/illustrations"
            artwork_urls = self.get_artwork_urls(driver, url, limit=limit)
            artworks = self.collect_artworks(driver, artwork_urls, limit=limit, retry=retry)
            return artworks
        finally:
            driver.quit()

    def get_artwork_urls(
        self,
        driver: Chrome,
        illustration_url: str, *,
        limit: Optional[int] = 100,
        artwork_urls: Optional[List[str]] = []
    ) -> List[str]:
        driver.get(illustration_url)

        image_cards = self._find_cards(driver)

        if len(image_cards) > 0:
            artwork_urls += [
                image_card.find_element(By.TAG_NAME, "a").get_attribute("href")
                for image_card in image_cards
            ]

            if len(artwork_urls) < limit:
                next_page = self._get_next_page(driver)
                return self.get_artwork_urls(driver, next_page, limit=limit, artwork_urls=artwork_urls)

        # free cache memory before return for next run
        tmp = copy.deepcopy(artwork_urls)
        artwork_urls.clear() 
        return tmp

    def collect_artworks(
        self,
        driver: Chrome,
        artwork_urls: List[str], *,
        limit: Optional[int] = 100,
        retry: Optional[int] = 5
    ) -> List[Artwork]:
        artworks = []
        for artwork_url in tqdm(artwork_urls[:limit]):
            artwork = self.get_artwork(driver, artwork_url, retry=retry)
            artworks.append(artwork)
        return artworks

    def get_artwork(
        self,
        driver: Chrome,
        artwork_url: str, *,
        retry: Optional[int] = 5
    ) -> Artwork:
        try:
            driver.get(artwork_url)
            figure = self._explicitly_wait(driver, 5, EC.visibility_of_element_located((By.TAG_NAME, "figure")))
            body = driver.find_element(By.TAG_NAME, "figcaption")
            
            try:
                title_element = body.find_element(By.TAG_NAME, "h1")
                title = title_element.text
            except Exception as e:
                logger.error(e)
                title = ""

            try:
                desc_element = body.find_element(By.TAG_NAME, "p")
                desc = desc_element.text
            except Exception as e:
                logger.error(e)
                desc = ""

            try:
                tag_body = body.find_element(By.TAG_NAME, "footer")
                tag_elements = tag_body.find_elements(By.TAG_NAME, "a")
                tags = [ tag_element.text for tag_element in tag_elements]
            except Exception as e:
                logger.error(e)
                tags = []

            image_elements = figure.find_elements(By.TAG_NAME, "img")
            image_urls = [ image_element.get_attribute("src") for image_element in image_elements ]
            return Artwork(artwork_url, title, desc, image_urls, tags)
        except Exception as e:
            if retry > 0:
                return self.get_artwork(driver, artwork_url, retry=retry - 1)
            else:
                return Artwork(artwork_url)

    def download_artworks(
        self,
        artworks: List[Artwork], *,
        output_dir: Optional[str] = "output/pixiv",
        num_workers: Optional[int] = 10,
    ):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        image_urls = []
        for artwork in artworks:
            image_urls += artwork.image_urls

        task = lambda x: download(
            x,
            os.path.join(output_dir, x.split("/")[-1]),
            headers=self.REQUEST_HEADERS
        )
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            results = list(tqdm(executor.map(task, image_urls), total=len(image_urls)))
        return results

    def _launch(self) -> Chrome:
        driver = super()._launch()
        status = self._load_cookies(driver, self.PIXIV_URL)
        if status < 0 and (self.__username and self.__password):
            self._login(self.__username, self.__password)
        return driver

    def _setup(self, mode: str, target: str) -> str:
        return super()._setup("pixiv", mode, target)

    def _login(self, driver: Chrome):
        driver.get(self.LOGIN_URL)
        self.delay()

        login_element = driver.find_element_by_xpath("//div[@id='container-login']")
        username_input_element = login_element.find_element_by_xpath(".//input[@type='text']")
        username_input_element.send_keys(self.__username)
        password_input_element = login_element.find_element_by_xpath(".//input[@type='password']")
        password_input_element.send_keys(self.__password)
        login_button = login_element.find_element_by_xpath(".//button")
        login_button.click()

        try:
            element = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "root")))
            self.save_cookies()
        except Exception as e:
            if not os.path.exists("tmp"):
                os.makedirs("tmp", exist_ok=True)
            driver.save_screenshot("./temp/login_err.png")
            driver.quit()
            raise IOError("login sim wait failed, 'root' did not appear")

    def _search(self, driver: Chrome, keyword: str):
        logger.info("Enter search bar")
        search_element = driver.find_element_by_xpath("//input[@type='text']")
        search_element.send_keys(keyword)
        search_element.submit()
    
    def _find_cards(self, driver: Chrome):
        section = driver.find_elements(By.TAG_NAME,"section")[0]
        image_cards = section.find_elements(By.TAG_NAME, "li")
        return image_cards

    def _get_next_page(self, driver: Chrome):
        nav_links = driver.find_elements_by_xpath(".//a[contains(@href, '?p=') or contains(@href, '&p=')]")
        next_page = nav_links[-1].get_attribute("href")
        return next_page

    def _select_user(self, driver: Chrome):
        logger.info("Select user on search result")
        user_href = driver.find_element(By.PARTIAL_LINK_TEXT, "유저")
        user_href.click()
