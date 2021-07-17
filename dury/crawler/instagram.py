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
class Post:
    url: str
    title: Optional[str] = ""
    desc: Optional[str] = ""
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

    def run_on_user(self, user: str):
        driver = self._launch()

        try:
            url = f"{self.INSTAGRAM_URL}/{user}/"
            self.get_post_urls(driver, url)
        finally:
            driver.quit()

    def run_on_hashtag(self, hashtag: str):
        driver = self._launch()

        try:
            url = f"{self.INSTAGRAM_URL}/explore/tags/{hashtag}/"
        finally:
            driver.quit()

    def get_post_urls(self, driver: Chrome, page_url: str):
        driver.get(page_url)

        print("A")

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
