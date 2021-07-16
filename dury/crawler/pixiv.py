import os
from enum import Enum
from typing import Optional, Union

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from loguru import logger

from dury.utils import download
from dury.crawler.base import SeleniumCrawler


class PixivMode(Enum):
    USER = 0
    TAG = 1


class PixivCrawler(SeleniumCrawler):
    LOGIN_URL = "https://accounts.pixiv.net/login"
    PIXIV_URL = "https://www.pixiv.net"
    REQUEST_HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "Referer": "https://www.pixiv.net/"
    }
    VALID_MODE_LIST = ["keyword", "author"]

    def __init__(
        self,
        username: str,
        password: str, *,
        retry: Optional[int] = 5,
        limit: Optional[int] = 100,
        **kwargs
    ) -> None:
        super(PixivCrawler, self).__init__(**kwargs)

        self.retry = retry
        self.limit = limit

        status = self._load_cookies(self.PIXIV_URL)
        if status < 0:
            self._login(username, password)

    def run(self, target: str, mode: Optional[Union[PixivMode, int]] = 0):
        try:
            logger.info(f"Crawling target - {target}")

            if PixivMode(mode) is PixivMode.USER:
                self.run_on_user(target)
            elif PixivMode(mode) is PixivMode.TAG:
                self.run_on_keyword(target)
            else:
                raise NotImplementedError
        except Exception as e:
            logger.error(e)
        finally:
            self.driver.close()
 
    def run_on_keyword(
        self,
        keyword: str, *,
        output_dir: Optional[str] = "output",
        safe_mode: Optional[bool] = True
    ):
        self._setup("keyword", keyword)
        url = f"{self.PIXIV_URL}/tags/{keyword}/illustrations"
        if safe_mode:
            url += "?mode=safe"
        self.driver.get(url)

        # Visit all cards in each page recursively
        artwork_urls = []

        while len(artwork_urls) < self.limit:
            next_page = self._get_next_page()
            image_cards = self._find_cards()
            artwork_urls += [
                image_card.find_element(By.TAG_NAME, "a").get_attribute("href")
                for image_card in image_cards
            ]
            self.driver.get(next_page)
            self._delay()

        logger.info("Start to download artworks")
        for artwork_url in artwork_urls[:self.limit]:
            self.download_artworks(
                artwork_url, output_dir,
                recursive=False,
                retry=self.retry
            )

    def run_on_user(self, user: str, output_dir: str = "output"):
        self._setup("user", user)
        self.driver.get(f"{self.PIXIV_URL}/search_user.php?nick={user}")

        # Go to top user page
        target = self.driver.find_elements(By.CLASS_NAME, "user-recommendation-item")[0]
        target = target.find_element(By.CLASS_NAME, "title")
        target.click()
        self._delay()

        # New tab is created after link to user page is clicked
        last_tab = self.driver.window_handles[-1]

        # Switch to illustrations page
        logger.info("Switch to illustrations page")
        self.driver.switch_to.window(window_name=last_tab)
        self.driver.get(f"{self.driver.current_url}/illustrations")

        # Visit each artworks page recursively
        image_cards = self._find_cards()
        latest_illust_url = image_cards[0].find_element(By.TAG_NAME, "a").get_attribute("href")

        logger.info("Start to download artworks")
        self.download_artworks(latest_illust_url, output_dir, recursive=True, limit=self.limit, retry=self.retry)

        self.driver.close()
        first_tab = self.driver.window_handles[0]
        self.driver.switch_to.window(window_name=first_tab)

        return self.driver

    def download_artworks(self, url, output_dir, recursive=False, limit=100, retry=2):
        try:
            logger.info(f"Move to {url}")
            self.driver.get(url)
            
            figure = self.explicitly_wait(5, EC.visibility_of_element_located((By.TAG_NAME, "figure")))
            image_elements = figure.find_elements(By.TAG_NAME, "img")
            
            for image_element in image_elements:
                image_url = image_element.get_attribute("src")
                image_name = image_url.split("/")[-1]
                out_path = os.path.join(output_dir, image_name)
                if os.path.exists(out_path):
                    logger.info(f"Skip download {image_url}")
                    continue
                
                logger.info(f"Download {image_url}")
                status = download(image_url, out_path, self.REQUEST_HEADERS)
                if status < 0:
                    raise IOError(f"Failed to download {url}")

            if recursive and limit > 0:
                nav = self.driver.find_elements(By.TAG_NAME, "nav")[-1]
                nav_elements = nav.find_elements(By.TAG_NAME, "a")
                last_nav_url = nav_elements[-1].get_attribute("href")
                
                if self.driver.current_url != last_nav_url:
                    self.download_artworks(last_nav_url, output_dir, recursive, limit - 1, self.retry)
        except Exception as e:
            if retry > 0:
                logger.error(f"Retry to download {url} - {retry - 1}")
                self.download_artworks(url, output_dir, recursive, limit, retry - 1)
            else:
                logger.error(e)
                # do something...

    def _setup(self, mode, target):
        return super()._setup("pixiv", mode, target)

    def _login(self, username: str, password: str):
        self.driver.get(self.LOGIN_URL)
        self.delay()

        login_element = self.driver.find_element_by_xpath("//div[@id='container-login']")
        username_input_element = login_element.find_element_by_xpath(".//input[@type='text']")
        username_input_element.send_keys(username)
        password_input_element = login_element.find_element_by_xpath(".//input[@type='password']")
        password_input_element.send_keys(password)
        login_button = login_element.find_element_by_xpath(".//button")
        login_button.click()

        try:
            element = WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.ID, "root")))
            self.save_cookies()
        except Exception as e:
            if not os.path.exists("tmp"):
                os.makedirs("tmp", exist_ok=True)
            self.driver.save_screenshot("./temp/login_err.png")
            self.driver.quit()
            raise IOError("login sim wait failed, 'root' did not appear")

    def _search(self, keyword):
        logger.info("Enter search bar")
        search_element = self.driver.find_element_by_xpath("//input[@type='text']")
        search_element.send_keys(keyword)
        search_element.submit()
    
    def _find_cards(self):
        section = self.driver.find_elements(By.TAG_NAME,"section")[0]
        image_cards = section.find_elements(By.TAG_NAME, "li")
        return image_cards

    def _get_next_page(self):
        nav_bar = self.driver.find_elements(By.TAG_NAME, "nav")
        nav_links = nav_bar[-1].find_elements(By.TAG_NAME, "a")
        next_page = nav_links[-1].get_attribute("href")
        return next_page

    def _select_user(self):
        logger.info("Select user on search result")
        user_href = self.driver.find_element(By.PARTIAL_LINK_TEXT, "유저")
        user_href.click()
