from dury.crawler.pixiv import PixivCrawler


if __name__ == "__main__":
    import argparse
    import os
    from dotenv import load_dotenv
    
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=str, default="pixiv_output")
    args = parser.parse_args()

    username = os.environ.get("PIXIV_USERNAME", None)
    password = os.environ.get("PIXIV_PASSWORD", None)
    crawler = PixivCrawler(username, password, driver_path="./chromedriver")

    artworks_0 = crawler.run_on_id("11", limit=2)
    artworks_1 = crawler.run_on_user("pixiv事務局", limit=2)
    artworks_2 = crawler.run_on_keyword("風景", safe_mode=True, limit=2)

    print("Done")
