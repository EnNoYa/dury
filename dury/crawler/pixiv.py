from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from loguru import logger
from tqdm import tqdm
import os

from yacs.config import CfgNode

from dury.utils import download
from dury.crawler.base import SeleniumCrawler


class PixivCrawler(SeleniumCrawler):
    LOGIN_URL = "https://accounts.pixiv.net/login"
    PIXIV_URL = "https://www.pixiv.net/"
    REQUEST_HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "Referer": "https://www.pixiv.net/"
    }
    VALID_MODE_LIST = ["keyword", "author"]

    def __init__(self, cfg: CfgNode) -> None:
        super(PixivCrawler, self).__init__(cfg)

        self.retry = cfg.PIXIV.RETRY
        self.limit = cfg.PIXIV.LIMIT

        status = self.load_cookies(self.PIXIV_URL)
        if status < 0:
            self.login(cfg.PIXIV.USERNAME, cfg.PIXIV.PASSWORD)

    def login(self, username: str, password: str):
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

    def setup(self, target: str, mode: str, root_dir: str):
        output_dir = os.path.join(root_dir, mode, target)
        os.makedirs(output_dir, exist_ok=True)

        self.driver.get(self.PIXIV_URL)
        self.delay()

        self.search(target)
        self.delay()

        return output_dir

    def run(self, target: str, mode: str, root_dir: str = "output"):
        try:
            assert mode in self.VALID_MODE_LIST, "Invalid mode"

            logger.info(f"Crawling target - {target}")
            output_dir = self.setup(target, mode, root_dir)

            if mode == "keyword":
                self.run_on_keyword(output_dir)
            elif mode == "author":
                self.run_on_author(output_dir)
            else:
                raise NotImplementedError
        except Exception as e:
            logger.error(e)
        finally:
            self.driver.close()
 
    def run_on_keyword(self, output_dir: str = "output"):
        # Visit all cards in each page recursively
        artwork_urls = []

        while len(artwork_urls) < self.limit:
            next_page = self.get_next_page()
            image_cards = self.find_cards()
            artwork_urls += [
                image_card.find_element(By.TAG_NAME, "a").get_attribute("href")
                for image_card in image_cards
            ]
            self.driver.get(next_page)
            self.delay()

        logger.info("Start to download artworks")
        for artwork_url in artwork_urls[:self.limit]:
            self.download_artworks(
                artwork_url, output_dir,
                recursive=False,
                retry=self.retry
            )

    def run_on_author(self, output_dir: str = "output"):
        # Switch to user tab in search result
        self.select_user()
        self.delay()

        # Go to top user page
        target = self.driver.find_elements(By.CLASS_NAME, "user-recommendation-item")[0]
        target = target.find_element(By.CLASS_NAME, "title")
        target.click()
        self.delay()

        # New tab is created after link to user page is clicked
        last_tab = self.driver.window_handles[-1]

        # Switch to illustrations page
        logger.info("Switch to illustrations page")
        self.driver.switch_to.window(window_name=last_tab)
        illust_link = self.driver.find_element(By.PARTIAL_LINK_TEXT, "일러스트")
        illust_link.click()
        self.delay()

        # Visit each artworks page recursively
        image_cards = self.find_cards()
        latest_illust_url = image_cards[0].find_element(By.TAG_NAME, "a").get_attribute("href")

        logger.info("Start to download artworks")
        self.download_artworks(latest_illust_url, output_dir, recursive=True, limit=self.limit, retry=self.retry)

        self.driver.close()
        first_tab = self.driver.window_handles[0]
        self.driver.switch_to.window(window_name=first_tab)

        return self.driver

    def search(self, keyword):
        logger.info("Enter search bar")
        search_element = self.driver.find_element_by_xpath("//input[@type='text']")
        search_element.send_keys(keyword)
        search_element.submit()
    
    def find_cards(self):
        section = self.driver.find_elements(By.TAG_NAME,"section")[0]
        image_cards = section.find_elements(By.TAG_NAME, "li")
        return image_cards

    def get_next_page(self):
        nav_bar = self.driver.find_elements(By.TAG_NAME, "nav")
        nav_links = nav_bar[-1].find_elements(By.TAG_NAME, "a")
        next_page = nav_links[-1].get_attribute("href")
        return next_page

    def select_user(self):
        logger.info("Select user on search result")
        user_href = self.driver.find_element(By.PARTIAL_LINK_TEXT, "유저")
        user_href.click()

    def download_artworks(self, url, output_dir, recursive=False, limit=100, retry=2):
        try:
            logger.info(f"Move to {url}")
            self.driver.get(url)
            
            figure = self.explicitly_wait(5, EC.presence_of_element_located((By.TAG_NAME, "figure")))
            self.delay()
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


if __name__ == "__main__":
    import argparse
    import json
    from dury.config import get_default_config

    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file", required=True)
    parser.add_argument("--mode", choices=["author", "keyword"], required=True)
    parser.add_argument("--target", type=str, required=True)
    args = parser.parse_args()

    cfg = get_default_config()
    cfg.merge_from_file(args.config_file)
    cfg.freeze()

    crawler = PixivCrawler(cfg)

    crawler.run(args.target, args.mode, cfg.OUTPUT_DIR)

    logger.info("Done")
