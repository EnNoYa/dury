from selenium import webdriver

import time


class SeleniumCrawler:
    def __init__(self, cfg) -> None:
        self.safe_delay = cfg.SELENIUM.SAFE_DELAY
        self.driver = self.launch(cfg.SELENIUM.CHROMEDRIVER_PATH)
    
    def launch(self, driver_path) -> webdriver:
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")
        driver = webdriver.Chrome(executable_path=driver_path, chrome_options=options)
        return driver

    def delay(self) -> None:
        time.sleep(self.safe_delay)
