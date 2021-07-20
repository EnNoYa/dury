import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List

from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from loguru import logger
from tqdm import tqdm

from .base import SeleniumCrawler
from dury.utils import download, get_extension


class NaverImageCralwer(SeleniumCrawler):
    NAVER_SEARCH_URL = "https://search.naver.com/"

    def __init__(self, *args, **kwargs) -> None:
        super(NaverImageCralwer, self).__init__(*args, **kwargs)

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
        image_search_url = f"{self.NAVER_SEARCH_URL}/search.naver?where=image&query={keyword}"
        driver.get(image_search_url)

        prev_num_elements = 0
        retry_cnt = max_retry

        image_containers = []
        while (retry_cnt > 0 and prev_num_elements < limit):
            image_containers = driver.find_elements(By.CLASS_NAME, "thumb")
            if prev_num_elements == len(image_containers):
                retry_cnt -= 1
            else:
                retry_cnt = max_retry
                prev_num_elements = len(image_containers)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._delay(0.5)

        image_urls = []
        for image_container in image_containers[:limit]:
            try:
                image_element = image_container.find_element(By.TAG_NAME, "img")
                image_url = image_element.get_attribute("src")
                if "http" in image_url[:4]:
                    image_urls.append(image_url)
            except Exception as e:
                logger.error(e)

        rel_keywords = []
        tag_containers = driver.find_elements(By.CLASS_NAME, "tag_bx")
        for tag_container in tag_containers:
            tag_elements = tag_container.find_elements(By.CLASS_NAME, "txt")
            tags = [ tag_element.text for tag_element in tag_elements ]
            rel_keywords += tags
        return image_urls, rel_keywords

    def download_images(
        self,
        image_urls: List[str], *,
        output_dir: Optional[str] = "output/naver",
        num_workers: Optional[int] = 10
    ):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        task_inputs = []
        for i, image_url in enumerate(image_urls):
            task_inputs.append((i, image_url))
        task = lambda x: download(x[1], os.path.join(output_dir, f"{str(x[0]).zfill(6)}.{get_extension(image_url)}"))

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            results = list(tqdm(executor.map(task, task_inputs), total=len(image_urls)))
        return results
