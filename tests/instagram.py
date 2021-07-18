from dury.crawler.instagram import InstagramCrawler


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()

    username = os.environ.get("INSTAGRAM_USERNAME", None)
    password = os.environ.get("INSTAGRAM_PASSWORD", None)

    crawler = InstagramCrawler(username, password)

    crawler.run_on_user("rachel_mypark")
    crawler.run_on_hashtag("커피")
    print("Done")
