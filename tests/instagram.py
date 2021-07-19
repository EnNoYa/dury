from dury.crawler.instagram import InstagramCrawler


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()

    username = os.environ.get("INSTAGRAM_USERNAME", None)
    password = os.environ.get("INSTAGRAM_PASSWORD", None)

    crawler = InstagramCrawler(username, password)

    articles_0 = crawler.run_on_user("pixel._.store", limit=2)
    articles_1 = crawler.run_on_user("yangazi025", limit=2)
    articles_2 = crawler.run_on_hashtag("커피", limit=2)
    print("Done")
