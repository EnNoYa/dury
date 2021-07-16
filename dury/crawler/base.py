import json
import time
import os
from typing import Optional, Any

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SeleniumCrawler:
    def __init__(
        self, *,
        driver_path: Optional[str] = "./chromedriver",
        headless: Optional[bool] = False,
        implicitly_wait: Optional[float] = 10.0,
        cookie_file: Optional[str] = "cookies.json",
        safe_delay: Optional[float] = 1.0,
    ) -> None:
        self.cookie_file = cookie_file
        self.safe_delay = safe_delay
        self.driver = self.launch(
            driver_path,
            headless=headless,
            implicitly_wait=implicitly_wait
        )

    def launch(
        self,
        driver_path: str, *,
        headless: Optional[bool] = False,
        implicitly_wait: Optional[float] = 10.0
    ) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")
        driver = webdriver.Chrome(executable_path=driver_path, chrome_options=options)
        driver.implicitly_wait(implicitly_wait)
        return driver

    def delay(self) -> None:
        time.sleep(self.safe_delay)

    def explicitly_wait(self, timeout: float, condition: Any):
        return WebDriverWait(self.driver, timeout).until(condition)

    def save_cookies(self):
        cookies = self.driver.get_cookies()
        with open(self.cookie_file, "w") as f:
            json.dump(cookies, f, indent=4)

    def load_cookies(self, domain: str):
        self.driver.get(domain)

        if not os.path.exists(self.cookie_file):
            return -1

        with open(self.cookie_file, "r") as f:
                cookies = json.load(f)
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        return 0
