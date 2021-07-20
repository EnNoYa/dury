import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List

from selenium.webdriver import Chrome
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from loguru import logger
from tqdm import tqdm

from .base import SeleniumCrawler
from dury.utils import download


class GoogleImageCralwer(SeleniumCrawler):
    GOOGLE_URL = "https://www.google.com"

    def __init__(self, *args, **kwargs) -> None:
        super(GoogleImageCralwer, self).__init__(*args, **kwargs)

    def run_on_keyword(self, keyword: str, *, limit: Optional[int] = 100):
        driver = self._launch()
        try:
            image_urls = self.get_image_urls(driver, keyword, limit=limit)
            return image_urls
        finally:
            driver.quit()

    def get_image_urls(
        self,
        driver: Chrome,
        keyword: str, *,
        limit: Optional[int] = 100,
        max_retry: Optional[int] = 5
    ):
        image_search_url = f"{self.GOOGLE_URL}/search?q={keyword}&tbm=isch"
        driver.get(image_search_url)

        prev_num_elements = 0
        retry_cnt = max_retry

        image_containers = []
        while (retry_cnt > 0 and prev_num_elements < limit):
            image_containers = driver.find_elements(By.CLASS_NAME, "islib")
            if prev_num_elements == len(image_containers):
                retry_cnt -= 1
            else:
                retry_cnt = max_retry
                prev_num_elements = len(image_containers)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._delay(0.5)

        image_urls = []
        for image_container in image_containers[:limit]:
            image_container.click()
            self._delay(0.5)
            try:
                image_link = driver.find_elements(By.XPATH, ".//a[@role='link']")[2]
                image_element = image_link.find_element(By.TAG_NAME, "img")
                image_url = image_element.get_attribute("src")
                if "http" in image_url[:4]:
                    image_urls.append(image_url)
            except Exception as e:
                logger.error(e)
        return image_urls

    def download_images(
        self,
        image_urls: List[str], *,
        output_dir: Optional[str] = "output/google",
        num_workers: Optional[int] = 10
    ):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        task_inputs = []
        for i, image_url in enumerate(image_urls):
            task_inputs.append((i, image_url))
        task = lambda x: download(x[1], os.path.join(output_dir, f"{str(x[0]).zfill(6)}.{image_url.split('.')[-1]}"))

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            results = list(tqdm(executor.map(task, task_inputs), total=len(image_urls)))
        return results
