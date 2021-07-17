import os
from typing import Optional

from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from loguru import logger
from tqdm import tqdm

from dury.utils import download
from dury.crawler.base import SeleniumCrawler


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
        limit: Optional[int] = 100
    ):
        driver = self._launch()

        try:
            output_dir = self._setup("keyword", keyword)
            url = f"{self.PIXIV_URL}/tags/{keyword}/illustrations"
            if safe_mode:
                url += "?mode=safe"

            driver.get(url)

            artwork_urls = []
            while len(artwork_urls) < limit:
                next_page = self._get_next_page(driver)
                image_cards = self._find_cards(driver)
                artwork_urls += [
                    image_card.find_element(By.TAG_NAME, "a").get_attribute("href")
                    for image_card in image_cards
                ]
                driver.get(next_page)
                self._delay()

            logger.info("Start to download artworks")
            for artwork_url in tqdm(artwork_urls[:limit]):
                self.download_artworks(
                    driver, artwork_url, output_dir,
                    recursive=False,
                    retry=self.retry
                )
        finally:
            driver.quit()

    def run_on_id(
        self,
        user_id: str, *,
        limit: Optional[int] = 100
    ):
        driver = self._launch()

        try:
            output_dir = self._setup("user_id", user_id)

            driver.get(f"{self.PIXIV_URL}/users/{user_id}/illustrations")
            
            # Visit each artworks page recursively
            image_cards = self._find_cards(driver)
            latest_illust_url = image_cards[0].find_element(By.TAG_NAME, "a").get_attribute("href")

            logger.info("Start to download artworks")
            self.download_artworks(driver, latest_illust_url, output_dir, recursive=True, limit=limit, retry=self.retry)
        finally:
            driver.quit()

    def run_on_user(
        self,
        username: str, *,
        limit: Optional[int] = 100
    ):
        driver = self._launch()

        try:
            output_dir = self._setup("username", username)

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
            driver.get(f"{driver.current_url}/illustrations")

            # Visit each artworks page recursively
            image_cards = self._find_cards(driver)
            latest_illust_url = image_cards[0].find_element(By.TAG_NAME, "a").get_attribute("href")

            logger.info("Start to download artworks")
            self.download_artworks(driver, latest_illust_url, output_dir, recursive=True, limit=limit, retry=self.retry)

            driver.close()
            first_tab = driver.window_handles[0]
            driver.switch_to.window(window_name=first_tab)
        finally:
            driver.quit()

    def download_artworks(
        self,
        driver: Chrome,
        url: str,
        output_dir: str, *,
        recursive: Optional[bool] = False,
        limit: Optional[int] = 100,
        retry: Optional[int] = 5
    ):
        try:
            logger.info(f"Move to {url}")
            driver.get(url)
            
            figure = self._explicitly_wait(driver, 5, EC.visibility_of_element_located((By.TAG_NAME, "figure")))
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

            if recursive and limit > 1:
                nav = driver.find_elements(By.TAG_NAME, "nav")[-1]
                nav_elements = nav.find_elements(By.TAG_NAME, "a")
                last_nav_url = nav_elements[-1].get_attribute("href")
                
                if driver.current_url != last_nav_url:
                    self.download_artworks(driver, last_nav_url, output_dir, recursive=recursive, limit=limit - 1, retry=self.retry)
        except Exception as e:
            if retry > 0:
                logger.error(f"Retry to download {url} - {retry - 1}")
                self.download_artworks(driver, url, output_dir, recursive, limit, retry - 1)
            else:
                logger.error(e)
                # do something...

    def _launch(self) -> Chrome:
        driver = super()._launch()
        status = self._load_cookies(driver, self.PIXIV_URL)
        if status < 0 and (self.__username and self.__password):
            self._login(self.__username, self.__password)
        return driver

    def _setup(self, mode: str, target: str):
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
        nav_bar = driver.find_elements(By.TAG_NAME, "nav")
        nav_links = nav_bar[-1].find_elements(By.TAG_NAME, "a")
        next_page = nav_links[-1].get_attribute("href")
        return next_page

    def _select_user(self, driver: Chrome):
        logger.info("Select user on search result")
        user_href = driver.find_element(By.PARTIAL_LINK_TEXT, "유저")
        user_href.click()
