import json
import time
import os
from typing import Optional, Any

from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SeleniumCrawler:
    def __init__(
        self, *,
        output_dir: Optional[str] = "output",
        driver_path: Optional[str] = "./chromedriver",
        headless: Optional[bool] = False,
        implicitly_wait: Optional[float] = 10.0,
        cookie_file: Optional[str] = "cookies.json",
        safe_delay: Optional[float] = 1.0,
    ) -> None:
        self.output_dir = output_dir
        self.cookie_file = cookie_file
        self.safe_delay = safe_delay
        self.driver_path = driver_path
        self.headless = headless
        self.implicitly_wait = implicitly_wait

    def _launch(self) -> Chrome:
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")
        driver = Chrome(executable_path=self.driver_path, chrome_options=options)
        driver.implicitly_wait(self.implicitly_wait)
        return driver

    def _delay(self) -> None:
        time.sleep(self.safe_delay)

    def _explicitly_wait(self, driver: Chrome, timeout: float, condition: Any):
        return WebDriverWait(driver, timeout).until(condition)

    def _save_cookies(self, driver: Chrome):
        cookies = driver.get_cookies()
        with open(self.cookie_file, "w") as f:
            json.dump(cookies, f, indent=4)

    def _load_cookies(self, driver: Chrome, domain: str):
        driver.get(domain)

        if not os.path.exists(self.cookie_file):
            return -1

        with open(self.cookie_file, "r") as f:
                cookies = json.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
        return 0

    def _setup(self, platform, mode, target):
        output_dir = os.path.join(self.output_dir, platform, mode, target)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
