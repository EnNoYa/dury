from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from loguru import logger
from tqdm import tqdm
import os

from yacs.config import CfgNode

from dury.utils import download_image
from dury.crawler.base import SeleniumCrawler


class PixivCrawler(SeleniumCrawler):
    LOGIN_URL = "https://accounts.pixiv.net/login"
    PIXIV_URL = "https://www.pixiv.net/"
    REQUEST_HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "Referer": "https://www.pixiv.net/"
    }

    def __init__(self, cfg: CfgNode) -> None:
        super(PixivCrawler, self).__init__(cfg)

        status = self.load_cookies(self.PIXIV_URL)
        if status < 0:
            self.login(cfg.PIXIV.USERNAME, cfg.PIXIV.PASSWORD)

    def login(self, username, password):
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
        except Exception as e:
            if not os.path.exists("tmp"):
                os.makedirs("tmp", exist_ok=True)
            self.driver.save_screenshot("./temp/login_err.png")
            self.driver.quit()
            raise IOError("login sim wait failed, 'root' did not appear")
        
        self.save_cookies()

    def run(self, author, root_dir="output", limit=100):
        out_dir = os.path.join(root_dir, author)
        os.makedirs(out_dir, exist_ok=True)

        self.driver.get(self.PIXIV_URL)
        self.delay()

        # Enter author name to searchbar
        search_element = self.driver.find_element_by_xpath("//input[@type='text']")
        search_element.send_keys(author)
        search_element.submit()
        self.delay()

        # Find user and go to users page
        user_href = self.driver.find_element(By.PARTIAL_LINK_TEXT, "유저")
        user_href.click()
        self.delay()

        target = self.driver.find_elements(By.CLASS_NAME, "user-recommendation-item")[0]
        target = target.find_element(By.CLASS_NAME, "title")
        target.click()
        self.delay()

        # Switch to illustrations page
        last_tab = self.driver.window_handles[-1]
        self.driver.switch_to.window(window_name=last_tab)
        self.driver.find_element(By.PARTIAL_LINK_TEXT, "일러스트").click()
        self.delay()
        
        # Visit each artworks page recursively
        image_cards = self.driver.find_elements(By.XPATH, "//div[@type='illust']")
        latest_illust_url = image_cards[0].find_element(By.TAG_NAME, "a").get_attribute("href")
        self.download_artworks(latest_illust_url, out_dir, recursive=True, limit=limit)

        self.driver.close()
        first_tab = self.driver.window_handles[0]
        self.driver.switch_to.window(window_name=first_tab)

        return self.driver

    def download_artworks(self, url, out_dir, recursive=False, retry=2, limit=100):
        try:
            self.driver.get(url)
            self.delay()
            
            figure = self.driver.find_element(By.TAG_NAME, "figure")
            image_elements = figure.find_elements(By.TAG_NAME, "img")
            
            for image_element in image_elements:
                image_url = image_element.get_attribute("src")
                image_name = image_url.split("/")[-1]
                out_path = os.path.join(out_dir, image_name)

                status = download_image(image_url, out_path, self.REQUEST_HEADERS)
                if status < 0:
                    logger.error(f"Failed to download {image_url}")
        except:
            self.download_artworks(url, out_dir, recursive, retry - 1)

        if recursive and limit > 0:
            nav = self.driver.find_elements(By.TAG_NAME, "nav")[-1]
            nav_elements = nav.find_elements(By.TAG_NAME, "a")
            last_nav_url = nav_elements[-1].get_attribute("href")
            
            if self.driver.current_url != last_nav_url:
                self.download_artworks(last_nav_url, out_dir, recursive, limit - 1)


if __name__ == "__main__":
    import argparse
    import json
    from dury.config import get_default_config

    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file", required=True)
    parser.add_argument("--author-file", required=True)
    parser.add_argument("--limit", default=100, type=int)
    args = parser.parse_args()

    cfg = get_default_config()
    cfg.merge_from_file(args.config_file)
    cfg.freeze()

    with open(args.author_file, "r") as f:
        authors = json.load(f)["authors"]

    crawler = PixivCrawler(cfg)
    for author in tqdm(authors):
        crawler.run(author, cfg.OUTPUT_DIR, limit=args.limit)

    logger.info("Done")
