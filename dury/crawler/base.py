from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json
import time
import os


class SeleniumCrawler:
    def __init__(self, cfg) -> None:
        self.cookie_file = cfg.SELENIUM.COOKIE_FILE
        self.safe_delay = cfg.SELENIUM.SAFE_DELAY
        self.driver = self.launch(
            cfg.SELENIUM.CHROMEDRIVER_PATH,
            cfg.SELENIUM.HEADLESS,
            cfg.SELENIUM.IMPLICITLY_WAIT
        )

    def launch(self, driver_path, headless=False, implicitly_wait=10) -> webdriver:
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

    def explicitly_wait(self, timeout, condition):
        return WebDriverWait(self.driver, timeout).until(condition)

    def save_cookies(self):
        cookies = self.driver.get_cookies()
        with open(self.cookie_file, "w") as f:
            json.dump(cookies, f, indent=4)

    def load_cookies(self, domain):
        self.driver.get(domain)

        if not os.path.exists(self.cookie_file):
            return -1

        with open(self.cookie_file, "r") as f:
                cookies = json.load(f)
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        return 0
