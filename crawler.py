from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from loguru import logger

from tqdm import tqdm
import requests

import time
import json
import os


LOGIN_URL = "https://accounts.pixiv.net/login"
PIXIV_URL = "https://www.pixiv.net/"
DRIVER_PATH = "./chromedriver"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "Referer": "https://www.pixiv.net/"
}


def launch():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    driver = webdriver.Chrome(executable_path=DRIVER_PATH, chrome_options=options)
    driver.get(PIXIV_URL)

    return driver


def login(username, password, driver):
    driver.get(LOGIN_URL)
    login_element = driver.find_element_by_xpath("//div[@id='container-login']")
    username_input_element = login_element.find_element_by_xpath(".//input[@type='text']")
    username_input_element.send_keys(username)
    password_input_element = login_element.find_element_by_xpath(".//input[@type='password']")
    password_input_element.send_keys(password)
    loign_button = login_element.find_element_by_xpath(".//button")
    loign_button.click()

    try:
        element = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "root")))
    except Exception as e:
        driver.save_screenshot("./temp/log_in_err.png")
        driver.quit()
        raise IOError("login sim wait failed, 'root' did not appear")
    
    cookies_dict = {}
    cookies=driver.get_cookies()
    for cookie in cookies:
        cookies_dict[cookie['name']] = cookie['value']

    return cookies_dict


def process(author, driver, safe_delay=2, root_dir="output"):
    out_dir = os.path.join(root_dir, author)
    os.makedirs(out_dir, exist_ok=True)

    driver.get(PIXIV_URL)
    search_element = driver.find_element_by_xpath("//input[@type='text']")
    search_element.send_keys(author)
    search_element.submit()
    time.sleep(safe_delay)

    user_href = driver.find_element(By.PARTIAL_LINK_TEXT, "유저")
    user_href.click()
    time.sleep(safe_delay)

    target = driver.find_elements(By.CLASS_NAME, "user-recommendation-item")[0]
    target = target.find_element(By.CLASS_NAME, "title")
    target.click()
    time.sleep(safe_delay)

    last_tab = driver.window_handles[-1]
    driver.switch_to.window(window_name=last_tab)
    driver.find_element(By.PARTIAL_LINK_TEXT, "일러스트").click()
    time.sleep(safe_delay)
    
    image_cards = driver.find_elements(By.XPATH, "//div[@type='illust']")
    target_urls = [ image_card.find_element(By.TAG_NAME, "a").get_attribute("href") for image_card in image_cards ]
    for target_url in target_urls:
        driver.get(target_url)
        time.sleep(safe_delay)

        figure = driver.find_element(By.TAG_NAME, "figure")
        image_elements = figure.find_elements(By.TAG_NAME, "img")
        
        for image_element in image_elements:
            image_url = image_element.get_attribute("src")
            image_name = image_url.split("/")[-1]
            out_path = os.path.join(out_dir, image_name)
        #     status = download_image(image_url, out_path, REQUEST_HEADERS)

        # if status < 0:
        #     logger.error(f"Failed to download {image_url}")

    driver.close()
    first_tab = driver.window_handles[0]
    driver.switch_to.window(window_name=first_tab)

    return driver


def download_image(url, out_path, headers={}, timeout=10):
    logger.info(f"Downloading {url}")

    try:
        res = requests.get(url, headers=headers, timeout=timeout)
        if res.status_code != 200:
            raise IOError("Failed request")
        with open(out_path, "wb") as f:
            f.write(res.content)
    except Exception as e:
        logger.error(e)
        return -1
    return 0

if __name__ == "__main__":
    with open("config.json", "r") as f:
        cfg = json.load(f)

    driver = launch()
    cookie_dict = login(cfg["username"], cfg["password"], driver)
    
    for author in tqdm(cfg["authors"]):
        driver = process(author, driver)

    logger.info("Done")
