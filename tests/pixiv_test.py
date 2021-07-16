from dury.crawler.pixiv import PixivCrawler


if __name__ == "__main__":
    import argparse
    import os
    from dotenv import load_dotenv
    
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=int, required=True)
    parser.add_argument("--target", type=str, required=True)
    parser.add_argument("--output-dir", type=str, default="pixiv_output")
    args = parser.parse_args()

    username = os.environ.get("PIXIV_USERNAME")
    password = os.environ.get("PIXIV_PASSWORD")
    crawler = PixivCrawler(username, password, driver_path="./chromedriver")
    crawler.run(args.target, args.mode)
    print("Done")
